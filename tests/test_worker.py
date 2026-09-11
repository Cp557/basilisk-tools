import json
from pathlib import Path

import pytest

from basilisk_tools import worker


def _script(tmp_path: Path, source: str) -> Path:
    path = tmp_path / "scenario.py"
    path.write_text(source, encoding="utf-8")
    return path


def test_worker_executes_successful_script(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    scenario = _script(tmp_path, "print('worker success')\n")
    outcome = tmp_path / "outcome.json"

    exit_code = worker.execute_scenario(scenario, outcome)

    assert exit_code == 0
    assert capsys.readouterr().out == "worker success\n"
    assert json.loads(outcome.read_text()) == {
        "schema_version": 1,
        "exit_code": 0,
        "error": None,
    }


def test_worker_records_python_failure(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    scenario = _script(tmp_path, "raise LookupError('broken scenario')\n")
    outcome = tmp_path / "outcome.json"

    exit_code = worker.execute_scenario(scenario, outcome)

    assert exit_code == 1
    assert "LookupError: broken scenario" in capsys.readouterr().err
    assert json.loads(outcome.read_text())["error"] == {
        "type": "LookupError",
        "message": "broken scenario",
    }


@pytest.mark.parametrize(
    ("statement", "expected_code", "expected_message"),
    [
        ("raise SystemExit()", 0, None),
        ("raise SystemExit(4)", 4, "4"),
        ("raise SystemExit('stop')", 1, "stop"),
    ],
)
def test_worker_preserves_system_exit(
    tmp_path: Path,
    capsys: pytest.CaptureFixture,
    statement: str,
    expected_code: int,
    expected_message: str | None,
) -> None:
    scenario = _script(tmp_path, statement)
    outcome = tmp_path / "outcome.json"

    assert worker.execute_scenario(scenario, outcome) == expected_code

    payload = json.loads(outcome.read_text())
    assert payload["exit_code"] == expected_code
    if expected_message is None:
        assert payload["error"] is None
    else:
        assert payload["error"] == {
            "type": "SystemExit",
            "message": expected_message,
        }
    captured = capsys.readouterr()
    if statement.endswith("'stop')"):
        assert captured.err == "stop\n"


def test_worker_main_parses_arguments(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    scenario = _script(tmp_path, "pass\n")
    outcome = tmp_path / "outcome.json"
    monkeypatch.setattr(
        "sys.argv",
        ["worker", "--outcome", str(outcome), str(scenario)],
    )

    assert worker.main() == 0
    assert json.loads(outcome.read_text())["exit_code"] == 0
