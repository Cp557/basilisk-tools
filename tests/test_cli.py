import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from basilisk_tools import __version__, cli
from basilisk_tools.cli import _run_exit_code, app
from basilisk_tools.results import ErrorSummary, RunResult, RunStatus

runner = CliRunner()
FIXTURE_DIR = Path(__file__).parent / "fixtures" / "scenarios"


def test_cli_starts() -> None:
    result = runner.invoke(app)

    assert result.exit_code == 0
    assert "bsk --help" in result.stdout


def test_cli_help() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "Inspect, run, and verify" in result.stdout


def test_cli_version() -> None:
    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert result.stdout.strip() == __version__


def test_doctor_reports_working_environment_as_json() -> None:
    result = runner.invoke(app, ["doctor", "--json"])

    assert result.exit_code == 0
    report = json.loads(result.stdout)
    assert report["schema_version"] == 1
    assert report["ok"] is True
    assert report["basilisk"]["version"] == "2.11.1"
    assert report["python"]["executable"]
    assert report["required_dependencies"]
    assert report["optional_dependencies"]


def test_doctor_renders_human_report() -> None:
    result = runner.invoke(app, ["doctor"])

    assert result.exit_code == 0


def test_run_json_is_not_corrupted_by_scenario_output(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "run",
            str(FIXTURE_DIR / "success.py"),
            "--runs-dir",
            str(tmp_path),
            "--json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "success"
    assert "scenario completed" not in result.stdout


def test_run_failure_returns_child_error_and_nonzero_exit(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "run",
            str(FIXTURE_DIR / "failure.py"),
            "--runs-dir",
            str(tmp_path),
            "--json",
        ],
    )

    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert payload["status"] == "failure"
    assert payload["error"] == {
        "type": "RuntimeError",
        "message": "intentional scenario failure",
    }


def test_run_renders_human_success(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "run",
            str(FIXTURE_DIR / "success.py"),
            "--runs-dir",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0


def test_run_renders_human_error(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "run",
            str(FIXTURE_DIR / "failure.py"),
            "--runs-dir",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 1


@pytest.mark.parametrize(
    ("status", "child_exit_code", "expected"),
    [
        (RunStatus.SUCCESS, 0, 0),
        (RunStatus.FAILURE, -1, 1),
        (RunStatus.TIMEOUT, -15, 124),
        (RunStatus.INTERRUPTED, -15, 130),
    ],
)
def test_run_exit_codes(status: RunStatus, child_exit_code: int, expected: int) -> None:
    result = RunResult(
        run_id="test-run",
        status=status,
        elapsed_seconds=0,
        exit_code=child_exit_code,
        error=ErrorSummary(type="TestError", message="test"),
    )

    assert _run_exit_code(result) == expected


def test_inspect_json_reports_runtime_structure() -> None:
    result = runner.invoke(
        app, ["inspect", str(FIXTURE_DIR / "instrumented.py"), "--json"]
    )

    assert result.exit_code == 0
    report = json.loads(result.stdout)
    assert report["cases"][0]["runtime"]["execution_order"] == [
        "testSpacecraft",
        "Rec:SCStatesMsg",
    ]
    assert "instrumented scenario loaded" not in result.stdout


def test_inspect_renders_human_structure() -> None:
    result = runner.invoke(app, ["inspect", str(FIXTURE_DIR / "instrumented.py")])

    assert result.exit_code == 0


def test_inspect_reports_unsupported_standard_scenario() -> None:
    result = runner.invoke(app, ["inspect", str(FIXTURE_DIR / "success.py")])

    assert result.exit_code == 2


def test_inspect_renders_structured_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        cli,
        "inspect_scenario",
        lambda *args, **kwargs: {
            "supported": True,
            "error": {"type": "TestError", "message": "broken"},
        },
    )

    result = runner.invoke(app, ["inspect", str(FIXTURE_DIR / "success.py")])

    assert result.exit_code == 1


def test_inspect_reports_unavailable_runtime(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        cli,
        "inspect_scenario",
        lambda *args, **kwargs: {
            "supported": True,
            "scenario": "test",
            "error": None,
            "cases": [
                {
                    "name": "case",
                    "runtime": {"supported": False, "reason": "unavailable"},
                }
            ],
        },
    )

    result = runner.invoke(app, ["inspect", str(FIXTURE_DIR / "success.py")])

    assert result.exit_code == 0


def test_verify_json_runs_declared_checks(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "verify",
            str(FIXTURE_DIR / "instrumented.py"),
            "--output-dir",
            str(tmp_path),
            "--json",
        ],
    )

    assert result.exit_code == 0
    report = json.loads(result.stdout)
    assert report["passed"] is True
    assert "instrumented scenario loaded" not in result.stdout


def test_verify_renders_human_checks(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "verify",
            str(FIXTURE_DIR / "instrumented.py"),
            "--output-dir",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0


def test_verify_reports_unsupported_standard_scenario(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "verify",
            str(FIXTURE_DIR / "success.py"),
            "--output-dir",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 2


def test_verify_converts_invalid_saved_run_to_unsupported(tmp_path: Path) -> None:
    result_path = tmp_path / "result.json"
    result_path.write_text(
        json.dumps({"schema_version": 1, "artifacts": {}}), encoding="utf-8"
    )

    result = runner.invoke(app, ["verify", str(result_path), "--json"])

    assert result.exit_code == 2
    assert json.loads(result.stdout)["supported"] is False


def test_verify_renders_structured_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        cli,
        "verify_target",
        lambda *args, **kwargs: {
            "supported": True,
            "error": {"type": "TestError", "message": "broken"},
        },
    )

    result = runner.invoke(app, ["verify", str(FIXTURE_DIR / "success.py")])

    assert result.exit_code == 1


def test_verify_failed_check_exits_three(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        cli,
        "verify_target",
        lambda *args, **kwargs: {
            "supported": True,
            "error": None,
            "scenario": "test",
            "passed": False,
            "checks": [
                {
                    "name": "failed",
                    "passed": False,
                    "actual": 2,
                    "expected": 1,
                    "tolerance": 0,
                    "units": None,
                }
            ],
            "artifacts": {},
        },
    )

    result = runner.invoke(app, ["verify", str(FIXTURE_DIR / "success.py")])

    assert result.exit_code == 3
