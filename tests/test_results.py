import json

from basilisk_tools.results import (
    SCHEMA_VERSION,
    ErrorSummary,
    RunMetadata,
    RunResult,
    RunStatus,
)


def test_success_result_serializes_to_versioned_json() -> None:
    result = RunResult(
        run_id="run-001",
        status=RunStatus.SUCCESS,
        elapsed_seconds=1.25,
        exit_code=0,
        artifacts={"stdout": ".bsk/runs/run-001/stdout.log"},
    )

    payload = json.loads(result.to_json())

    assert payload == {
        "artifacts": {"stdout": ".bsk/runs/run-001/stdout.log"},
        "elapsed_seconds": 1.25,
        "error": None,
        "exit_code": 0,
        "run_id": "run-001",
        "schema_version": SCHEMA_VERSION,
        "status": "success",
    }


def test_failure_result_includes_error_summary() -> None:
    result = RunResult(
        run_id="run-002",
        status=RunStatus.FAILURE,
        elapsed_seconds=0.1,
        exit_code=1,
        error=ErrorSummary(type="RuntimeError", message="scenario failed"),
    )

    payload = result.to_dict()

    assert payload["status"] == RunStatus.FAILURE
    assert payload["error"] == {
        "type": "RuntimeError",
        "message": "scenario failed",
    }


def test_metadata_serializes_nullable_basilisk_version() -> None:
    metadata = RunMetadata(
        run_id="run-003",
        scenario_path="scenario.py",
        scenario_sha256="abc123",
        started_at="2026-09-10T12:00:00Z",
        python_version="3.11.9",
        basilisk_version=None,
        basilisk_tools_version="0.1.0",
    )

    payload = json.loads(metadata.to_json())

    assert payload["schema_version"] == SCHEMA_VERSION
    assert payload["basilisk_version"] is None
