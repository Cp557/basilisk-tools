import re
from pathlib import Path

ROOT = Path(__file__).parents[1]
README = ROOT / "README.md"


def test_readme_links_to_release_documentation() -> None:
    text = README.read_text(encoding="utf-8")

    for relative_path in (
        "docs/architecture.md",
        "docs/orbit-results.md",
        "docs/demo.md",
        "docs/example-output.md",
        "docs/release-checklist.md",
        "docs/skill-installation.md",
        "docs/vizard.md",
        "LICENSE",
        "REFERENCE.md",
    ):
        assert f"]({relative_path})" in text
        assert (ROOT / relative_path).is_file()


def test_readme_local_images_exist() -> None:
    text = README.read_text(encoding="utf-8")
    image_paths = re.findall(r'(?:!\[[^]]*\]\(|src=")([^)"]+\.(?:gif|png|svg))', text)
    local_image_paths = {
        path for path in image_paths if not path.startswith(("http://", "https://"))
    }

    assert local_image_paths == {
        "icon.svg",
        "docs/assets/demo.gif",
        "docs/assets/orbit_comparison.png",
        "docs/assets/orbital_elements.png",
    }
    for relative_path in local_image_paths:
        assert (ROOT / relative_path).stat().st_size > 100


def test_generated_visuals_have_expected_formats() -> None:
    demo = (ROOT / "docs/assets/demo.gif").read_bytes()
    orbit_plot = (ROOT / "docs/assets/orbit_comparison.png").read_bytes()
    elements_plot = (ROOT / "docs/assets/orbital_elements.png").read_bytes()

    assert demo.startswith(b"GIF89a")
    assert orbit_plot.startswith(b"\x89PNG\r\n\x1a\n")
    assert elements_plot.startswith(b"\x89PNG\r\n\x1a\n")


def test_release_metadata_is_visible() -> None:
    readme = README.read_text(encoding="utf-8")

    assert "v0.1.0" in readme
    assert "License: MIT" in readme
    assert "https://github.com/Cp557/basilisk-tools" in readme


def test_ci_runs_tests_lint_format_and_package_build() -> None:
    workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")

    for command in (
        "uv run ruff check .",
        "uv run ruff format --check .",
        "uv run pytest",
        "uv build",
    ):
        assert command in workflow
