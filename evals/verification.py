"""Independent numerical verification shared by the evaluation cases."""

from __future__ import annotations

import argparse
import csv
import json
import math
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any

import numpy as np
from Basilisk.utilities import orbitalMotion

from basilisk_tools.results import SCHEMA_VERSION

REQUIRED_COLUMNS = (
    "time_s",
    "r_x_m",
    "r_y_m",
    "r_z_m",
    "v_x_m_s",
    "v_y_m_s",
    "v_z_m_s",
)


def load_expectations(case_directory: Path) -> dict[str, Any]:
    """Load a case's trusted expectations."""
    with (case_directory / "expected.toml").open("rb") as expected_file:
        expectations = tomllib.load(expected_file)
    if expectations.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("Evaluation expectations must use schema_version 1.")
    return expectations


def _json_value(value: Any) -> Any:
    if isinstance(value, (float, np.floating)):
        return float(value) if math.isfinite(float(value)) else None
    if isinstance(value, (int, np.integer)):
        return int(value)
    return value


def _check(
    name: str,
    passed: bool,
    actual: Any,
    expected: Any,
    tolerance: float | None = None,
    units: str | None = None,
) -> dict[str, Any]:
    return {
        "name": name,
        "passed": bool(passed),
        "actual": _json_value(actual),
        "expected": _json_value(expected),
        "tolerance": tolerance,
        "units": units,
    }


def _max_relative_drift(values: np.ndarray) -> float:
    initial = float(values[0])
    if initial == 0.0:
        return math.inf
    return float(np.max(np.abs(values - initial)) / abs(initial))


def _load_telemetry(path: Path) -> tuple[tuple[str, ...], np.ndarray]:
    with path.open(newline="", encoding="utf-8") as telemetry_file:
        reader = csv.DictReader(telemetry_file)
        columns = tuple(reader.fieldnames or ())
        rows = list(reader)

    if not rows or not set(REQUIRED_COLUMNS).issubset(columns):
        return columns, np.empty((0, len(REQUIRED_COLUMNS)))
    values = np.asarray(
        [[float(row[column]) for column in REQUIRED_COLUMNS] for row in rows],
        dtype=float,
    )
    return columns, values


def _timeout_output(value: str | bytes | None) -> str:
    if value is None:
        return ""
    return value.decode(errors="replace") if isinstance(value, bytes) else value


