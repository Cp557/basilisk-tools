"""Small instrumented Basilisk scenario for CLI tests."""

from pathlib import Path

from Basilisk.simulation import spacecraft
from Basilisk.utilities import SimulationBaseClass, macros

from basilisk_tools.instrumentation import (
    InstrumentedScenario,
    ScenarioCase,
    TelemetrySpec,
    VerificationCheck,
    VerificationReport,
)


def build_cases() -> tuple[ScenarioCase, ...]:
    simulation = SimulationBaseClass.SimBaseClass()
    process = simulation.CreateNewProcess("testProcess")
    task = simulation.CreateNewTask("testTask", macros.sec2nano(1.0))
    process.addTask(task)
    model = spacecraft.Spacecraft()
    model.ModelTag = "testSpacecraft"
    simulation.AddModelToTask("testTask", model)
    recorder = model.scStateOutMsg.recorder(macros.sec2nano(2.0))
    simulation.AddModelToTask("testTask", recorder)
    telemetry = TelemetrySpec(
        name="state",
        source_message="testSpacecraft.scStateOutMsg",
        fields=("r_BN_N", "v_BN_N"),
        units={"position": "m", "velocity": "m/s"},
        sample_interval_s=2.0,
        frame="inertial N",
    )
    return (
        ScenarioCase(
            name="test-case",
            simulation=simulation,
            telemetry=(telemetry,),
            metadata={"purpose": "test"},
        ),
    )


def verify(output_dir: Path) -> VerificationReport:
    output_dir.mkdir(parents=True, exist_ok=True)
    evidence = output_dir / "evidence.txt"
    evidence.write_text("deterministic evidence\n", encoding="utf-8")
    return VerificationReport(
        scenario="instrumented_test",
        passed=True,
        checks=(
            VerificationCheck(
                name="known_value",
                passed=True,
                actual=42.0,
                expected=42.0,
                tolerance=0.0,
                units=None,
            ),
        ),
        metrics={"answer": 42.0},
        artifacts={"evidence": str(evidence.resolve())},
    )


def basilisk_tools_scenario() -> InstrumentedScenario:
    print("instrumented scenario loaded")
    return InstrumentedScenario(
        name="instrumented_test",
        description="A minimal contract fixture.",
        build_cases=build_cases,
        verify=verify,
    )
