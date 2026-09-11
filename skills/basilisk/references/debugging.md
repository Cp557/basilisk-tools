# Debugging Basilisk Scenarios

Read this reference after a failed launch, incorrect result, broken connection,
or telemetry problem.

## Evidence-first loop

```bash
bsk doctor --json
bsk inspect scenario.py --json
bsk run scenario.py --json
bsk verify scenario.py --json
```

Run only the commands relevant to the failure. Use paths returned in JSON to
read `stderr.log`, `stdout.log`, metadata, telemetry, and verification artifacts.
Change one causal issue at a time and rerun the narrowest failing check.

## Classify before editing

- Environment/import failure: compare Python, Basilisk, and Basilisk Tools
  versions in `doctor` and run metadata.
- Python/API failure: use the final traceback frames and confirm the exact API
  against documentation for the installed Basilisk version.
- Structure/message failure: inspect process, task, module, priority, and
  connection records. An unlinked input can be optional; check its module docs.
- Time/scheduling failure: trace seconds-to-nanoseconds conversion, task period,
  model order, recorder interval, stop time, and first/last sample times.
- Units/frame failure: trace every input and transformation from its source;
  check meters/kilometers, radians/degrees, body/inertial frames, and origin.
- Physics-configuration failure: confirm central body, gravity field, effectors,
  initial state, and that an acceleration is not included twice.
- Numerical/verification failure: inspect the actual value and tolerance before
  changing the integrator or loosening the threshold.

## Common traps

- `macros.sec2nano()` omitted or applied twice.
- Orbital angles supplied in degrees where radians are required.
- Kilometers assigned to a spacecraft state that expects meters.
- A module created but never added to the scheduled task.
- A message reader never subscribed to its producer.
- A recorder added after initialization or sampled on an unsuitable schedule.
- Wrapped angles fitted directly, creating a false discontinuity.
- A two-body conservation formula used as if it included perturbation
  potentials.
- A tolerance widened to hide a configuration error.

If a standard scenario is not instrumented, `inspect` or `verify` returning exit
code 2 is expected. Do not rewrite the scenario solely to silence that status;
instrument it only when the requested workflow benefits from structured
evidence.
