"""Deterministic verification for instrumented scenarios and saved runs."""

from __future__ import annotations

import json
import subprocess
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from basilisk_tools.instrumentation import error_payload

DEFAULT_VERIFICATION_DIRECTORY = Path(".bsk/verifications")
DEFAULT_VERIFICATION_TIMEOUT_SECONDS = 300.0


def _identifier() -> str:
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S.%fZ")
    return f"{timestamp}-{uuid.uuid4().hex[:8]}"


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _validate_report(payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get("schema_version") != 1:
        raise ValueError("Verification report must use schema_version 1.")
    if not isinstance(payload.get("passed"), bool):
        raise ValueError("Verification report must contain a boolean 'passed'.")
    if not isinstance(payload.get("checks"), list):
        raise ValueError("Verification report must contain a 'checks' list.")
    return payload


def _load_saved_verification(target: Path) -> dict[str, Any]:
    if target.is_dir():
        direct_report = target / "verification.json"
        if direct_report.is_file():
            return _validate_report(_read_json(direct_report))
        result_path = target / "result.json"
    else:
        result_path = target

    payload = _read_json(result_path)
    if "checks" in payload and "passed" in payload:
        return _validate_report(payload)

    if payload.get("schema_version") != 1:
        raise ValueError("Run result must use schema_version 1.")

    verification_path = payload.get("artifacts", {}).get("verification")
    if not verification_path:
        raise ValueError(
            "Run does not contain a registered semantic verification artifact."
        )
    return _validate_report(_read_json(Path(verification_path)))


def _timeout_output(value: str | bytes | None) -> str:
    if value is None:
        return ""
    return value.decode(errors="replace") if isinstance(value, bytes) else value


def _verify_scenario(
    scenario_path: Path,
    *,
    verification_directory: Path,
    timeout_seconds: float,
) -> dict[str, Any]:
    operation_directory = verification_directory.resolve() / _identifier()
    artifacts_directory = operation_directory / "artifacts"
    operation_directory.mkdir(parents=True)
    artifacts_directory.mkdir()
    response_path = operation_directory / ".worker-response.json"
    stdout_path = operation_directory / "stdout.log"
    stderr_path = operation_directory / "stderr.log"
    report_path = operation_directory / "verification.json"

    command = [
        sys.executable,
        "-m",
        "basilisk_tools.tool_worker",
        "verify",
        "--response",
        str(response_path),
        "--output-dir",
        str(artifacts_directory),
        str(scenario_path),
    ]
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
        stdout = completed.stdout
        stderr = completed.stderr
        try:
            report = _read_json(response_path)
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            message = stderr.strip() or (
                f"Verification worker exited with code {completed.returncode}."
            )
            report = error_payload(scenario_path, RuntimeError(message))
    except subprocess.TimeoutExpired as error:
        stdout = _timeout_output(error.stdout)
        stderr = _timeout_output(error.stderr)
        report = error_payload(
            scenario_path,
            TimeoutError(
                f"Verification exceeded the {timeout_seconds:g} second timeout."
            ),
        )

    stdout_path.write_text(stdout, encoding="utf-8")
    stderr_path.write_text(stderr, encoding="utf-8")
    response_path.unlink(missing_ok=True)

    artifacts = dict(report.get("artifacts", {}))
    artifacts.update(
        {
            "verification": str(report_path),
            "verification_directory": str(operation_directory),
            "stdout": str(stdout_path),
            "stderr": str(stderr_path),
        }
    )
    report["artifacts"] = artifacts
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def verify_target(
    target: Path,
    *,
    verification_directory: Path = DEFAULT_VERIFICATION_DIRECTORY,
    timeout_seconds: float = DEFAULT_VERIFICATION_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """Verify an instrumented scenario or load a saved verification result."""
    target = target.resolve(strict=True)
    if target.is_file() and target.suffix == ".py":
        return _verify_scenario(
            target,
            verification_directory=verification_directory,
            timeout_seconds=timeout_seconds,
        )
    return _load_saved_verification(target)
