"""Create a point-mass Earth orbit and export state telemetry."""

from pathlib import Path

from basilisk_tools.artifacts import register_artifacts, registered_output_directory

OUTPUT_DIRECTORY = Path("artifacts")
TELEMETRY_COLUMNS = (
    "time_s",
    "r_x_m",
    "r_y_m",
    "r_z_m",
    "v_x_m_s",
    "v_y_m_s",
    "v_z_m_s",
)

SEMI_MAJOR_AXIS_M = 7_000_000.0
ECCENTRICITY = 0.01
INCLINATION_DEG = 55.0
RAAN_DEG = 40.0
ARGUMENT_OF_PERIAPSIS_DEG = 30.0
TRUE_ANOMALY_DEG = 0.0
DURATION_S = 1_200.0
TIME_STEP_S = 10.0
SAMPLE_INTERVAL_S = 60.0


def main() -> int:
    """Build and execute the requested Basilisk scenario."""
    # TODO: configure Basilisk, record the state, and write telemetry.csv.
    raise NotImplementedError("Implement the two-body orbit scenario")


if __name__ == "__main__":
    artifacts_directory = registered_output_directory(OUTPUT_DIRECTORY)
    exit_code = main()
    register_artifacts(
        {"telemetry": str((artifacts_directory / "telemetry.csv").resolve())}
    )
    raise SystemExit(exit_code)
