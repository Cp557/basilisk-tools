import json
from pathlib import Path

from basilisk_tools.artifacts import (
    ARTIFACT_MANIFEST_ENV,
    ARTIFACTS_DIRECTORY_ENV,
    register_artifacts,
    registered_output_directory,
)


def test_registered_output_directory_uses_environment(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.delenv(ARTIFACTS_DIRECTORY_ENV, raising=False)
    assert registered_output_directory(Path("default")) == Path("default")

    monkeypatch.setenv(ARTIFACTS_DIRECTORY_ENV, str(tmp_path))
    assert registered_output_directory(Path("default")) == tmp_path


def test_artifact_registration_writes_absolute_paths(
    tmp_path: Path, monkeypatch
) -> None:
    manifest = tmp_path / "manifest.json"
    artifact = tmp_path / "artifact.txt"
    monkeypatch.setenv(ARTIFACT_MANIFEST_ENV, str(manifest))

    register_artifacts({"evidence": str(artifact)})

    assert json.loads(manifest.read_text()) == {"evidence": str(artifact.resolve())}


def test_artifact_registration_is_optional(monkeypatch) -> None:
    monkeypatch.delenv(ARTIFACT_MANIFEST_ENV, raising=False)

    register_artifacts({"unused": "file.txt"})
