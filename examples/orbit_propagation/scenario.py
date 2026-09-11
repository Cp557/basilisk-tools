"""Compare point-mass and J2 low Earth orbits with AVS Basilisk.

Frames and units
----------------
Position and velocity are expressed in Basilisk's inertial N frame, centered on
Earth, in meters and meters per second. Angles are radians internally. Time is
seconds from simulation start.
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict, dataclass
from enum import StrEnum
from pathlib import Path

import numpy as np
from Basilisk.simulation import spacecraft
from Basilisk.utilities import (
    SimulationBaseClass,
    macros,
    orbitalMotion,
    simIncludeGravBody,
    vizSupport,
)
from Basilisk.utilities.supportDataTools.dataFetcher import DataFile, get_path

from basilisk_tools.artifacts import register_artifacts, registered_output_directory
from basilisk_tools.instrumentation import (
    InstrumentedScenario,
    ScenarioCase,
    TelemetrySpec,
    VerificationCheck,
    VerificationReport,
)

if __package__:
    from .analysis import OrbitMetrics, calculate_metrics, save_comparison_plots
else:
    from analysis import OrbitMetrics, calculate_metrics, save_comparison_plots

SCHEMA_VERSION = 1
DEFAULT_OUTPUT_DIR = Path(".bsk/examples/orbit_propagation")
POINT_MASS_ENERGY_DRIFT_TOLERANCE = 1e-8
POINT_MASS_ANGULAR_MOMENTUM_DRIFT_TOLERANCE = 5e-9
POINT_MASS_RAAN_RATE_TOLERANCE_RAD_S = 1e-12
J2_RAAN_RATE_RELATIVE_TOLERANCE = 0.02
J2_ANGULAR_MOMENTUM_Z_DRIFT_TOLERANCE = 5e-9
INITIAL_TRUE_ANOMALY_TOLERANCE_RAD = 5e-8
TELEMETRY_COLUMNS = (
    "time_s",
    "r_x_m",
    "r_y_m",
    "r_z_m",
    "v_x_m_s",
    "v_y_m_s",
    "v_z_m_s",
    "semi_major_axis_m",
    "eccentricity",
    "inclination_rad",
    "raan_rad",
    "argument_of_periapsis_rad",
    "true_anomaly_rad",
)


class GravityModel(StrEnum):
    """Gravity configurations supported by the reference scenario."""

    POINT_MASS = "point-mass"
    J2 = "j2"


@dataclass(frozen=True)
class OrbitConfiguration:
    """Inputs for one reference propagation, in SI units."""

    gravity_model: GravityModel = GravityModel.POINT_MASS
    semi_major_axis_m: float = 7_000_000.0
    eccentricity: float = 0.01
    inclination_rad: float = 55.0 * np.pi / 180.0
    raan_rad: float = 40.0 * np.pi / 180.0
    argument_of_periapsis_rad: float = 30.0 * np.pi / 180.0
    true_anomaly_rad: float = 0.0
    duration_s: float = 18_000.0
    time_step_s: float = 10.0
    sample_interval_s: float = 60.0


DEFAULT_CONFIG = OrbitConfiguration()


CheckResult = VerificationCheck


@dataclass(frozen=True)
class PreparedOrbit:
    """Configured Basilisk objects ready for initialization and execution."""

    config: OrbitConfiguration
    simulation: SimulationBaseClass.SimBaseClass
    recorder: object
    gravitational_parameter_m3_s2: float
    initial_position_m: np.ndarray
    initial_velocity_m_s: np.ndarray


@dataclass(frozen=True)
class OrbitRun:
    """In-memory telemetry and verification outcome for one propagation."""

    times_s: np.ndarray
    positions_m: np.ndarray
    velocities_m_s: np.ndarray
    elements: np.ndarray
    gravitational_parameter_m3_s2: float
    metrics: OrbitMetrics
    checks: tuple[CheckResult, ...]

    @property
    def passed(self) -> bool:
        """Return whether every deterministic check passed."""
        return all(check.passed for check in self.checks)


def _validate_configuration(config: OrbitConfiguration) -> None:
    if config.semi_major_axis_m <= 0:
        raise ValueError("semi_major_axis_m must be positive")
    if not 0 <= config.eccentricity < 1:
        raise ValueError("eccentricity must be in [0, 1)")
    if config.duration_s <= 0:
        raise ValueError("duration_s must be positive")
    if config.time_step_s <= 0:
        raise ValueError("time_step_s must be positive")
    if config.sample_interval_s < config.time_step_s:
        raise ValueError("sample_interval_s must be at least time_step_s")
    if config.sample_interval_s > config.duration_s:
        raise ValueError("sample_interval_s must not exceed duration_s")


def _initial_elements(config: OrbitConfiguration) -> orbitalMotion.ClassicElements:
    elements = orbitalMotion.ClassicElements()
    elements.a = config.semi_major_axis_m
    elements.e = config.eccentricity
    elements.i = config.inclination_rad
    elements.Omega = config.raan_rad
    elements.omega = config.argument_of_periapsis_rad
    elements.f = config.true_anomaly_rad
    return elements


def _calculate_elements(
    mu: float,
    positions_m: np.ndarray,
    velocities_m_s: np.ndarray,
) -> np.ndarray:
    rows = []
    for position_m, velocity_m_s in zip(positions_m, velocities_m_s, strict=True):
        elements = orbitalMotion.rv2elem(mu, position_m, velocity_m_s)
        rows.append(
            (
                elements.a,
                elements.e,
                elements.i,
                elements.Omega,
                elements.omega,
                elements.f,
            )
        )
    return np.asarray(rows, dtype=float)


def _angle_error(actual: float, expected: float) -> float:
    """Return the smallest absolute difference between two wrapped angles."""
    return abs(float(np.arctan2(np.sin(actual - expected), np.cos(actual - expected))))


def _checks(
    config: OrbitConfiguration,
    initial_position_m: np.ndarray,
    initial_velocity_m_s: np.ndarray,
    times_s: np.ndarray,
    positions_m: np.ndarray,
    velocities_m_s: np.ndarray,
    elements: np.ndarray,
    metrics: OrbitMetrics,
) -> tuple[CheckResult, ...]:
    finite = bool(
        np.isfinite(times_s).all()
        and np.isfinite(positions_m).all()
        and np.isfinite(velocities_m_s).all()
        and np.isfinite(elements).all()
    )
    time_ordered = bool(len(times_s) > 1 and np.all(np.diff(times_s) > 0))
    position_error = float(np.linalg.norm(positions_m[0] - initial_position_m))
    velocity_error = float(np.linalg.norm(velocities_m_s[0] - initial_velocity_m_s))

    element_expectations = (
        ("initial_semi_major_axis", elements[0, 0], config.semi_major_axis_m, 1.0, "m"),
        ("initial_eccentricity", elements[0, 1], config.eccentricity, 1e-8, None),
        ("initial_inclination", elements[0, 2], config.inclination_rad, 1e-8, "rad"),
        ("initial_raan", elements[0, 3], config.raan_rad, 1e-8, "rad"),
        (
            "initial_argument_of_periapsis",
            elements[0, 4],
            config.argument_of_periapsis_rad,
            1e-8,
            "rad",
        ),
        (
            "initial_true_anomaly",
            elements[0, 5],
            config.true_anomaly_rad,
            INITIAL_TRUE_ANOMALY_TOLERANCE_RAD,
            "rad",
        ),
    )

    results = [
        CheckResult("finite_telemetry", finite, finite, True, None, None),
        CheckResult(
            "strictly_increasing_time", time_ordered, time_ordered, True, None, "s"
        ),
        CheckResult(
            "initial_position", position_error <= 1e-3, position_error, 0.0, 1e-3, "m"
        ),
        CheckResult(
            "initial_velocity", velocity_error <= 1e-6, velocity_error, 0.0, 1e-6, "m/s"
        ),
    ]
    angular_names = {
        "initial_inclination",
        "initial_raan",
        "initial_argument_of_periapsis",
        "initial_true_anomaly",
    }
    for name, actual, expected, tolerance, units in element_expectations:
        error = (
            _angle_error(float(actual), expected)
            if name in angular_names
            else abs(float(actual) - expected)
        )
        results.append(
            CheckResult(
                name=name,
                passed=error <= tolerance,
                actual=float(actual),
                expected=expected,
                tolerance=tolerance,
                units=units,
            )
        )

    if config.gravity_model is GravityModel.POINT_MASS:
        results.extend(
            (
                CheckResult(
                    name="bounded_keplerian_energy_drift",
                    passed=(
                        metrics.max_relative_keplerian_specific_energy_drift
                        <= POINT_MASS_ENERGY_DRIFT_TOLERANCE
                    ),
                    actual=metrics.max_relative_keplerian_specific_energy_drift,
                    expected=0.0,
                    tolerance=POINT_MASS_ENERGY_DRIFT_TOLERANCE,
                    units=None,
                ),
                CheckResult(
                    name="bounded_angular_momentum_drift",
                    passed=(
                        metrics.max_relative_specific_angular_momentum_drift
                        <= POINT_MASS_ANGULAR_MOMENTUM_DRIFT_TOLERANCE
                    ),
                    actual=metrics.max_relative_specific_angular_momentum_drift,
                    expected=0.0,
                    tolerance=POINT_MASS_ANGULAR_MOMENTUM_DRIFT_TOLERANCE,
                    units=None,
                ),
                CheckResult(
                    name="constant_raan",
                    passed=(
                        abs(metrics.raan_rate_rad_s)
                        <= POINT_MASS_RAAN_RATE_TOLERANCE_RAD_S
                    ),
                    actual=metrics.raan_rate_rad_s,
                    expected=0.0,
                    tolerance=POINT_MASS_RAAN_RATE_TOLERANCE_RAD_S,
                    units="rad/s",
                ),
            )
        )
    else:
        expected_rate = metrics.expected_raan_rate_rad_s
        rate_tolerance = abs(expected_rate) * J2_RAAN_RATE_RELATIVE_TOLERANCE
        results.extend(
            (
                CheckResult(
                    name="j2_raan_regression",
                    passed=metrics.raan_rate_rad_s < 0.0,
                    actual=metrics.raan_rate_rad_s < 0.0,
                    expected=True,
                    tolerance=None,
                    units=None,
                ),
                CheckResult(
                    name="j2_raan_rate",
                    passed=(
                        abs(metrics.raan_rate_rad_s - expected_rate) <= rate_tolerance
                    ),
                    actual=metrics.raan_rate_rad_s,
                    expected=expected_rate,
                    tolerance=rate_tolerance,
                    units="rad/s",
                ),
                CheckResult(
                    name="bounded_angular_momentum_z_drift",
                    passed=(
                        metrics.max_relative_specific_angular_momentum_z_drift
                        <= J2_ANGULAR_MOMENTUM_Z_DRIFT_TOLERANCE
                    ),
                    actual=metrics.max_relative_specific_angular_momentum_z_drift,
                    expected=0.0,
                    tolerance=J2_ANGULAR_MOMENTUM_Z_DRIFT_TOLERANCE,
                    units=None,
                ),
            )
        )
    return tuple(results)


def prepare(
    config: OrbitConfiguration | None = None,
    *,
    vizard_file: Path | None = None,
) -> PreparedOrbit:
    """Configure one propagation without initializing or executing it."""
    if config is None:
        config = DEFAULT_CONFIG
    _validate_configuration(config)

    simulation = SimulationBaseClass.SimBaseClass()
    process = simulation.CreateNewProcess("dynamicsProcess")
    task_name = "dynamicsTask"
    process.addTask(
        simulation.CreateNewTask(task_name, macros.sec2nano(config.time_step_s))
    )

    spacecraft_model = spacecraft.Spacecraft()
    spacecraft_model.ModelTag = "leoSpacecraft"
    simulation.AddModelToTask(task_name, spacecraft_model)

    gravity_factory = simIncludeGravBody.gravBodyFactory()
    earth = gravity_factory.createEarth()
    earth.isCentralBody = True
    if config.gravity_model is GravityModel.J2:
        gravity_path = get_path(DataFile.LocalGravData.GGM03S_J2_only)
        earth.useSphericalHarmonicsGravityModel(str(gravity_path), 2)
    gravity_factory.addBodiesTo(spacecraft_model)

    initial_elements = _initial_elements(config)
    initial_position_m, initial_velocity_m_s = orbitalMotion.elem2rv(
        earth.mu, initial_elements
    )
    spacecraft_model.hub.r_CN_NInit = initial_position_m
    spacecraft_model.hub.v_CN_NInit = initial_velocity_m_s

    recorder = spacecraft_model.scStateOutMsg.recorder(
        macros.sec2nano(config.sample_interval_s)
    )
    simulation.AddModelToTask(task_name, recorder)

    if vizard_file is not None:
        if not vizSupport.vizFound:
            raise RuntimeError(
                "This Basilisk installation does not include Vizard support."
            )
        vizard_file = vizard_file.resolve()
        vizard_file.parent.mkdir(parents=True, exist_ok=True)
        vizSupport.enableUnityVisualization(
            simulation,
            task_name,
            spacecraft_model,
            saveFile=str(vizard_file),
        )

    return PreparedOrbit(
        config=config,
        simulation=simulation,
        recorder=recorder,
        gravitational_parameter_m3_s2=float(earth.mu),
        initial_position_m=np.asarray(initial_position_m),
        initial_velocity_m_s=np.asarray(initial_velocity_m_s),
    )


def run(
    config: OrbitConfiguration | None = None,
    *,
    vizard_file: Path | None = None,
) -> OrbitRun:
    """Build and execute one propagation in AVS Basilisk."""
    prepared = prepare(config, vizard_file=vizard_file)
    config = prepared.config
    simulation = prepared.simulation
    recorder = prepared.recorder

    simulation.InitializeSimulation()
    simulation.ConfigureStopTime(macros.sec2nano(config.duration_s))
    simulation.ExecuteSimulation()

    times_s = np.asarray(recorder.times(), dtype=float) * macros.NANO2SEC
    positions_m = np.asarray(recorder.r_BN_N, dtype=float)
    velocities_m_s = np.asarray(recorder.v_BN_N, dtype=float)
    elements = _calculate_elements(
        prepared.gravitational_parameter_m3_s2,
        positions_m,
        velocities_m_s,
    )
    metrics = calculate_metrics(
        times_s=times_s,
        positions_m=positions_m,
        velocities_m_s=velocities_m_s,
        elements=elements,
        mu_m3_s2=prepared.gravitational_parameter_m3_s2,
        semi_major_axis_m=config.semi_major_axis_m,
        eccentricity=config.eccentricity,
        inclination_rad=config.inclination_rad,
        include_j2=config.gravity_model is GravityModel.J2,
    )
    checks = _checks(
        config,
        prepared.initial_position_m,
        prepared.initial_velocity_m_s,
        times_s,
        positions_m,
        velocities_m_s,
        elements,
        metrics,
    )

    return OrbitRun(
        times_s=times_s,
        positions_m=positions_m,
        velocities_m_s=velocities_m_s,
        elements=elements,
        gravitational_parameter_m3_s2=prepared.gravitational_parameter_m3_s2,
        metrics=metrics,
        checks=checks,
    )


def write_outputs(
    result: OrbitRun,
    config: OrbitConfiguration,
    output_dir: Path,
) -> tuple[Path, Path]:
    """Write CSV telemetry and a compact JSON verification report."""
    output_dir.mkdir(parents=True, exist_ok=True)
    telemetry_path = output_dir / "telemetry.csv"
    verification_path = output_dir / "verification.json"

    with telemetry_path.open("w", newline="", encoding="utf-8") as telemetry_file:
        writer = csv.writer(telemetry_file)
        writer.writerow(TELEMETRY_COLUMNS)
        for index, time_s in enumerate(result.times_s):
            writer.writerow(
                (
                    float(time_s),
                    *result.positions_m[index].tolist(),
                    *result.velocities_m_s[index].tolist(),
                    *result.elements[index].tolist(),
                )
            )

    verification = {
        "schema_version": SCHEMA_VERSION,
        "scenario": f"{config.gravity_model.value}_leo",
        "passed": result.passed,
        "configuration": asdict(config),
        "gravitational_parameter_m3_s2": result.gravitational_parameter_m3_s2,
        "telemetry": str(telemetry_path),
        "samples": len(result.times_s),
        "metrics": asdict(result.metrics),
        "checks": [asdict(check) for check in result.checks],
    }
    verification_path.write_text(
        json.dumps(verification, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return telemetry_path, verification_path


def write_comparison(
    point_mass: OrbitRun,
    j2: OrbitRun,
    plot_paths: tuple[Path, Path],
    output_dir: Path,
) -> Path:
    """Write a machine-readable summary of the model comparison."""
    comparison_path = output_dir / "comparison.json"
    payload = {
        "schema_version": SCHEMA_VERSION,
        "scenario": "point_mass_vs_j2_leo",
        "passed": point_mass.passed and j2.passed,
        "point_mass_metrics": asdict(point_mass.metrics),
        "j2_metrics": asdict(j2.metrics),
        "plots": [str(path) for path in plot_paths],
        "interpretation": {
            "raan": "J2 produces nodal regression for this prograde orbit.",
            "energy": (
                "Keplerian specific energy is conserved only in the point-mass "
                "model; its J2 variation is physical because the metric omits "
                "the J2 potential."
            ),
        },
    }
    comparison_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return comparison_path


def _execute_configurations(
    configurations: tuple[OrbitConfiguration, ...],
    output_dir: Path,
    *,
    include_vizard: bool = False,
) -> tuple[dict[GravityModel, OrbitRun], VerificationReport]:
    """Execute configured cases and write their declared verification artifacts."""
    runs: dict[GravityModel, OrbitRun] = {}
    artifacts: dict[str, str] = {}
    for config in configurations:
        case_output_dir = output_dir / config.gravity_model.value
        vizard_path = case_output_dir / "vizard.bin" if include_vizard else None
        result = run(config, vizard_file=vizard_path)
        runs[config.gravity_model] = result
        telemetry_path, case_verification_path = write_outputs(
            result,
            config,
            case_output_dir,
        )
        prefix = config.gravity_model.value.replace("-", "_")
        artifacts[f"{prefix}_telemetry"] = str(telemetry_path.resolve())
        artifacts[f"{prefix}_verification"] = str(case_verification_path.resolve())
        if vizard_path is not None:
            if not vizard_path.is_file():
                raise RuntimeError(f"Vizard playback was not written: {vizard_path}")
            artifacts[f"{prefix}_vizard"] = str(vizard_path.resolve())

    if len(runs) == 2:
        point_mass = runs[GravityModel.POINT_MASS]
        j2 = runs[GravityModel.J2]
        plot_paths = save_comparison_plots(
            point_mass_times_s=point_mass.times_s,
            point_mass_positions_m=point_mass.positions_m,
            point_mass_elements=point_mass.elements,
            j2_times_s=j2.times_s,
            j2_positions_m=j2.positions_m,
            j2_elements=j2.elements,
            output_dir=output_dir,
        )
        comparison_path = write_comparison(point_mass, j2, plot_paths, output_dir)
        artifacts.update(
            {
                "comparison": str(comparison_path.resolve()),
                "orbit_plot": str(plot_paths[0].resolve()),
                "elements_plot": str(plot_paths[1].resolve()),
            }
        )

    checks = tuple(
        VerificationCheck(
            name=f"{model.value}.{check.name}",
            passed=check.passed,
            actual=check.actual,
            expected=check.expected,
            tolerance=check.tolerance,
            units=check.units,
        )
        for model, result in runs.items()
        for check in result.checks
    )
    report_path = (output_dir / "verification.json").resolve()
    artifacts["verification"] = str(report_path)
    report = VerificationReport(
        scenario="point_mass_vs_j2_leo",
        passed=all(check.passed for check in checks),
        checks=checks,
        metrics={model.value: asdict(result.metrics) for model, result in runs.items()},
        artifacts=artifacts,
    )
    report_path.write_text(report.to_json() + "\n", encoding="utf-8")
    register_artifacts(report.artifacts)
    return runs, report


def generate_vizard_playback(output_dir: Path) -> VerificationReport:
    """Run both reference cases and record offline Vizard playback files."""
    configurations = (
        OrbitConfiguration(gravity_model=GravityModel.POINT_MASS),
        OrbitConfiguration(gravity_model=GravityModel.J2),
    )
    _, report = _execute_configurations(
        configurations,
        output_dir,
        include_vizard=True,
    )
    return report


def verify_reference(output_dir: Path) -> VerificationReport:
    """Execute both reference cases and return their declared checks."""
    configurations = (
        OrbitConfiguration(gravity_model=GravityModel.POINT_MASS),
        OrbitConfiguration(gravity_model=GravityModel.J2),
    )
    _, report = _execute_configurations(configurations, output_dir)
    return report


def _instrumented_cases() -> tuple[ScenarioCase, ...]:
    telemetry = TelemetrySpec(
        name="spacecraft_state",
        source_message="leoSpacecraft.scStateOutMsg",
        fields=(
            "time_s",
            "r_x_m",
            "r_y_m",
            "r_z_m",
            "v_x_m_s",
            "v_y_m_s",
            "v_z_m_s",
        ),
        units={"time": "s", "position": "m", "velocity": "m/s"},
        sample_interval_s=DEFAULT_CONFIG.sample_interval_s,
        frame="Earth-centered inertial N",
    )
    cases = []
    for gravity_model in (GravityModel.POINT_MASS, GravityModel.J2):
        config = OrbitConfiguration(gravity_model=gravity_model)
        prepared = prepare(config)
        cases.append(
            ScenarioCase(
                name=gravity_model.value,
                simulation=prepared.simulation,
                telemetry=(telemetry,),
                metadata={
                    "gravity_model": gravity_model.value,
                    "duration_s": config.duration_s,
                    "time_step_s": config.time_step_s,
                },
            )
        )
    return tuple(cases)


def basilisk_tools_scenario() -> InstrumentedScenario:
    """Expose the optional Basilisk Tools contract for this reference scenario."""
    return InstrumentedScenario(
        name="point_mass_vs_j2_leo",
        description="Compare point-mass and J2 low Earth orbit propagation.",
        build_cases=_instrumented_cases,
        verify=verify_reference,
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=registered_output_directory(DEFAULT_OUTPUT_DIR),
    )
    parser.add_argument(
        "--gravity-model",
        choices=(GravityModel.POINT_MASS.value, GravityModel.J2.value, "both"),
        default="both",
    )
    parser.add_argument("--duration-seconds", type=float, default=18_000.0)
    parser.add_argument("--time-step-seconds", type=float, default=10.0)
    parser.add_argument("--sample-interval-seconds", type=float, default=60.0)
    parser.add_argument(
        "--vizard",
        action="store_true",
        help="Write an offline Vizard playback file for each gravity case.",
    )
    return parser


def main() -> int:
    """Run the example, write its outputs, and report verification status."""
    args = _parser().parse_args()
    models = (
        (GravityModel.POINT_MASS, GravityModel.J2)
        if args.gravity_model == "both"
        else (GravityModel(args.gravity_model),)
    )
    configurations = tuple(
        OrbitConfiguration(
            gravity_model=model,
            duration_s=args.duration_seconds,
            time_step_s=args.time_step_seconds,
            sample_interval_s=args.sample_interval_seconds,
        )
        for model in models
    )
    runs, report = _execute_configurations(
        configurations,
        args.output_dir,
        include_vizard=args.vizard,
    )

    for model, result in runs.items():
        prefix = model.value.replace("-", "_")
        status = "PASS" if result.passed else "FAIL"
        print(f"{model.value} LEO verification: {status}")
        print(f"Telemetry: {report.artifacts[f'{prefix}_telemetry']}")
        print(f"Verification: {report.artifacts[f'{prefix}_verification']}")
        if f"{prefix}_vizard" in report.artifacts:
            print(f"Vizard: {report.artifacts[f'{prefix}_vizard']}")
        for check in result.checks:
            marker = "PASS" if check.passed else "FAIL"
            print(f"  [{marker}] {check.name}")

    if "comparison" in report.artifacts:
        print(f"Comparison: {report.artifacts['comparison']}")
        print(f"Plot: {report.artifacts['orbit_plot']}")
        print(f"Plot: {report.artifacts['elements_plot']}")
    print(f"Overall verification: {report.artifacts['verification']}")

    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
