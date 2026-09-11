---
name: basilisk
description: Build, inspect, run, verify, and debug AVS Basilisk spacecraft simulation scenarios. Use when working with Basilisk Python simulations, processes, tasks, modules, messages, telemetry, orbital dynamics, numerical checks, or Basilisk Tools CLI output.
---

# Basilisk

Develop technically credible Basilisk scenarios and ground conclusions in
runtime evidence. Keep the requested fidelity and scope; add environmental
effects or abstractions only when they support the user's objective.

## Route the task

Read only the references needed for the current work:

- Read [architecture.md](references/architecture.md) to configure or inspect
  processes, tasks, modules, priorities, and messages.
- Read [scenario-development.md](references/scenario-development.md) to create
  or modify a scenario and optionally instrument it for Basilisk Tools.
- Read [orbit-propagation.md](references/orbit-propagation.md) for orbital
  initial conditions, gravity models, elements, and perturbation analysis.
- Read [telemetry.md](references/telemetry.md) when recording, exporting, or
  diagnosing simulation data.
- Read [verification.md](references/verification.md) when defining tolerances,
  interpreting results, or making correctness claims.
- Read [debugging.md](references/debugging.md) after a failed run, incorrect
  result, missing message connection, or empty/stale telemetry history.

## Ground the implementation

1. Identify the installed Basilisk version. Prefer documentation and examples
   for that release over recollection or development-branch APIs.
2. Search the official examples for the closest working scenario and adapt its
   module and message pattern. Use existing Basilisk physics modules instead of
   reimplementing their equations in the scenario.
3. State units, reference frames, central bodies, time conventions, model
   assumptions, and excluded effects near the configuration or output.
4. Separate scenario configuration from execution when inspection is needed.
   Connect messages and attach recorders before initialization.
5. Use deterministic evidence to finish the task:

```bash
bsk doctor --json
bsk inspect path/to/scenario.py --json
bsk run path/to/scenario.py --json
bsk verify path/to/scenario.py --json
```

`inspect` and `verify` require the optional instrumented-scenario contract. If
the CLI reports exit code 2 or `supported: false`, describe that limitation and
continue with process-level run evidence; do not invent structure or semantic
checks.

## Interpret evidence

- Read `result.json`, `metadata.json`, and the referenced logs and artifacts.
  Scenario text output is in logs, not JSON command output.
- Treat a successful process exit as evidence that Python execution completed,
  not that the physics is correct.
- Make numerical claims only from declared checks, recorded telemetry, or a
  documented calculation. Distinguish physical variation from integration
  error and state where each tolerance comes from.
- Verify finite data, monotonic time, expected shape, initial conditions, and
  domain invariants appropriate to the model.
- Rerun the narrowest relevant command after each correction. Report the model,
  configuration, evidence, and remaining limitations with the conclusion.

## Preserve key boundaries

- Basilisk is the simulation source of truth; Basilisk Tools supplies
  deterministic operation and evidence.
- Never infer coordinate frames or units from a variable name alone.
- Do not claim automatic semantic verification for arbitrary Python scenarios.
- Treat scenarios as trusted local code because CLI commands execute them.
- Keep exploratory plots separate from deterministic pass/fail checks.
