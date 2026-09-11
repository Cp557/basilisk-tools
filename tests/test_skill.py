import re
from pathlib import Path

SKILL_DIR = Path(__file__).parents[1] / "skills" / "basilisk"
SKILL_PATH = SKILL_DIR / "SKILL.md"
INSTALLATION_PATH = Path(__file__).parents[1] / "docs" / "skill-installation.md"


def _frontmatter(text: str) -> dict[str, str]:
    _, raw_frontmatter, _ = text.split("---", 2)
    return {
        key.strip(): value.strip()
        for line in raw_frontmatter.strip().splitlines()
        for key, value in (line.split(":", 1),)
    }


def test_skill_metadata_supports_explicit_and_implicit_discovery() -> None:
    text = SKILL_PATH.read_text(encoding="utf-8")
    metadata = _frontmatter(text)

    assert metadata["name"] == "basilisk"
    assert "AVS Basilisk" in metadata["description"]
    assert "simulation" in metadata["description"]
    assert "debug" in metadata["description"]
    assert "disable-model-invocation" not in metadata


def test_every_local_skill_reference_resolves() -> None:
    text = SKILL_PATH.read_text(encoding="utf-8")
    local_links = re.findall(r"\]\((references/[^)]+)\)", text)

    assert len(local_links) == 6
    assert all((SKILL_DIR / link).is_file() for link in local_links)


def test_skill_core_loop_uses_every_v1_command() -> None:
    text = SKILL_PATH.read_text(encoding="utf-8")

    for command in ("doctor", "inspect", "run", "verify"):
        assert f"bsk {command}" in text


def test_installation_uses_one_canonical_skill_for_both_agents() -> None:
    text = INSTALLATION_PATH.read_text(encoding="utf-8")

    assert ".agents/skills/basilisk" in text
    assert ".claude/skills/basilisk" in text
    assert "skills/basilisk" in text
    assert "$basilisk" in text
    assert "/basilisk" in text
    assert "implicit" in text
