import json
import subprocess
from pathlib import Path

import pytest

from basilisk_tools.verification import verify_target

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "scenarios"


def test_scenario_verification_preserves_report_and_logs(tmp_path: Path) -> None:
    report = verify_target(
        FIXTURE_DIR / "instrumented.py",
        verification_directory=tmp_path,
    )

    assert report["supported"] is True
    assert report["passed"] is True
    assert report["checks"][0]["name"] == "known_value"
    assert Path(report["artifacts"]["verification"]).is_file()
    assert (
        "instrumented scenario loaded"
        in Path(report["artifacts"]["stdout"]).read_text()
    )


def test_saved_verification_directory_is_loaded(tmp_path: Path) -> None:
    report_path = tmp_path / "verification.json"
    report_path.write_text(
        json.dumps({"schema_version": 1, "passed": True, "checks": []}),
        encoding="utf-8",
    )

    assert verify_target(tmp_path)["passed"] is True
    assert verify_target(report_path)["checks"] == []


def test_registered_run_verification_is_loaded(tmp_path: Path) -> None:
    report_path = tmp_path / "semantic.json"
    report_path.write_text(
        json.dumps({"schema_version": 1, "passed": True, "checks": []}),
        encoding="utf-8",
    )
    result_path = tmp_path / "result.json"
    result_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "artifacts": {"verification": str(report_path)},
            }
        ),
        encoding="utf-8",
    )

    assert verify_target(result_path)["passed"] is True


def test_run_without_semantic_artifact_is_rejected(tmp_path: Path) -> None:
    result_path = tmp_path / "result.json"
    result_path.write_text(
        json.dumps({"schema_version": 1, "artifacts": {}}), encoding="utf-8"
    )

    with pytest.raises(ValueError, match="semantic verification"):
        verify_target(result_path)


def test_invalid_saved_verification_schema_is_rejected(tmp_path: Path) -> None:
    report_path = tmp_path / "verification.json"
    report_path.write_text(
        json.dumps({"schema_version": 2, "passed": True, "checks": []}),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="schema_version 1"):
        verify_target(report_path)


def test_verification_timeout_is_structured(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    timeout = subprocess.TimeoutExpired("verify", 0.01, output="started")
    monkeypatch.setattr(
        "basilisk_tools.verification.subprocess.run",
        lambda *args, **kwargs: (_ for _ in ()).throw(timeout),
    )

    report = verify_target(
        FIXTURE_DIR / "instrumented.py",
        verification_directory=tmp_path,
        timeout_seconds=0.01,
    )

    assert report["error"]["type"] == "TimeoutError"
    assert Path(report["artifacts"]["stdout"]).read_text() == "started"
