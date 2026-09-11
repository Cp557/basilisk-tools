# Basilisk Tools Technical Reference

## Purpose

Basilisk Tools makes AVS Basilisk easier for AI coding agents to operate reliably. It combines a portable domain skill with a small deterministic CLI. Basilisk remains the source of truth for simulation behavior and numerical results.

The v1 reference workflow is orbit propagation with point-mass and J2 gravity.

## Core Boundary

- The skill teaches agents how to create, modify, analyze, and debug Basilisk scenarios.
- The CLI reports deterministic environment, runtime, structure, and verification data.
- The project does not replace the Basilisk Python API or wrap individual Basilisk modules with CLI commands.
- Scenarios are trusted local Python code and always run in a child process.

## Package Names

- Distribution: `basilisk-tools`
- Python package: `basilisk_tools`
- CLI executable: `bsk`
- Basilisk dependency distribution: `bsk`

Keep the project distribution and import names distinct from the upstream `bsk` package.

## Current Implementation

Steps 1 through 6 are complete. Step 7's reproducible evaluation suite and Step
8's release documentation, generated visuals, and CI build check are
implemented. The MIT license and GitHub target are set. Controlled agent
comparisons, the first pushed CI run, and final public review remain.

The initial structured models live in `basilisk_tools.results`:

- `RunStatus`: `success`, `failure`, `timeout`, or `interrupted`.
- `RunMetadata`: scenario identity and runtime/tool versions.
- `RunResult`: process outcome, elapsed time, artifacts, and optional error.
- `ErrorSummary`: concise error type and message.

Every serialized model contains `schema_version: 1`.

## Reference Orbit Scenario

`examples/orbit_propagation/scenario.py` propagates the same spacecraft with
Basilisk 2.11.1 point-mass and J2 Earth gravity. Run both cases directly:

```bash
uv run python examples/orbit_propagation/scenario.py
```

The default orbit and simulation configuration is:

- Semi-major axis: 7,000,000 m.
- Eccentricity: 0.01.
- Inclination: 55 degrees.
- RAAN: 40 degrees.
- Argument of periapsis: 30 degrees.
- True anomaly: 0 degrees.
- Duration: 18,000 s; integration step: 10 s; sampling interval: 60 s.

Position and velocity use an Earth-centered inertial N frame and SI units. The
model excludes drag, third bodies, and radiation pressure. The J2 case uses only
Basilisk's versioned `GGM03S-J2-only.txt` degree-2 zonal model. Basilisk fetches
this official support file on first use.

Direct-run outputs default to `.bsk/examples/orbit_propagation/`:

- `point-mass/` and `j2/`: telemetry CSV and versioned verification JSON.
- `comparison.json`: metrics and concise interpretation boundaries.
- `orbit_comparison.png`: inertial trajectories for both models.
- `orbital_elements.png`: semi-major axis, eccentricity, inclination, and RAAN.

Checks require finite telemetry, strictly increasing time, and agreement between
the configured and recorded initial state and classical elements. State-vector
tolerances are 1 mm and 1 micrometer/second; semi-major axis tolerance is 1 m;
dimensionless and angular element tolerances are `1e-8`, except the initial
true-anomaly tolerance is `5e-8 rad`. Converting an exact zero anomaly from
state vectors can produce a platform-dependent round-off of about `1.5e-8 rad`.

Analysis calculates Keplerian specific energy, specific angular-momentum
magnitude and z-component, unwrapped RAAN change, and a least-squares RAAN rate.
Keplerian energy omits the J2 potential and is therefore a conservation check
only for point-mass gravity. For J2, compare the fitted RAAN rate with first-order
secular theory and check conservation of inertial angular momentum's z-component.

Reference tolerances at the default 10 s integration step are:

- Point-mass relative energy drift: `1e-8` maximum.
- Point-mass relative angular-momentum drift: `5e-9` maximum.
- Point-mass absolute RAAN rate: `1e-12 rad/s` maximum.
- J2 RAAN-rate relative error against first-order theory: 2% maximum.
- J2 relative angular-momentum z drift: `5e-9` maximum.

The calibrated Basilisk 2.11.1 run produced about `8e-11` point-mass energy
drift, `4e-11` angular-momentum drift, and 0.12% J2 RAAN-rate error. These limits
leave substantial numerical/platform margin while still detecting incorrect
gravity setup or degraded integration. They apply to the documented reference
configuration, not arbitrary orbit or integrator settings.

## v1 Commands

```bash
bsk doctor
bsk run <scenario.py>
bsk inspect <scenario.py>
bsk verify <scenario-or-run>
```

