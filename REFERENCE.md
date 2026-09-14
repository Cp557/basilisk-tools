# Basilisk Tools Technical Reference

This file records the contracts and invariants a coding agent needs to change
the repository safely. Public usage belongs in `README.md` and `docs/`.

## Product boundary

- The skill teaches Basilisk workflows and engineering checks.
- The CLI provides environment, execution, structure, and verification data.
- Basilisk remains the source of simulation behavior and numerical results.
- The project does not wrap individual Basilisk modules.
- Scenario files are trusted local Python executed in child processes.

## Names and versions

- Distribution: `basilisk-tools`
- Import package: `basilisk_tools`
- CLI: `bsk`
- Upstream Basilisk distribution: `bsk==2.11.1`
- Python target: 3.11 or newer
- JSON schema: `schema_version: 1`

Keep the project names distinct from the upstream `bsk` package.

## CLI contracts

```bash
bsk doctor [--json]
bsk run <scenario.py> [--timeout 300] [--runs-dir .bsk/runs] [--json]
bsk inspect <scenario.py> [--timeout 30] [--json]
bsk verify <scenario-or-run> [--timeout 300] [--json]
```

Human output and JSON are two presentations of the same result. Scenario stdout
and stderr belong in log files, never in CLI JSON.

### `doctor`

Reports Python, Basilisk, Basilisk Tools, runtime dependencies, development
dependencies, and actionable errors. An unhealthy environment exits 1.

### `run`

Resolves and hashes a Python file, then launches it with the current interpreter
through `basilisk_tools.worker`. The worker uses normal script globals and adds
the scenario directory to the import path. The caller's working directory is
preserved.

The parent captures logs, reads a private worker outcome, registers scenario
artifacts, and writes the public result. It stops the child process group on a
timeout or interruption.

Exit codes:

- 0: success
- positive scenario code or 1: failure
- 124: timeout
- 130: interruption

### `inspect`

Accepts a scenario that declares `basilisk_tools_scenario()`. A child process
loads each configured case and reads processes, tasks, modules, execution order,
connections, and unlinked inputs from
`SimBaseClass.GetMessageConnectionGraph`. Telemetry units and frames come from
the scenario contract; they are not inferred.

### `verify`

Runs an instrumented scenario's verification callback in a child process, or
loads a saved `verification.json`. It also accepts a run directory or
`result.json` that registers a `verification` artifact.

For `inspect` and `verify`, exit 0 means success, 1 means tool or scenario error,
2 means unsupported, and 3 means one or more checks failed.

## Result models

`basilisk_tools.results` defines:

- `RunStatus`: `success`, `failure`, `timeout`, or `interrupted`
- `RunMetadata`: scenario hash, start time, and runtime versions
- `RunResult`: status, elapsed time, exit code, artifacts, and optional error
- `ErrorSummary`: error type and message

Every serialized result contains `schema_version: 1`.

## Scenario support

Any trusted Python file can run through `bsk run`. Deep inspection and semantic
verification require an instrumented scenario.

An instrumented file exports `basilisk_tools_scenario()`, which returns:

```python
InstrumentedScenario(
    name="scenario_name",
    description="What the scenario demonstrates.",
    build_cases=build_cases,
    verify=verify,
)
```

`build_cases()` returns configured but uninitialized `ScenarioCase` objects.
Each case contains a Basilisk simulation, explicit `TelemetrySpec` values, and
metadata. `verify(output_dir)` returns a `VerificationReport` containing checks,
metrics, and artifact paths.

Contract types live in `basilisk_tools.instrumentation`. Keep this boundary
limited to data and callbacks required by the reference scenario.

## Artifacts

Runs default to:

```text
.bsk/runs/<run-id>/
├── result.json
├── metadata.json
├── stdout.log
├── stderr.log
└── artifacts/
```

Every launch creates the four top-level files and artifact directory. Scenario
artifacts are optional. Paths in `result.json` are absolute; large telemetry is
referenced rather than embedded.

Instrumented scenarios use `registered_output_directory()` and
`register_artifacts()` from `basilisk_tools.artifacts` to write into an active
run. Do not record the complete process environment because it may contain
secrets.

## Reference orbit scenario

`examples/orbit_propagation/scenario.py` propagates the same spacecraft with
point-mass and degree-2 J2 Earth gravity.

Default configuration:

| Quantity | Value |
| --- | ---: |
| Semi-major axis | 7,000,000 m |
| Eccentricity | 0.01 |
| Inclination | 55 degrees |
| RAAN | 40 degrees |
| Argument of periapsis | 30 degrees |
| True anomaly | 0 degrees |
| Duration | 18,000 s |
| Integration step | 10 s |
| Sample interval | 60 s |

Position and velocity use SI units in the Earth-centered inertial N frame. The
model excludes drag, third-body gravity, and radiation pressure. J2 uses
Basilisk's versioned `GGM03S-J2-only.txt` support file at degree 2.

The scenario checks:

- finite, ordered telemetry and recorded initial state;
- initial classical elements;
- point-mass Keplerian-energy, angular-momentum, and RAAN drift;
- J2 RAAN rate against first-order secular theory;
- J2 inertial angular-momentum-z drift.

Keplerian energy omits the J2 potential, so it is not a J2 conservation check.
Detailed tolerances, calibrated results, and claim boundaries are in
`docs/orbit-results.md`.

Direct outputs default to `.bsk/examples/orbit_propagation/`. Under `bsk run`,
registered telemetry, verification reports, comparison data, and plots are
redirected into the run directory.

## Vizard

`examples/orbit_propagation/vizard.py` records both gravity cases with
Basilisk's `vizSupport` and registers `point_mass_vizard` and `j2_vizard`
playback files. Vizard is a separate desktop application and is not required
for simulation, CI, or numerical verification. V1 supports offline playback,
not live streaming.

## Skill

`skills/basilisk/` is the canonical skill. Its entry point routes agents to six
focused references. Installation links or copies this directory to:

- Codex: `.agents/skills/basilisk`
- Claude Code: `.claude/skills/basilisk`

See `docs/skill-installation.md`. Validate skill changes with the Agent Skills
quick validator and `tests/test_skill.py`.

## Verification commands

```bash
uv run ruff check .
uv run ruff format --check .
BSK_SUPPORT_DATA_CACHE=.bsk/support-data uv run pytest
uv build
```

Tests require at least 90% statement coverage. CI runs the same lint, format,
test, and package-build checks on Python 3.11.
