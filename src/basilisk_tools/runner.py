"""Isolated scenario execution and durable run artifacts."""

import hashlib
import json
import os
import platform
import signal
import subprocess
import sys
import time
import uuid
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

from basilisk_tools import __version__
from basilisk_tools.artifacts import ARTIFACT_MANIFEST_ENV, ARTIFACTS_DIRECTORY_ENV
from basilisk_tools.results import ErrorSummary, RunMetadata, RunResult, RunStatus

DEFAULT_RUNS_DIRECTORY = Path(".bsk/runs")
DEFAULT_TIMEOUT_SECONDS = 300.0
TERMINATION_GRACE_SECONDS = 2.0
WORKER_OUTCOME_NAME = ".worker-outcome.json"


def _scenario_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as scenario_file:
        for chunk in iter(lambda: scenario_file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _basilisk_version() -> str | None:
    try:
        return version("bsk")
    except PackageNotFoundError:
        return None


def _new_run_id() -> str:
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S.%fZ")
    return f"{timestamp}-{uuid.uuid4().hex[:8]}"


def _write_json(path: Path, payload: str) -> None:
    temporary_path = path.with_suffix(f"{path.suffix}.tmp")
    temporary_path.write_text(payload + "\n", encoding="utf-8")
    temporary_path.replace(path)


def _stop_process(process: subprocess.Popen[Any]) -> None:
    if process.poll() is not None:
        return

    try:
        if os.name == "posix":
            os.killpg(process.pid, signal.SIGTERM)
        else:  # pragma: no cover - Windows behavior
            process.terminate()
        process.wait(timeout=TERMINATION_GRACE_SECONDS)
    except subprocess.TimeoutExpired:
        if os.name == "posix":
            os.killpg(process.pid, signal.SIGKILL)
        else:  # pragma: no cover - Windows behavior
            process.kill()
        process.wait()


def _read_worker_outcome(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None


def run_scenario(
    scenario_path: Path,
    *,
    runs_directory: Path = DEFAULT_RUNS_DIRECTORY,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
) -> RunResult:
    """Run a trusted scenario in a child process and preserve its artifacts."""
    scenario_path = scenario_path.resolve(strict=True)
    if not scenario_path.is_file():
        raise ValueError(f"Scenario is not a file: {scenario_path}")
    if timeout_seconds <= 0:
        raise ValueError("Timeout must be greater than zero.")

    run_id = _new_run_id()
    run_directory = runs_directory.resolve() / run_id
    run_directory.mkdir(parents=True)

    stdout_path = run_directory / "stdout.log"
    stderr_path = run_directory / "stderr.log"
    metadata_path = run_directory / "metadata.json"
    result_path = run_directory / "result.json"
    outcome_path = run_directory / WORKER_OUTCOME_NAME
    artifacts_directory = run_directory / "artifacts"
    artifact_manifest_path = run_directory / ".artifact-manifest.json"
    artifacts_directory.mkdir()

    started_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    metadata = RunMetadata(
        run_id=run_id,
        scenario_path=str(scenario_path),
        scenario_sha256=_scenario_hash(scenario_path),
        started_at=started_at,
        python_version=platform.python_version(),
        basilisk_version=_basilisk_version(),
        basilisk_tools_version=__version__,
    )
    _write_json(metadata_path, metadata.to_json())

    artifacts = {
        "run_directory": str(run_directory),
        "result": str(result_path),
        "metadata": str(metadata_path),
        "stdout": str(stdout_path),
        "stderr": str(stderr_path),
        "artifacts_directory": str(artifacts_directory),
    }
    command = [
        sys.executable,
        "-m",
        "basilisk_tools.worker",
        "--outcome",
        str(outcome_path),
        str(scenario_path),
    ]
    started = time.monotonic()
    status = RunStatus.FAILURE
    exit_code: int | None = None
    error: ErrorSummary | None = None
    environment = os.environ.copy()
    environment[ARTIFACTS_DIRECTORY_ENV] = str(artifacts_directory)
    environment[ARTIFACT_MANIFEST_ENV] = str(artifact_manifest_path)

    with (
        stdout_path.open("w", encoding="utf-8") as stdout_file,
        stderr_path.open("w", encoding="utf-8") as stderr_file,
    ):
        try:
            process = subprocess.Popen(
                command,
                stdout=stdout_file,
                stderr=stderr_file,
                env=environment,
                start_new_session=os.name == "posix",
            )
        except OSError as launch_error:
            error = ErrorSummary(type="LaunchError", message=str(launch_error))
        else:
            try:
                exit_code = process.wait(timeout=timeout_seconds)
                worker_outcome = _read_worker_outcome(outcome_path)
                if exit_code == 0:
                    status = RunStatus.SUCCESS
                elif worker_outcome and worker_outcome.get("error"):
                    error = ErrorSummary(**worker_outcome["error"])
                else:
                    error = ErrorSummary(
                        type="ProcessError",
                        message=f"Scenario process exited with code {exit_code}.",
                    )
            except subprocess.TimeoutExpired:
                _stop_process(process)
                exit_code = process.returncode
                status = RunStatus.TIMEOUT
                error = ErrorSummary(
                    type="TimeoutExpired",
                    message=(
                        f"Scenario exceeded the {timeout_seconds:g} second timeout."
                    ),
                )
            except KeyboardInterrupt:
                _stop_process(process)
                exit_code = process.returncode
                status = RunStatus.INTERRUPTED
                error = ErrorSummary(
                    type="KeyboardInterrupt",
                    message="Scenario execution was interrupted by the user.",
                )

    elapsed_seconds = time.monotonic() - started
    outcome_path.unlink(missing_ok=True)
    registered_artifacts = _read_worker_outcome(artifact_manifest_path)
    if registered_artifacts:
        artifacts.update(
            {
                name: path
                for name, path in registered_artifacts.items()
                if isinstance(name, str) and isinstance(path, str)
            }
        )
    artifact_manifest_path.unlink(missing_ok=True)
    result = RunResult(
        run_id=run_id,
        status=status,
        elapsed_seconds=elapsed_seconds,
        exit_code=exit_code,
        artifacts=artifacts,
        error=error,
    )
    _write_json(result_path, result.to_json())
    return result