Commands should provide concise human output and machine-readable JSON where applicable. Scenario stdout and stderr must never corrupt JSON command output.

All v1 commands are implemented:

```bash
bsk doctor [--json]
bsk run <scenario.py> [--timeout 300] [--runs-dir .bsk/runs] [--json]
bsk inspect <scenario.py> [--timeout 30] [--json]
bsk verify <scenario-or-run> [--timeout 300] [--json]
```

`bsk doctor` reports Python and executable paths, the supported Basilisk and
Basilisk Tools versions, required runtime dependencies, optional development
dependencies, and actionable errors. Its JSON document includes `ok` and
`schema_version` fields; an unhealthy environment exits with code 1.

`bsk run` resolves and hashes a trusted Python file, then executes it through
`basilisk_tools.worker` using the current Python interpreter. Script globals,
the scenario-directory import path, and the caller's working directory match
normal script execution. Scenario output goes only to run logs. The parent and
worker exchange a private structured outcome file, which is removed after the
public result is written.

Successful runs exit 0, ordinary failures preserve a positive scenario exit
code when available, timeouts exit 124, and user interruptions exit 130. The
parent sends graceful termination to the child process group and escalates to a
forced stop after two seconds if needed.

`bsk inspect` statically checks for the optional contract before importing the
scenario in a child process. For each declared case it reports processes,
tasks, modules, execution order, message connections, and unlinked inputs from
Basilisk 2.11.1's `SimBaseClass.GetMessageConnectionGraph`. Telemetry names,
fields, units, sampling, and frames are explicitly declared by the scenario and
identified as such; the CLI does not infer them.

`bsk verify` runs a scenario's declared verification callback in a child
process or reads a saved `verification.json`. It also accepts a `bsk run`
directory or `result.json` when that run registered a `verification` artifact.
New verification executions are stored under `.bsk/verifications/<id>/` with
logs, the normalized report, and scenario-generated artifacts. Checks contain
name, status, actual value, expected value, tolerance, and units.

For `inspect` and `verify`, exit 0 means the requested result passed, 1 means a
tool or scenario error, 2 means the target does not support the optional
contract, and 3 means declared verification checks failed.

## Scenario Support

### Standard scenario

Any trusted Python file can be executed by `bsk run`. Process-level metadata and logs are available. Deep inspection, telemetry discovery, and semantic verification are not guaranteed.

### Instrumented scenario

An instrumented file defines a top-level `basilisk_tools_scenario()` factory
that returns `InstrumentedScenario` with four fields:

- `name` and `description`.
- `build_cases()`, returning one or more `ScenarioCase` values with a configured
  Basilisk simulation, explicit telemetry metadata, and concise case metadata.
- `verify(output_dir)`, returning a `VerificationReport` with declared checks,
  metrics, and generated artifact paths.

The contract types live in `basilisk_tools.instrumentation`. Building a case
must configure but not initialize or execute the simulation. The CLI loads the
contract only inside a child process. A standard scenario without the factory
is reported as unsupported without being imported. Keep this as a data-and-
callback boundary, not a plugin lifecycle.

## Process Model

```text
bsk CLI
   ↓
basilisk_tools worker or tool_worker subprocess
   ↓
Basilisk scenario
   ↓
versioned JSON + logs + CSV + artifacts
```

Use a dedicated private file for worker-to-parent structured results. Do not use
child stdout as the structured transport because scenarios may print arbitrary
output. The worker runs the scenario with `runpy` under `__main__` and records a
concise exception type and message; the full traceback remains in `stderr.log`.

## Run Artifacts

Default location:

```text
.bsk/runs/<run-id>/
├── result.json
├── metadata.json
├── stdout.log
├── stderr.log
└── artifacts/
    ├── verification.json
    └── optional telemetry, plots, and other registered outputs
```

`result.json`, `metadata.json`, `stdout.log`, `stderr.log`, and an `artifacts/`
directory are created for every completed launch attempt. Artifact contents are
optional.

JSON artifacts must contain `schema_version: 1`. Large telemetry is referenced by path rather than embedded in CLI output.

Artifact paths in `result.json` are absolute so callers can locate them
unambiguously. The default timeout is 300 seconds and can be changed per run.
Instrumented scenarios can use `registered_output_directory()` and
`register_artifacts()` from `basilisk_tools.artifacts`; this lets `bsk run`
redirect outputs into the run directory and add named paths to `result.json`.

Record at least:

- Run ID and status.
- Scenario path and SHA-256 hash.
- Start time and elapsed duration.
- Exit code.
- Python, Basilisk, and Basilisk Tools versions.
- Artifact paths.
- Structured error summary when applicable.

