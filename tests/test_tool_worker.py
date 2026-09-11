import json
from pathlib import Path

import pytest

from basilisk_tools import tool_worker

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "scenarios"


def test_tool_worker_inspects_contract() -> None:
    payload = tool_worker.execute("inspect", FIXTURE_DIR / "instrumented.py", None)

    assert payload["supported"] is True
    assert payload["cases"][0]["runtime"]["modules"][0]["tag"] == "testSpacecraft"


def test_tool_worker_verifies_contract(tmp_path: Path) -> None:
    payload = tool_worker.execute("verify", FIXTURE_DIR / "instrumented.py", tmp_path)

    assert payload["passed"] is True
    assert payload["checks"][0]["actual"] == 42.0
    assert Path(payload["artifacts"]["evidence"]).is_file()


def test_tool_worker_reports_unsupported_standard_scenario() -> None:
    payload = tool_worker.execute("inspect", FIXTURE_DIR / "success.py", None)

    assert payload["supported"] is False
    assert payload["error"] is None


def test_tool_worker_structures_operation_errors() -> None:
    payload = tool_worker.execute("unknown", FIXTURE_DIR / "success.py", None)

    assert payload["error"]["type"] == "ValueError"


def test_tool_worker_main_writes_response(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    response = tmp_path / "response.json"
    monkeypatch.setattr(
        "sys.argv",
        [
            "tool_worker",
            "inspect",
            "--response",
            str(response),
            str(FIXTURE_DIR / "instrumented.py"),
        ],
    )

    assert tool_worker.main() == 0
    assert json.loads(response.read_text())["supported"] is True
