"""Versioned structured result models shared by CLI commands."""

import json
from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any

SCHEMA_VERSION = 1


class RunStatus(StrEnum):
    """Terminal states for a scenario launch."""

    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    INTERRUPTED = "interrupted"


@dataclass(frozen=True)
class ErrorSummary:
    """A concise, machine-readable failure description."""

    type: str
    message: str


@dataclass(frozen=True)
class RunMetadata:
    """Reproducibility metadata recorded for a scenario launch."""

    run_id: str
    scenario_path: str
    scenario_sha256: str
    started_at: str
    python_version: str
    basilisk_version: str | None
    basilisk_tools_version: str
    schema_version: int = SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation."""
        return asdict(self)

    def to_json(self) -> str:
        """Serialize the metadata using stable, readable formatting."""
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)


@dataclass(frozen=True)
class RunResult:
    """Process-level outcome for a scenario launch."""

    run_id: str
    status: RunStatus
    elapsed_seconds: float
    exit_code: int | None
    artifacts: dict[str, str] = field(default_factory=dict)
    error: ErrorSummary | None = None
    schema_version: int = SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation."""
        return asdict(self)

    def to_json(self) -> str:
        """Serialize the result using stable, readable formatting."""
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)