Statuses should distinguish success, failure, timeout, and interruption. Do not capture the full process environment because it may contain secrets.

## Technical Stack

- Python 3.11 initial target, selected locally by `.python-version`.
- `pyproject.toml` and `uv` with a committed lockfile.
- Typer and Rich for the CLI.
- Standard-library subprocess and JSON handling.
- Dataclasses and enums for result models.
- AVS Basilisk 2.11.1, NumPy, and Matplotlib.
- CSV for v1 telemetry exchange.
- pytest and pytest-cov for tests.
- Ruff for formatting and linting.
- GitHub Actions for CI.
- Markdown and Mermaid for documentation.

Do not add Node, a web service, database, container platform, LLM SDK, or agent orchestration framework in v1.

## Skill Layout

```text
skills/basilisk/
├── SKILL.md
└── references/
    ├── architecture.md
    ├── scenario-development.md
    ├── orbit-propagation.md
    ├── telemetry.md
    ├── verification.md
    └── debugging.md
```

`skills/basilisk/` is the single canonical skill source. `SKILL.md` uses the
open Agent Skills format and routes architecture, scenario development, orbit
propagation, telemetry, verification, and debugging tasks to concise references.

Codex discovers a repository link or copy under `.agents/skills/basilisk`;
Claude Code uses `.claude/skills/basilisk`. Both support explicit and implicit
invocation. See `docs/skill-installation.md`; validate changes with the Agent
Skills quick validator and `tests/test_skill.py`.

## Agent Evaluation Cases

The v1 evaluation set covers:

1. Creating two-body orbit propagation.
2. Adding J2 and explaining its effect.
3. Repairing a kilometer-versus-meter error.
4. Repairing missing or incorrect telemetry.

Each fixture contains a prompt, starting files, TOML expectations, and a
deterministic Python verifier. `evals.run prepare` creates a fresh workspace;
`evals.run score` runs its scenario through `bsk run` and records raw output,
telemetry, independent checks, agent metadata, and an optional final response.

Verifiers calculate physics checks from the registered state telemetry and do
not trust candidate-authored metrics. Run baseline workspaces without skill
discovery and skill-assisted workspaces with the canonical skill, holding the
agent, settings, prompt, environment, and time limit fixed. Human-score the
technical explanation from 0 through 2. Preserve raw outcomes and describe the
four-case comparison as a limited study rather than a general benchmark. See
`evals/README.md` for the controlled protocol.

## Portfolio Documentation

- `README.md` is the public project overview and quick start.
- `docs/architecture.md` documents boundaries, components, and process flow.
- `docs/orbit-results.md` presents the checked reference metrics and plots.
- `docs/demo.md` is the reproducible live-demonstration script.
- `docs/example-output.md` contains shortened structured-output examples.
- `docs/release-checklist.md` lists the external publication gates.
- `docs/vizard.md` documents optional offline 3D playback.
- `docs/render_demo.py` reproducibly generates `docs/assets/demo.gif`.

The checked-in result visuals come from the maintained reference scenario.
Regenerate them when the scenario or calibrated metrics change. Do not present
harness calibration as comparative agent evidence.

## Vizard Integration

`examples/orbit_propagation/vizard.py` is a `bsk run`-compatible entry point
that records both reference cases through Basilisk's `vizSupport`. It registers
`point_mass_vizard` and `j2_vizard` `.bin` playback artifacts alongside the
normal telemetry, checks, plots, and comparison JSON. The main scenario also
accepts `--vizard` for direct execution.

Vizard is a separately installed Unity desktop application and is not required
for simulation, tests, CI, or numerical verification. V1 supports deterministic
offline playback files only; live streaming and two-way communication remain
future work.

## Development Rules

- Prefer small functions, explicit data flow, and standard-library functionality.
- Keep human presentation separate from structured result generation.
- Make units, coordinate frames, assumptions, and tolerances explicit.
- Obtain numerical facts from Basilisk or deterministic analysis, never from an agent guess.
- Reuse Basilisk runtime inspection APIs where available.
- Report unsupported inspection or verification honestly.
- Update this reference when technical contracts or architecture change.
- Run `npm run build` for larger repository changes if an npm build is introduced. Do not run `npm run dev`.

## v1 Non-Goals

- Per-module CLI wrappers.
- Automatic telemetry or unit inference.
- Exhaustive validation of arbitrary scenarios.
- Plot, compare, sweep, GUI, cloud, and distributed execution commands.
- A universal solver abstraction or plugin ecosystem.
- Broad operating-system and Basilisk-version compatibility guarantees.

See [PLAN.md](PLAN.md) for milestones, acceptance criteria, risks, and future direction.
