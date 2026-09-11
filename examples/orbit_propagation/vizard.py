"""Generate offline Vizard playback files for the reference orbit cases."""

from pathlib import Path

from basilisk_tools.artifacts import registered_output_directory

if __package__:
    from .scenario import generate_vizard_playback
else:
    from scenario import generate_vizard_playback

DEFAULT_OUTPUT_DIRECTORY = Path(".bsk/examples/orbit_propagation/vizard")


def main() -> int:
    """Record both gravity cases and register their playback artifacts."""
    output_directory = registered_output_directory(DEFAULT_OUTPUT_DIRECTORY)
    report = generate_vizard_playback(output_directory)
    print(f"Point-mass playback: {report.artifacts['point_mass_vizard']}")
    print(f"J2 playback: {report.artifacts['j2_vizard']}")
    print(f"Verification: {report.artifacts['verification']}")
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
