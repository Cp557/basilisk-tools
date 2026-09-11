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
        "evals/README.md",
        "LICENSE",
        "REFERENCE.md",
        "PLAN.md",
    ):
        assert f"]({relative_path})" in text
        assert (ROOT / relative_path).is_file()


def test_readme_local_images_exist() -> None:
    text = README.read_text(encoding="utf-8")
    image_paths = re.findall(r'(?:!\[[^]]*\]\(|src=")([^)"]+\.(?:gif|png))', text)

    assert set(image_paths) == {
        "docs/assets/demo.gif",
        "docs/assets/orbit_comparison.png",
        "docs/assets/orbital_elements.png",
    }
    for relative_path in image_paths:
        assert (ROOT / relative_path).stat().st_size > 50_000


def test_generated_visuals_have_expected_formats() -> None:
    demo = (ROOT / "docs/assets/demo.gif").read_bytes()
    orbit_plot = (ROOT / "docs/assets/orbit_comparison.png").read_bytes()
    elements_plot = (ROOT / "docs/assets/orbital_elements.png").read_bytes()

    assert demo.startswith(b"GIF89a")
    assert orbit_plot.startswith(b"\x89PNG\r\n\x1a\n")
    assert elements_plot.startswith(b"\x89PNG\r\n\x1a\n")


def test_release_claims_keep_pending_work_visible() -> None:
    readme = README.read_text(encoding="utf-8")
    results = (ROOT / "evals/results/README.md").read_text(encoding="utf-8")

    assert "no comparative Codex/Claude results are\npublished yet" in readme
    assert "No comparative agent runs are published yet" in results
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
