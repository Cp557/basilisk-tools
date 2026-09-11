"""Orbit scenario containing a recorder scheduling defect."""

import csv
from pathlib import Path

import numpy as np
from Basilisk.simulation import spacecraft
from Basilisk.utilities import (
    SimulationBaseClass,
    macros,
    orbitalMotion,
    simIncludeGravBody,
)

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
DURATION_S = 1_200.0
TIME_STEP_S = 10.0
SAMPLE_INTERVAL_S = 60.0


def _write_telemetry(
    path: Path,
    times_s: np.ndarray,
    positions_m: np.ndarray,
    velocities_m_s: np.ndarray,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as telemetry_file:
        writer = csv.writer(telemetry_file)
        writer.writerow(TELEMETRY_COLUMNS)
        for time_s, position_m, velocity_m_s in zip(
            times_s, positions_m, velocities_m_s, strict=True
        ):
            writer.writerow((time_s, *position_m, *velocity_m_s))


def main() -> int:
    simulation = SimulationBaseClass.SimBaseClass()
    process = simulation.CreateNewProcess("dynamicsProcess")
    task_name = "dynamicsTask"
    process.addTask(simulation.CreateNewTask(task_name, macros.sec2nano(TIME_STEP_S)))

    vehicle = spacecraft.Spacecraft()
    vehicle.ModelTag = "evaluationSpacecraft"
    simulation.AddModelToTask(task_name, vehicle)

    gravity_factory = simIncludeGravBody.gravBodyFactory()
    earth = gravity_factory.createEarth()
    earth.isCentralBody = True
    gravity_factory.addBodiesTo(vehicle)

    elements = orbitalMotion.ClassicElements()
    elements.a = 7_000_000.0
    elements.e = 0.01
    elements.i = np.deg2rad(55.0)
    elements.Omega = np.deg2rad(40.0)
    elements.omega = np.deg2rad(30.0)
    elements.f = 0.0
    position_m, velocity_m_s = orbitalMotion.elem2rv(earth.mu, elements)
    vehicle.hub.r_CN_NInit = position_m
    vehicle.hub.v_CN_NInit = velocity_m_s

    recorder = vehicle.scStateOutMsg.recorder(macros.sec2nano(SAMPLE_INTERVAL_S))
    # BUG: the recorder is never scheduled on the task.
    simulation.InitializeSimulation()
    simulation.ConfigureStopTime(macros.sec2nano(DURATION_S))
    simulation.ExecuteSimulation()

    output_directory = registered_output_directory(OUTPUT_DIRECTORY)
    telemetry_path = output_directory / "telemetry.csv"
    _write_telemetry(
        telemetry_path,
        np.asarray(recorder.times(), dtype=float) * macros.NANO2SEC,
        np.asarray(recorder.r_BN_N, dtype=float),
        np.asarray(recorder.v_BN_N, dtype=float),
    )
    register_artifacts({"telemetry": str(telemetry_path.resolve())})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
