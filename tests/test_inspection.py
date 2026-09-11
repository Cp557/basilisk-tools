from pathlib import Path
from types import SimpleNamespace

import pytest

from basilisk_tools.inspection import inspect_scenario, inspect_simulation
from basilisk_tools.instrumentation import load_contract

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "scenarios"


def test_inspection_reads_basilisk_runtime_graph() -> None:
    contract = load_contract(FIXTURE_DIR / "instrumented.py")
    case = contract.build_cases()[0]

    report = inspect_simulation(case.simulation)

    assert report["supported"] is True
    assert report["source"] == "Basilisk SimBaseClass.GetMessageConnectionGraph"
    assert report["execution_order"] == ["testSpacecraft", "Rec:SCStatesMsg"]
    assert report["processes"][0]["name"] == "testProcess"
    assert report["processes"][0]["tasks"][0]["name"] == "testTask"
    assert report["message_connections"][0]["payload_type"] == "SCStatesMsgPayload"


def test_inspection_reports_missing_runtime_api() -> None:
    report = inspect_simulation(SimpleNamespace())

    assert report == {
        "supported": False,
        "reason": "Basilisk runtime does not expose GetMessageConnectionGraph.",
    }


def test_scenario_inspection_runs_in_child_process() -> None:
    report = inspect_scenario(FIXTURE_DIR / "instrumented.py")

    assert report["supported"] is True
    assert report["scenario"] == "instrumented_test"
    assert report["cases"][0]["telemetry"][0]["frame"] == "inertial N"


def test_standard_scenario_is_honestly_unsupported() -> None:
    report = inspect_scenario(FIXTURE_DIR / "success.py")

    assert report["supported"] is False
    assert "does not declare" in report["reason"]


def test_inspection_timeout_is_structured(monkeypatch: pytest.MonkeyPatch) -> None:
    def time_out(*args, **kwargs):
        raise __import__("subprocess").TimeoutExpired("inspect", 0.01)

    monkeypatch.setattr("basilisk_tools.inspection.subprocess.run", time_out)

    report = inspect_scenario(FIXTURE_DIR / "instrumented.py", timeout_seconds=0.01)

    assert report["error"]["type"] == "TimeoutError"
