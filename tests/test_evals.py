import tomllib
from pathlib import Path

import pytest

from evals.run import CASES, prepare_case
from evals.verification import load_expectations, verify_telemetry
from examples.orbit_propagation.scenario import (
    GravityModel,
    OrbitConfiguration,
    run,
    write_outputs,
)

ROOT = Path(__file__).parents[1]
EVALS_DIRECTORY = ROOT / "evals"


@pytest.mark.parametrize("case", CASES)
def test_evaluation_case_has_complete_fixture(case: str) -> None:
    case_directory = EVALS_DIRECTORY / case

    assert (case_directory / "prompt.md").stat().st_size > 200
    assert (case_directory / "starting_files" / "scenario.py").is_file()
    assert (case_directory / "verify.py").is_file()
    with (case_directory / "expected.toml").open("rb") as expected_file:
        expected = tomllib.load(expected_file)
    assert expected["schema_version"] == 1
    assert expected["case"] == case


def test_prepare_case_copies_frozen_starting_files(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"

    prepare_case("fix_units", workspace)

    assert (workspace / "scenario.py").is_file()
    with pytest.raises(FileExistsError):
        prepare_case("fix_units", workspace)


@pytest.mark.parametrize(
    ("case", "config"),
    [
        (
            "two_body",
            OrbitConfiguration(
                duration_s=1_200.0,
                time_step_s=10.0,
                sample_interval_s=60.0,
            ),
        ),
        ("add_j2", OrbitConfiguration(gravity_model=GravityModel.J2)),
    ],
)
def test_independent_verifier_accepts_reference_physics(
    case: str,
    config: OrbitConfiguration,
    tmp_path: Path,
) -> None:
    result = run(config)
    telemetry_path, _ = write_outputs(result, config, tmp_path)
    expectations = load_expectations(EVALS_DIRECTORY / case)

    checks = verify_telemetry(telemetry_path, expectations)

    assert checks
    assert all(check["passed"] for check in checks), checks