def verify_telemetry(
    telemetry_path: Path,
    expectations: dict[str, Any],
) -> list[dict[str, Any]]:
    """Check recorded states independently of candidate-authored metrics."""
    columns, values = _load_telemetry(telemetry_path)
    checks = [
        _check(
            "required_telemetry_columns",
            set(REQUIRED_COLUMNS).issubset(columns),
            list(columns),
            list(REQUIRED_COLUMNS),
        ),
        _check(
            "minimum_samples",
            len(values) >= expectations["minimum_samples"],
            len(values),
            expectations["minimum_samples"],
            units="samples",
        ),
    ]
    if len(values) == 0:
        return checks

    times_s = values[:, 0]
    positions_m = values[:, 1:4]
    velocities_m_s = values[:, 4:7]
    finite = bool(np.isfinite(values).all())
    ordered = bool(len(times_s) > 1 and np.all(np.diff(times_s) > 0.0))
    duration_s = float(times_s[-1] - times_s[0])
    checks.extend(
        (
            _check("finite_telemetry", finite, finite, True),
            _check("strictly_increasing_time", ordered, ordered, True),
            _check(
                "minimum_duration",
                duration_s >= expectations["minimum_duration_s"],
                duration_s,
                expectations["minimum_duration_s"],
                units="s",
            ),
        )
    )
    if not finite or not ordered:
        return checks

    mu = float(expectations["mu_m3_s2"])
    elements = np.asarray(
        [
            (
                element.a,
                element.e,
                element.i,
                element.Omega,
            )
            for position, velocity in zip(positions_m, velocities_m_s, strict=True)
            for element in (orbitalMotion.rv2elem(mu, position, velocity),)
        ],
        dtype=float,
    )
    initial_a_m, initial_e, initial_i_rad, _ = elements[0]
    a_error_m = abs(initial_a_m - expectations["semi_major_axis_m"])
    perigee_altitude_m = (
        initial_a_m * (1.0 - initial_e) - expectations["earth_radius_m"]
    )
    checks.extend(
        (
            _check(
                "initial_semi_major_axis",
                a_error_m <= expectations["semi_major_axis_tolerance_m"],
                initial_a_m,
                expectations["semi_major_axis_m"],
                expectations["semi_major_axis_tolerance_m"],
                "m",
            ),
            _check(
                "perigee_above_earth",
                perigee_altitude_m > 0.0,
                perigee_altitude_m,
                "> 0",
                units="m",
            ),
        )
    )

    radii_m = np.linalg.norm(positions_m, axis=1)
    speeds_squared_m2_s2 = np.sum(velocities_m_s**2, axis=1)
    energy_j_kg = speeds_squared_m2_s2 / 2.0 - mu / radii_m
    angular_momentum_m2_s = np.cross(positions_m, velocities_m_s)

    if expectations["gravity_model"] == "point-mass":
        energy_drift = _max_relative_drift(energy_j_kg)
        momentum_drift = _max_relative_drift(
            np.linalg.norm(angular_momentum_m2_s, axis=1)
        )
        checks.extend(
            (
                _check(
                    "bounded_keplerian_energy_drift",
                    energy_drift <= expectations["max_energy_drift"],
                    energy_drift,
                    0.0,
                    expectations["max_energy_drift"],
                ),
                _check(
                    "bounded_angular_momentum_drift",
                    momentum_drift <= expectations["max_angular_momentum_drift"],
                    momentum_drift,
                    0.0,
                    expectations["max_angular_momentum_drift"],
                ),
            )
        )
    elif expectations["gravity_model"] == "j2":
        raan_rate_rad_s = float(np.polyfit(times_s, np.unwrap(elements[:, 3]), 1)[0])
        mean_motion_rad_s = math.sqrt(mu / initial_a_m**3)
        semi_latus_rectum_m = initial_a_m * (1.0 - initial_e**2)
        expected_rate_rad_s = (
            -1.5
            * mean_motion_rad_s
            * expectations["earth_j2"]
            * (expectations["earth_radius_m"] / semi_latus_rectum_m) ** 2
            * math.cos(initial_i_rad)
        )
        rate_error = abs((raan_rate_rad_s - expected_rate_rad_s) / expected_rate_rad_s)
        rate_tolerance_rad_s = (
            abs(expected_rate_rad_s) * expectations["max_raan_rate_relative_error"]
        )
        momentum_z_drift = _max_relative_drift(angular_momentum_m2_s[:, 2])
        checks.extend(
            (
                _check(
                    "raan_regresses",
                    raan_rate_rad_s < 0.5 * expected_rate_rad_s,
                    raan_rate_rad_s,
                    f"< {0.5 * expected_rate_rad_s}",
                    units="rad/s",
                ),
                _check(
                    "j2_raan_rate_matches_theory",
                    rate_error <= expectations["max_raan_rate_relative_error"],
                    raan_rate_rad_s,
                    expected_rate_rad_s,
                    rate_tolerance_rad_s,
                    "rad/s",
                ),
                _check(
                    "bounded_angular_momentum_z_drift",
                    momentum_z_drift <= expectations["max_angular_momentum_z_drift"],
                    momentum_z_drift,
                    0.0,
                    expectations["max_angular_momentum_z_drift"],
                ),
            )
        )
    else:
        raise ValueError(f"Unknown gravity model: {expectations['gravity_model']}")
    return checks


