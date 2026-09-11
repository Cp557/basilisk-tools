"""Render the README's reproducible terminal walkthrough as an animated GIF."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

WIDTH = 1_000
HEIGHT = 560
BACKGROUND = "#0d1117"
FOREGROUND = "#e6edf3"
MUTED = "#8b949e"
GREEN = "#3fb950"
BLUE = "#58a6ff"
YELLOW = "#d29922"
OUTPUT = Path(__file__).parent / "assets" / "demo.gif"

SCENES = (
    (
        "$ uv run bsk doctor",
        (
            (GREEN, "Basilisk Tools environment: ready"),
            (FOREGROUND, "Python: 3.11"),
            (FOREGROUND, "Basilisk: 2.11.1"),
            (FOREGROUND, "Basilisk Tools: 0.1.0"),
            (MUTED, "Deterministic environment evidence before simulation."),
        ),
    ),
    (
        "$ uv run bsk inspect examples/orbit_propagation/scenario.py",
        (
            (FOREGROUND, "Scenario: point_mass_vs_j2_leo"),
            (BLUE, "Case: point-mass"),
            (FOREGROUND, "  leoSpacecraft -> Rec:SCStatesMsg"),
            (BLUE, "Case: j2"),
            (FOREGROUND, "  leoSpacecraft -> Rec:SCStatesMsg"),
            (MUTED, "2 cases | 2 modules each | 1 message connection each"),
        ),
    ),
    (
        "$ uv run bsk run examples/orbit_propagation/scenario.py",
        (
            (GREEN, "Run <run-id>: success"),
            (FOREGROUND, "Artifacts: .bsk/runs/<run-id>/"),
            (FOREGROUND, "  result.json       metadata.json"),
            (FOREGROUND, "  stdout.log        stderr.log"),
            (FOREGROUND, "  telemetry.csv     verification.json"),
            (MUTED, "Scenario output stays in logs; command JSON stays parseable."),
        ),
    ),
    (
        "$ uv run bsk verify examples/orbit_propagation/scenario.py",
        (
            (GREEN, "Verification: PASS (point_mass_vs_j2_leo)"),
            (GREEN, "  PASS  point-mass.bounded_keplerian_energy_drift"),
            (GREEN, "  PASS  point-mass.bounded_angular_momentum_drift"),
            (GREEN, "  PASS  j2.j2_raan_rate"),
            (GREEN, "  PASS  j2.bounded_angular_momentum_z_drift"),
            (MUTED, "Every claim is backed by telemetry and a declared tolerance."),
        ),
    ),
    (
        "Verified result",
        (
            (BLUE, "J2 nodal regression: -8.348e-7 rad/s"),
            (FOREGROUND, "First-order theory:  -8.338e-7 rad/s"),
            (GREEN, "Relative error:         0.117%"),
            (FOREGROUND, "Point-mass energy drift: 7.97e-11"),
            (FOREGROUND, "J2 angular-momentum-z drift: 3.95e-11"),
            (YELLOW, "Scope: Earth LEO, point mass vs degree-2 J2 only"),
        ),
    ),
)


def _font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = (
        "/System/Library/Fonts/SFNSMono.ttf",
        "/System/Library/Fonts/SFNSMonoBold.ttf" if bold else "",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    )
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default(size=size)


def _frame(title: str, lines: tuple[tuple[str, str], ...]) -> Image.Image:
    image = Image.new("RGB", (WIDTH, HEIGHT), BACKGROUND)
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((10, 10, WIDTH - 10, HEIGHT - 10), 16, outline="#30363d")
    draw.ellipse((32, 31, 48, 47), fill="#ff5f56")
    draw.ellipse((58, 31, 74, 47), fill="#ffbd2e")
    draw.ellipse((84, 31, 100, 47), fill="#27c93f")
    draw.line((20, 66, WIDTH - 20, 66), fill="#30363d", width=2)

    title_font = _font(22, bold=True)
    body_font = _font(21)
    draw.text((36, 94), title, font=title_font, fill=FOREGROUND)
    y = 154
    for color, line in lines:
        draw.text((36, y), line, font=body_font, fill=color)
        y += 52
    return image


def main() -> None:
    """Render every scene and save an optimized looping animation."""
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    frames = [_frame(title, lines) for title, lines in SCENES]
    frames[0].save(
        OUTPUT,
        save_all=True,
        append_images=frames[1:],
        duration=(1_800, 2_100, 2_100, 2_400, 3_000),
        loop=0,
        optimize=True,
    )
    print(OUTPUT)


if __name__ == "__main__":
    main()
