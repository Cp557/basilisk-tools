"""Minimal artifact registration shared with instrumented scenarios."""

import json
import os
from pathlib import Path

ARTIFACTS_DIRECTORY_ENV = "BSK_ARTIFACTS_DIR"
ARTIFACT_MANIFEST_ENV = "BSK_ARTIFACT_MANIFEST"


def registered_output_directory(default: Path) -> Path:
    """Use the active run's artifact directory when one is available."""
    configured = os.environ.get(ARTIFACTS_DIRECTORY_ENV)
    return Path(configured) if configured else default


def register_artifacts(artifacts: dict[str, str]) -> None:
    """Register generated files with `bsk run`; otherwise do nothing."""
    manifest_value = os.environ.get(ARTIFACT_MANIFEST_ENV)
    if not manifest_value:
        return

    manifest_path = Path(manifest_value)
    registered = {name: str(Path(path).resolve()) for name, path in artifacts.items()}
    manifest_path.write_text(
        json.dumps(registered, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