def evaluate_submission(
    case_directory: Path,
    submission_directory: Path,
    output_directory: Path,
) -> dict[str, Any]:
    """Execute one trusted submission through bsk and verify its telemetry."""
    expectations = load_expectations(case_directory)
    output_directory.mkdir(parents=True, exist_ok=True)
    scenario_path = submission_directory.resolve() / expectations["scenario_file"]
    report_path = output_directory / "verification.json"
    bsk_stdout_path = output_directory / "bsk-stdout.log"
    bsk_stderr_path = output_directory / "bsk-stderr.log"
    checks: list[dict[str, Any]] = []
    artifacts: dict[str, str] = {
        "bsk_stdout": str(bsk_stdout_path.resolve()),
        "bsk_stderr": str(bsk_stderr_path.resolve()),
        "verification": str(report_path.resolve()),
    }

    if not scenario_path.is_file():
        checks.append(
            _check("scenario_exists", False, str(scenario_path), "existing file")
        )
    else:
        command = [
            sys.executable,
            "-m",
            "basilisk_tools.cli",
            "run",
            str(scenario_path),
            "--runs-dir",
            str(output_directory / "runs"),
            "--timeout",
            str(expectations["timeout_seconds"]),
            "--json",
        ]
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=float(expectations["timeout_seconds"]) + 10.0,
                check=False,
            )
            bsk_stdout_path.write_text(completed.stdout, encoding="utf-8")
            bsk_stderr_path.write_text(completed.stderr, encoding="utf-8")
            try:
                run_result = json.loads(completed.stdout)
            except json.JSONDecodeError:
                run_result = {}
            (output_directory / "bsk-result.json").write_text(
                json.dumps(run_result, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            artifacts["bsk_result"] = str(
                (output_directory / "bsk-result.json").resolve()
            )
            checks.append(
                _check(
                    "scenario_execution",
                    completed.returncode == 0 and run_result.get("status") == "success",
                    run_result.get("status", f"exit {completed.returncode}"),
                    "success",
                )
            )
            telemetry_value = run_result.get("artifacts", {}).get("telemetry")
            telemetry_path = Path(telemetry_value) if telemetry_value else None
            telemetry_exists = bool(telemetry_path and telemetry_path.is_file())
            checks.append(
                _check(
                    "telemetry_registered",
                    telemetry_exists,
                    str(telemetry_path) if telemetry_path else None,
                    "registered telemetry artifact",
                )
            )
            if telemetry_exists and telemetry_path is not None:
                artifacts["telemetry"] = str(telemetry_path.resolve())
                try:
                    checks.extend(verify_telemetry(telemetry_path, expectations))
                except (OSError, ValueError, ArithmeticError) as error:
                    checks.append(
                        _check(
                            "telemetry_analysis",
                            False,
                            f"{type(error).__name__}: {error}",
                            "successful independent analysis",
                        )
                    )
        except subprocess.TimeoutExpired as error:
            bsk_stdout_path.write_text(_timeout_output(error.stdout), encoding="utf-8")
            bsk_stderr_path.write_text(_timeout_output(error.stderr), encoding="utf-8")
            checks.append(
                _check(
                    "scenario_execution",
                    False,
                    "evaluation timeout",
                    "success",
                    units="s",
                )
            )

    if not bsk_stdout_path.exists():
        bsk_stdout_path.write_text("", encoding="utf-8")
    if not bsk_stderr_path.exists():
        bsk_stderr_path.write_text("", encoding="utf-8")
    report = {
        "schema_version": SCHEMA_VERSION,
        "case": expectations["case"],
        "passed": bool(checks) and all(check["passed"] for check in checks),
        "checks": checks,
        "artifacts": artifacts,
        "error": None,
    }
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def case_main(case_directory: Path) -> int:
    """Run the command-line verifier for one fixed evaluation case."""
    parser = argparse.ArgumentParser(
        description="Run an independent Basilisk evaluation verifier."
    )
    parser.add_argument("submission", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    arguments = parser.parse_args()
    report = evaluate_submission(
        case_directory.resolve(),
        arguments.submission.resolve(),
        arguments.output_dir.resolve(),
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["passed"] else 3
