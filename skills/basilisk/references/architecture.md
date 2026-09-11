# Basilisk Architecture

Read this reference when creating or inspecting simulation structure or message
connections.

## Mental model

```text
SimBaseClass
└── process
    └── task (period and priority)
        └── model/module (priority and execution order)
            ├── input message readers
            └── output messages
```

- A process groups scheduled tasks.
- A task calls its models at a fixed period. Convert seconds with
  `macros.sec2nano()` rather than hand-writing nanosecond constants.
- Higher explicit priorities execute before lower priorities. When priorities
  are equal or left at `-1`, preserve a deliberate creation/addition order and
  confirm it through inspection.
- Modules exchange typed messages. Connect a consumer input with
  `consumer.someInMsg.subscribeTo(producer.someOutMsg)` using the pattern shown
  by the module documentation or an official example.
- Add all models, connect messages, set initial state, and attach recorders
  before calling `InitializeSimulation()`.

## Inspect structure

For an instrumented scenario:

```bash
bsk inspect scenario.py --json
```

The report derives processes, tasks, modules, execution order, connections, and
unlinked inputs from Basilisk's `SimBaseClass.GetMessageConnectionGraph`.
Telemetry units and frames come from the scenario contract because runtime
objects do not establish those engineering meanings reliably.

An unlinked input is a diagnostic, not automatically an error. Some module
inputs are optional or use internal/default state. Check the module's official
documentation before connecting it.

If inspection reports `supported: false`, the file is a standard scenario. Run
it normally, inspect source and official documentation, and state that deep
runtime inspection is unavailable.

## Sources

- [Basilisk process and task creation](https://avslab.github.io/basilisk/Learn/bskPrinciples/bskPrinciples-1.html)
- [Adding Basilisk modules](https://avslab.github.io/basilisk/Learn/bskPrinciples/bskPrinciples-2.html)
- [SimulationBaseClass API](https://avslab.github.io/basilisk/Documentation/utilities/SimulationBaseClass.html)
