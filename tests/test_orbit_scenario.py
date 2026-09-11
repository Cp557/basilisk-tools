import csv
import json
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

from basilisk_tools.inspection import inspect_simulation
from examples.orbit_propagation.scenario import (
    TELEMETRY_COLUMNS,
    GravityModel,
    OrbitConfiguration,
    basilisk_tools_scenario,
    generate_vizard_playback,
    run,
    save_comparison_plots,
    write_comparison,
    write_outputs,
)


@pytest.fixture(scope="module")
def short_orbit_run():
    config = OrbitConfiguration(
        duration_s=120.0,
        time_step_s=10.0,
        sample_interval_s=20.0,
    )
    return config, run(config)


@pytest.fixture(scope="module")
def reference_comparison():
    point_mass_config = OrbitConfiguration()
    j2_config = replace(point_mass_config, gravity_model=GravityModel.J2)
    return run(point_mass_config), run(j2_config)


def test_point_mass_scenario_records_verified_telemetry(short_orbit_run) -> None:
    config, result = short_orbit_run

    assert result.passed, [check for check in result.checks if not check.passed]
    assert len(result.times_s) == 7
    assert result.positions_m.shape == (7, 3)
    assert result.velocities_m_s.shape == (7, 3)
    assert result.elements.shape == (7, 6)
    assert result.times_s[-1] == pytest.approx(config.duration_s)
    assert all(check.passed for check in result.checks)


def test_point_mass_scenario_matches_expected_initial_elements(short_orbit_run) -> None:
    config, result = short_orbit_run
    first_elements = result.elements[0]

    assert first_elements[0] == pytest.approx(config.semi_major_axis_m, abs=1.0)
    assert first_elements[1] == pytest.approx(config.eccentricity, abs=1e-8)
    assert first_elements[2] == pytest.approx(config.inclination_rad, abs=1e-8)
    assert np.isfinite(result.positions_m).all()
    assert np.all(np.diff(result.times_s) > 0)


def test_outputs_are_machine_readable(short_orbit_run, tmp_path) -> None:
    config, result = short_orbit_run

    telemetry_path, verification_path = write_outputs(result, config, tmp_path)

    with telemetry_path.open(newline="", encoding="utf-8") as telemetry_file:
        rows = list(csv.reader(telemetry_file))
    verification = json.loads(verification_path.read_text(encoding="utf-8"))

    assert tuple(rows[0]) == TELEMETRY_COLUMNS
    assert len(rows) == len(result.times_s) + 1
    assert verification["schema_version"] == 1
    assert verification["passed"] is True
    assert verification["samples"] == len(result.times_s)
    assert "metrics" in verification


def test_point_mass_conservation_metrics_pass(reference_comparison) -> None:
    point_mass, _ = reference_comparison

    assert point_mass.passed, [check for check in point_mass.checks if not check.passed]
    assert point_mass.metrics.max_relative_keplerian_specific_energy_drift < 1e-8
    assert point_mass.metrics.max_relative_specific_angular_momentum_drift < 5e-9
    assert abs(point_mass.metrics.raan_rate_rad_s) < 1e-12


def test_j2_raan_regresses_at_expected_rate(reference_comparison) -> None:
    _, j2 = reference_comparison

    assert j2.passed, [check for check in j2.checks if not check.passed]
    assert j2.metrics.raan_change_rad < 0.0
    assert j2.metrics.raan_rate_rad_s < 0.0
    assert j2.metrics.expected_raan_rate_rad_s < 0.0
    assert j2.metrics.raan_rate_relative_error is not None
    assert j2.metrics.raan_rate_relative_error < 0.02


def test_comparison_artifacts_are_written(reference_comparison, tmp_path) -> None:
    point_mass, j2 = reference_comparison
    plot_paths = save_comparison_plots(
        point_mass_times_s=point_mass.times_s,
        point_mass_positions_m=point_mass.positions_m,
        point_mass_elements=point_mass.elements,
        j2_times_s=j2.times_s,
        j2_positions_m=j2.positions_m,
        j2_elements=j2.elements,
        output_dir=tmp_path,
    )
    comparison_path = write_comparison(point_mass, j2, plot_paths, tmp_path)
    comparison = json.loads(comparison_path.read_text(encoding="utf-8"))

    assert all(path.stat().st_size > 10_000 for path in plot_paths)
    assert comparison["schema_version"] == 1
    assert comparison["passed"] is True
    assert comparison["j2_metrics"]["raan_rate_rad_s"] < 0.0


def test_reference_contract_exposes_pre_execution_structure() -> None:
    contract = basilisk_tools_scenario()
    cases = contract.build_cases()

    assert contract.name == "point_mass_vs_j2_leo"
    assert [case.name for case in cases] == ["point-mass", "j2"]
    runtime = inspect_simulation(cases[0].simulation)
    assert runtime["execution_order"] == ["leoSpacecraft", "Rec:SCStatesMsg"]
    assert cases[0].telemetry[0].frame == "Earth-centered inertial N"


def test_reference_contract_runs_declared_verification(tmp_path) -> None:
    report = basilisk_tools_scenario().verify(tmp_path)

    assert report.passed, [check for check in report.checks if not check.passed]
    assert len(report.checks) == 26
    assert all(check.passed for check in report.checks)
    assert set(report.metrics) == {"point-mass", "j2"}
    assert all(Path(path).exists() for path in report.artifacts.values())


def test_vizard_playback_files_are_generated_and_registered(tmp_path) -> None:
    report = generate_vizard_playback(tmp_path)

    assert report.passed, [check for check in report.checks if not check.passed]
    for artifact_name in ("point_mass_vizard", "j2_vizard"):
        playback_path = Path(report.artifacts[artifact_name])
        assert playback_path.suffix == ".bin"
        assert playback_path.stat().st_size > 1_000


@pytest.mark.parametrize(
    "config, message",
    [
        (OrbitConfiguration(semi_major_axis_m=0), "semi_major_axis_m"),
        (OrbitConfiguration(eccentricity=1), "eccentricity"),
        (OrbitConfiguration(duration_s=0), "duration_s"),
        (OrbitConfiguration(time_step_s=0), "time_step_s"),
        (
            OrbitConfiguration(time_step_s=10, sample_interval_s=5),
            "sample_interval_s",
        ),
        (
            OrbitConfiguration(duration_s=20, sample_interval_s=30),
            "sample_interval_s",
        ),
    ],
)
def test_invalid_configuration_is_rejected(config, message) -> None:
    with pytest.raises(ValueError, match=message):
        run(config)
