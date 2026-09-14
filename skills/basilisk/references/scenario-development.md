# Scenario Development

## Develop from a known-good pattern

1. Run `bsk doctor --json` and note the Basilisk version.
2. Find the nearest official example for the requested dynamics, environment,
   or flight-software behavior.
3. Preserve its process/task/module/message pattern while changing only the
   configuration relevant to the task.
4. Put configuration in explicit values or a small dataclass. Include units in
   names where practical and document frames separately.
5. Keep `prepare()` or equivalent configuration separate from `run()` when the
   scenario needs pre-execution inspection.
6. Attach recorders before initialization, execute for a justified duration,
   then calculate metrics and write artifacts.
7. Protect direct execution with `if __name__ == "__main__"` so importing an
   instrumented scenario does not start the simulation.

## Minimal lifecycle

```python
simulation = SimulationBaseClass.SimBaseClass()
process = simulation.CreateNewProcess("dynamicsProcess")
task = simulation.CreateNewTask("dynamicsTask", macros.sec2nano(time_step_s))
process.addTask(task)

model = some_module.SomeModel()
model.ModelTag = "descriptiveModel"
simulation.AddModelToTask("dynamicsTask", model)

# Configure state, connect messages, and add recorders here.

simulation.InitializeSimulation()
simulation.ConfigureStopTime(macros.sec2nano(duration_s))
simulation.ExecuteSimulation()
```

Use the real class, field, and message names from the installed release's
documentation. Do not treat this lifecycle sketch as an API catalog.

## Optional Basilisk Tools contract

Instrument only scenarios that benefit from structured inspection and semantic
verification. Define a top-level `basilisk_tools_scenario()` returning:

```python
InstrumentedScenario(
    name="scenario_name",
    description="What the scenario demonstrates.",
    build_cases=build_cases,  # configures but does not execute
    verify=verify,  # writes artifacts and returns VerificationReport
)
```

Each `ScenarioCase` contains a configured `SimBaseClass`, explicit
`TelemetrySpec` values, and concise metadata. Each `VerificationCheck` records
its actual value, expected value, tolerance, and units. Use
`registered_output_directory()` and `register_artifacts()` so normal `bsk run`
executions preserve generated files.

Inspection reports configured structure and explicitly declared metadata. It
does not recover orbital elements or other numeric inputs unless the scenario
exposes them through the contract; use telemetry and declared checks for that
evidence.

See `examples/orbit_propagation/scenario.py` for the maintained contract rather
than copying a second template into the skill.

## Sources

- [Basilisk examples index](https://avslab.github.io/basilisk/examples/index.html)
- [Learning Basilisk](https://avslab.github.io/basilisk/Learn.html)
