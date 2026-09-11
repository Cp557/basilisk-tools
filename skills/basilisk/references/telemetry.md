# Telemetry

Read this reference when adding recorders, exporting data, or diagnosing empty,
stale, mis-timed, or ambiguous telemetry.

## Record a message

Create the recorder from the producer message and add it to a task before
initialization:

```python
sample_ns = macros.sec2nano(sample_interval_s)
recorder = model.someOutMsg.recorder(sample_ns)
simulation.AddModelToTask(task_name, recorder)
```

- A zero/default recorder interval samples on each recorder task update.
- Choose a sampling interval that resolves the behavior being measured without
  embedding a large history in JSON output.
- Keep the producer and recorder schedule ordering deliberate. Confirm the
  connection and execution order with `bsk inspect` when instrumented.
- Convert `recorder.times()` from nanoseconds with `macros.NANO2SEC`.
- Read payload fields using the exact names in that message's documentation.

## Give data engineering meaning

For every exported column record its units, frame, time basis, and source
message or derivation. Do not infer these from a CSV header alone. Prefer CSV
for histories and compact JSON for configuration, metrics, checks, and artifact
paths.

At minimum, verify:

- at least two samples where a history is expected;
- finite numeric values;
- strictly increasing timestamps;
- consistent array lengths and shapes;
- agreement of the first sample with the configured initial state;
- a final timestamp consistent with duration and sampling policy.

Derived quantities such as classical orbital elements are not message payloads.
Label the source state, gravitational parameter, algorithm, units, and any
singularities or wrapping applied during derivation.

## Diagnose bad telemetry

1. Use `bsk inspect scenario.py --json` to confirm the recorder and its source
   message appear in `message_connections`.
2. Confirm the producer is added before initialization and runs at or before the
   required sample times.
3. Confirm the recorder is added to the intended task and its interval uses
   nanoseconds.
4. Read `stderr.log` and `stdout.log`, then inspect sample count, timestamps, and
   first/last records directly.
5. Rerun and verify the smallest invariant that previously failed.

## Sources

- [Basilisk messaging and Recorder API](https://avslab.github.io/basilisk/Documentation/architecture/messaging/messaging.html)
- [Basilisk basic orbit recorder example](https://avslab.github.io/basilisk/_modules/scenarioBasicOrbit.html)
