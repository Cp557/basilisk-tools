import json
from pathlib import Path

import pytest

from basilisk_tools.instrumentation import (
    InstrumentedScenario,
    VerificationCheck,
    VerificationReport,
    declares_contract,
    error_payload,
    load_contract,
    unsupported_payload,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "scenarios"


def test_contract_detection_does_not_import_scenario() -> None:
    assert declares_contract(FIXTURE_DIR / "instrumented.py") is True
    assert declares_contract(FIXTURE_DIR / "success.py") is False


def test_contract_loads_expected_entrypoint(capsys: pytest.CaptureFixture) -> None:
    contract = load_contract(FIXTURE_DIR / "instrumented.py")

    assert isinstance(contract, InstrumentedScenario)
    assert contract.name == "instrumented_test"
    assert capsys.readouterr().out == "instrumented scenario loaded\n"


def test_invalid_contract_return_is_rejected(tmp_path: Path) -> None:
    scenario = tmp_path / "invalid.py"
    scenario.write_text(
        "def basilisk_tools_scenario():\n    return object()\n",
        encoding="utf-8",
    )

    with pytest.raises(TypeError, match="InstrumentedScenario"):
        load_contract(scenario)


def test_verification_report_serializes() -> None:
    report = VerificationReport(
        scenario="test",
        passed=True,
        checks=(VerificationCheck("check", True, 1, 1, 0, None),),
    )

    payload = json.loads(report.to_json())
    assert payload["schema_version"] == 1
    assert payload["checks"][0]["name"] == "check"


def test_unsupported_and_error_payloads_are_versioned(tmp_path: Path) -> None:
    unsupported = unsupported_payload(tmp_path, "not instrumented")
    failed = error_payload(tmp_path, RuntimeError("broken"))

    assert unsupported["supported"] is False
    assert unsupported["schema_version"] == 1
    assert failed["supported"] is True
    assert failed["error"] == {"type": "RuntimeError", "message": "broken"}
