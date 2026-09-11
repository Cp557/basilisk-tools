"""Numerical diagnostics and plots for the orbit-propagation example."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

# Constants represented by Basilisk's GGM03S-J2-only coefficient file.
EARTH_J2 = 1.0826353865466185e-3
EARTH_EQUATORIAL_RADIUS_M = 6_378_136.3


@dataclass(frozen=True)
class OrbitMetrics:
    """Scalar diagnostics derived from one telemetry history."""

    initial_keplerian_specific_energy_j_kg: float
    max_relative_keplerian_specific_energy_drift: float
    initial_specific_angular_momentum_m2_s: float
    max_relative_specific_angular_momentum_drift: float
    initial_specific_angular_momentum_z_m2_s: float
    max_relative_specific_angular_momentum_z_drift: float
    raan_change_rad: float
    raan_rate_rad_s: float
    expected_raan_rate_rad_s: float
    raan_rate_relative_error: float | None


def _max_relative_drift(values: np.ndarray) -> float:
    initial = float(values[0])
    return float(np.max(np.abs(values - initial)) / abs(initial))


def calculate_metrics(
    *,
    times_s: np.ndarray,
    positions_m: np.ndarray,
    velocities_m_s: np.ndarray,
    elements: np.ndarray,
    mu_m3_s2: float,
    semi_major_axis_m: float,
    eccentricity: float,
    inclination_rad: float,
    include_j2: bool,
) -> OrbitMetrics:
    """Calculate conservation diagnostics and a fitted secular RAAN rate.

    Keplerian specific energy excludes the J2 potential. It is therefore a
    conservation diagnostic only for the point-mass run. The inertial z
    component of angular momentum remains the useful J2 symmetry diagnostic.
    """
    radius_m = np.linalg.norm(positions_m, axis=1)
    speed_squared_m2_s2 = np.sum(velocities_m_s**2, axis=1)
    keplerian_energy_j_kg = speed_squared_m2_s2 / 2.0 - mu_m3_s2 / radius_m

    angular_momentum_m2_s = np.cross(positions_m, velocities_m_s)
    angular_momentum_norm_m2_s = np.linalg.norm(angular_momentum_m2_s, axis=1)
    angular_momentum_z_m2_s = angular_momentum_m2_s[:, 2]

    unwrapped_raan_rad = np.unwrap(elements[:, 3])
    raan_rate_rad_s = float(np.polyfit(times_s, unwrapped_raan_rad, 1)[0])
    expected_raan_rate_rad_s = 0.0
    relative_error = None
    if include_j2:
        mean_motion_rad_s = np.sqrt(mu_m3_s2 / semi_major_axis_m**3)
        semi_latus_rectum_m = semi_major_axis_m * (1.0 - eccentricity**2)
        expected_raan_rate_rad_s = float(
            -1.5
            * mean_motion_rad_s
            * EARTH_J2
            * (EARTH_EQUATORIAL_RADIUS_M / semi_latus_rectum_m) ** 2
            * np.cos(inclination_rad)
        )
        relative_error = abs(
            (raan_rate_rad_s - expected_raan_rate_rad_s) / expected_raan_rate_rad_s
        )

    return OrbitMetrics(
        initial_keplerian_specific_energy_j_kg=float(keplerian_energy_j_kg[0]),
        max_relative_keplerian_specific_energy_drift=_max_relative_drift(
            keplerian_energy_j_kg
        ),
        initial_specific_angular_momentum_m2_s=float(angular_momentum_norm_m2_s[0]),
        max_relative_specific_angular_momentum_drift=_max_relative_drift(
            angular_momentum_norm_m2_s
        ),
        initial_specific_angular_momentum_z_m2_s=float(angular_momentum_z_m2_s[0]),
        max_relative_specific_angular_momentum_z_drift=_max_relative_drift(
            angular_momentum_z_m2_s
        ),
        raan_change_rad=float(unwrapped_raan_rad[-1] - unwrapped_raan_rad[0]),
        raan_rate_rad_s=raan_rate_rad_s,
        expected_raan_rate_rad_s=expected_raan_rate_rad_s,
        raan_rate_relative_error=relative_error,
    )


def _set_equal_3d_axes(axis, positions: tuple[np.ndarray, ...]) -> None:
    combined = np.concatenate(positions, axis=0) / 1_000.0
    minimum = np.min(combined, axis=0)
    maximum = np.max(combined, axis=0)
    center = (minimum + maximum) / 2.0
    half_range = float(np.max(maximum - minimum) / 2.0)
    axis.set_xlim(center[0] - half_range, center[0] + half_range)
    axis.set_ylim(center[1] - half_range, center[1] + half_range)
    axis.set_zlim(center[2] - half_range, center[2] + half_range)


def save_comparison_plots(
    *,
    point_mass_times_s: np.ndarray,
    point_mass_positions_m: np.ndarray,
    point_mass_elements: np.ndarray,
    j2_times_s: np.ndarray,
    j2_positions_m: np.ndarray,
    j2_elements: np.ndarray,
    output_dir: Path,
) -> tuple[Path, Path]:
    """Save trajectory and orbital-element comparison plots using a headless backend."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    output_dir.mkdir(parents=True, exist_ok=True)
    orbit_path = output_dir / "orbit_comparison.png"
    elements_path = output_dir / "orbital_elements.png"

    orbit_figure = plt.figure(figsize=(8, 7))
    orbit_axis = orbit_figure.add_subplot(111, projection="3d")
    for label, positions_m in (
        ("Point mass", point_mass_positions_m),
        ("J2", j2_positions_m),
    ):
        positions_km = positions_m / 1_000.0
        orbit_axis.plot(*positions_km.T, label=label, linewidth=1.3)
        orbit_axis.scatter(*positions_km[0], s=24)
    orbit_axis.scatter(0, 0, 0, color="tab:blue", s=80, label="Earth")
    orbit_axis.set_xlabel("Inertial x [km]")
    orbit_axis.set_ylabel("Inertial y [km]")
    orbit_axis.set_zlabel("Inertial z [km]")
    orbit_axis.set_title("LEO trajectory: point mass vs J2")
    orbit_axis.legend()
    _set_equal_3d_axes(
        orbit_axis,
        (point_mass_positions_m, j2_positions_m),
    )
    orbit_figure.tight_layout()
    orbit_figure.savefig(orbit_path, dpi=160)
    plt.close(orbit_figure)

    element_figure, axes = plt.subplots(2, 2, figsize=(11, 7), sharex=True)
    series = (
        ("Point mass", point_mass_times_s, point_mass_elements),
        ("J2", j2_times_s, j2_elements),
    )
    for label, times_s, elements in series:
        time_hours = times_s / 3_600.0
        axes[0, 0].plot(time_hours, elements[:, 0] / 1_000.0, label=label)
        axes[0, 1].plot(time_hours, elements[:, 1], label=label)
        axes[1, 0].plot(time_hours, np.rad2deg(elements[:, 2]), label=label)
        axes[1, 1].plot(
            time_hours,
            np.rad2deg(np.unwrap(elements[:, 3])),
            label=label,
        )
    axes[0, 0].set_ylabel("Semi-major axis [km]")
    axes[0, 1].set_ylabel("Eccentricity [-]")
    axes[1, 0].set_ylabel("Inclination [deg]")
    axes[1, 1].set_ylabel("Unwrapped RAAN [deg]")
    axes[1, 0].set_xlabel("Time [h]")
    axes[1, 1].set_xlabel("Time [h]")
    axes[0, 0].legend()
    element_figure.suptitle("Osculating classical orbital elements")
    element_figure.tight_layout()
    element_figure.savefig(elements_path, dpi=160)
    plt.close(element_figure)

    return orbit_path, elements_path
