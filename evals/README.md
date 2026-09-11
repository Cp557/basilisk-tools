# Agent Evaluations

These four cases measure whether a coding agent can create or repair a small
Basilisk orbit scenario and support its answer with deterministic evidence.
They are a limited project evaluation, not a general benchmark of an agent or
of spacecraft-simulation quality.

## Cases

| Case | Task | Independent evidence |
| --- | --- | --- |
| `two_body` | Create point-mass orbit propagation | Initial orbit, valid telemetry, two-body invariants |
| `add_j2` | Add degree-2 Earth gravity | Secular RAAN rate and angular-momentum-z behavior |
| `fix_units` | Repair 7,000 km interpreted as meters | Physical perigee and recovered semi-major axis |
| `fix_telemetry` | Repair an unscheduled recorder | Recorded, finite, ordered state history |

Every case contains `prompt.md`, `starting_files/`, `expected.toml`, and an
executable `verify.py`. The external verifier runs the submitted scenario with
`bsk run` and derives checks from its registered state telemetry. It does not
trust checks or metrics written by the submission.

## Controlled protocol

Use the same repository revision, model, settings, environment, prompt, and
time limit for both conditions. Prepare workspaces outside this repository so a
baseline agent cannot discover `skills/basilisk/` while searching nearby files.

1. Prepare a fresh workspace:

   ```bash
   uv run python -m evals.run prepare fix_units /tmp/fix-units-baseline
   ```

2. For `baseline`, expose Basilisk and `bsk` but no Basilisk skill. For `skill`,
   install the canonical skill using `docs/skill-installation.md`. Give the
   agent only the case prompt and workspace.
3. Start timing when the prompt is sent. Save the final response and any
   reliably reported token counts. Count failed simulation launches and human
   interventions using the same rule in every run.
4. Score the untouched workspace:

   ```bash
   uv run python -m evals.run score fix_units /tmp/fix-units-baseline \
     --agent codex --condition baseline --task-seconds 180 \
     --failed-attempts 1 --human-interventions 0 \
     --explanation-score 2 --response /tmp/agent-response.md
   ```

The scorer stores a source snapshot, raw CLI output, scenario logs, telemetry,
independent checks, `explanation.md`, the optional agent response, and experiment
metadata under `evals/results/<run-id>/`. Commit the complete selected runs used
for published comparisons.

## Scoring

`automated_pass` is true only when every external check passes. Separately,
score the final technical explanation:

- `0`: missing or materially incorrect;
- `1`: mostly correct but missing evidence, conventions, or an important limit;
- `2`: correct, evidence-based, and explicit about units, frames, and limits.

Do not infer missing timing, intervention, or token data. Leave optional command
arguments absent so the result records `null`. Report completion rate, failures,
interventions, elapsed time, and explanation scores per condition; do not claim
statistical significance from this four-case convenience sample.

Run a verifier directly when debugging the harness:

```bash
uv run python -m evals.fix_units.verify /tmp/submission --output-dir /tmp/check
```
