---
name: basilisk
description: Build, inspect, run, verify, and debug AVS Basilisk spacecraft simulations. Use for Basilisk scenarios, architecture, messages, telemetry, orbital dynamics, or Basilisk Tools CLI output.
---

# Basilisk

Develop Basilisk scenarios and support conclusions with runtime evidence. Keep
the model fidelity and scope requested by the user.

## References

Read only what the task needs:

- [architecture.md](references/architecture.md): processes, tasks, modules,
  priorities, and messages
- [scenario-development.md](references/scenario-development.md): creating or
  instrumenting a scenario
- [orbit-propagation.md](references/orbit-propagation.md): initial conditions,
  gravity, elements, and perturbations
- [telemetry.md](references/telemetry.md): recording, exporting, and diagnosing
  simulation data
- [verification.md](references/verification.md): checks, tolerances, and claims
- [debugging.md](references/debugging.md): failed runs, connections, and bad
  telemetry

## Workflow

1. Identify the installed Basilisk version and use documentation for that
   release.
2. Adapt the closest official example. Prefer Basilisk modules to equations
   reimplemented in scenario code.
3. Make units, frames, central bodies, time conventions, assumptions, and
   excluded effects explicit.
4. Connect messages and attach recorders before initialization. Separate
   configuration from execution when inspection is needed.
5. Gather the narrowest relevant evidence:

```bash
bsk doctor --json
bsk inspect path/to/scenario.py --json
bsk run path/to/scenario.py --json
bsk verify path/to/scenario.py --json
```

6. After a correction, rerun the failed command and report the configuration,
   evidence, and remaining limitations.

`inspect` and `verify` require the optional instrumented-scenario contract. If
they exit 2 or report `supported: false`, continue with source review and
process-level run evidence. Do not invent unavailable structure or checks.

## Evidence rules

- A successful process exit proves execution, not physical correctness.
- Read scenario output from the returned logs and artifacts, not CLI JSON.
- Base numerical claims on declared checks, recorded telemetry, or documented
  calculations with justified tolerances.
- Check finite data, monotonic time, shape, initial conditions, and model-specific
  invariants.
- Never infer units or coordinate frames from variable names alone.
- Treat scenarios as trusted local code because CLI commands execute them.
- Keep exploratory plots separate from pass/fail checks.
