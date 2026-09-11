import hashlib
import json
from pathlib import Path

import pytest

from basilisk_tools.results import SCHEMA_VERSION, RunStatus
from basilisk_tools.runner import run_scenario

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "scenarios"


def test_successful_run_preserves_logs_and_metadata(tmp_path: Path) -> None:
    scenario = FIXTURE_DIR / "success.py"

    result = run_scenario(scenario, runs_directory=tmp_path, timeout_seconds=2)

    assert result.status == RunStatus.SUCCESS
    assert result.exit_code == 0
    assert result.error is None
    assert result.elapsed_seconds >= 0

    run_directory = Path(result.artifacts["run_directory"])
    assert set(path.name for path in run_directory.iterdir()) == {
        "metadata.json",
        "result.json",
        "stderr.log",
        "stdout.log",
        "artifacts",
    }
    assert Path(result.artifacts["stdout"]).read_text(encoding="utf-8") == (
        "scenario completed\n"
    )
    assert Path(result.artifacts["stderr"]).read_text(encoding="utf-8") == (
        "scenario diagnostic\n"
    )

    metadata = json.loads(Path(result.artifacts["metadata"]).read_text())
    expected_hash = hashlib.sha256(scenario.read_bytes()).hexdigest()
    assert metadata["schema_version"] == SCHEMA_VERSION
    assert metadata["run_id"] == result.run_id
    assert metadata["scenario_path"] == str(scenario.resolve())
    assert metadata["scenario_sha256"] == expected_hash
    assert metadata["python_version"]
    assert metadata["basilisk_version"] == "2.11.1"

    stored_result = json.loads(Path(result.artifacts["result"]).read_text())
    assert stored_result == result.to_dict()


def test_failed_run_records_python_exception(tmp_path: Path) -> None:
    result = run_scenario(
        FIXTURE_DIR / "failure.py",
        runs_directory=tmp_path,
        timeout_seconds=2,
    )

    assert result.status == RunStatus.FAILURE
    assert result.exit_code == 1
    assert result.error is not None
    assert result.error.type == "RuntimeError"
    assert result.error.message == "intentional scenario failure"
    stderr = Path(result.artifacts["stderr"]).read_text(encoding="utf-8")
    assert "Traceback" in stderr
    assert "intentional scenario failure" in stderr


def test_timed_out_run_is_terminated_and_recorded(tmp_path: Path) -> None:
    result = run_scenario(
        FIXTURE_DIR / "timeout.py",
        runs_directory=tmp_path,
        timeout_seconds=0.05,
    )

    assert result.status == RunStatus.TIMEOUT
    assert result.exit_code is not None
    assert result.error is not None
    assert result.error.type == "TimeoutExpired"
    assert "0.05 second timeout" in result.error.message
    stdout = Path(result.artifacts["stdout"]).read_text(encoding="utf-8")
    assert stdout == "scenario started\n"


def test_run_rejects_nonpositive_timeout(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="greater than zero"):
        run_scenario(
            FIXTURE_DIR / "success.py",
            runs_directory=tmp_path,
            timeout_seconds=0,
        )
