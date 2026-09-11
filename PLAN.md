# Basilisk Tools v1 Plan

## Objective

Build a polished open-source demonstration showing that a portable domain skill and deterministic tools can make AI coding agents more reliable and efficient when working with AVS Basilisk spacecraft simulations.

The project is intended to be built quickly through AI-assisted development and presented as part of an application to the CU Boulder Satellite Systems Design graduate certificate. Orbit propagation is the flagship demonstration, but the skill and CLI should support general Basilisk workflows.

## Product Thesis

AI agents are good at writing code but can make subtle mistakes in engineering simulations, including incorrect units, frames, APIs, message connections, and telemetry configuration. Domain instructions alone are not enough when numerical and runtime facts can be obtained deterministically.

Basilisk Tools combines:

```text
Portable Basilisk skill
          ↓
AI agent creates or modifies a scenario
          ↓
Deterministic CLI inspects and executes it
          ↓
Numerical checks and structured artifacts
          ↓
Agent analyzes evidence and iterates
```

The skill provides domain knowledge and workflows. The CLI provides facts. Basilisk remains the source of truth.

## v1 Success Story

An AI coding agent should be able to:

1. Load the Basilisk skill.
2. Understand or create a Basilisk scenario.
3. Inspect its processes, tasks, modules, and messages when supported.
4. Run it through a predictable CLI.
5. Read structured results and telemetry.
6. Verify declared numerical expectations.
7. Diagnose failures and make a focused correction.
8. Rerun the simulation and explain the result.

The primary demo asks an agent to create and analyze a low-Earth-orbit simulation comparing point-mass gravity with a J2 gravity model.

## v1 Scope

### 1. Portable Basilisk Skill

Create one focused skill rather than several shallow skills:

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

The skill should:

- Follow the open Agent Skills `SKILL.md` format.
- Work with Codex and Claude Code through documented installation paths.
- Be concise and action-oriented.
- Use progressive disclosure for detailed references.
- Teach agents to find and adapt official Basilisk examples.
- Prefer existing Basilisk modules over invented physics.
- Emphasize explicit units, coordinate frames, and conventions.
- Require inspection, execution, and verification after changes.
- Teach a systematic debugging loop.

Do not copy the Basilisk documentation. Convert essential knowledge into decision rules, workflows, warnings, and known-good patterns, with links to authoritative sources.

### 2. Thin Deterministic CLI

Create an installable Python package named `basilisk-tools`, using the import package `basilisk_tools` and executable `bsk`.

The v1 commands are:

```bash
bsk doctor
bsk run <scenario.py>
bsk inspect <scenario.py>
bsk verify <scenario-or-run>
```

All commands should provide readable terminal output and support machine-readable JSON where applicable.

#### `bsk doctor`

Report:

- Python version and executable.
- Basilisk installation and version.
- Basilisk Tools version.
- Required and optional dependencies.
- Actionable environment errors.

#### `bsk run`

- Execute the scenario in an isolated child process.
- Support arbitrary Python scenarios at the execution boundary.
- Capture stdout, stderr, exit code, timing, and status.
- Support a timeout and graceful interruption.
- Record scenario path and SHA-256 hash.
- Record relevant tool and runtime versions.
- Write a versioned JSON result.
- Preserve registered artifacts.
- Keep JSON command output free from scenario logging.

#### `bsk inspect`

- Inspect supported scenarios without executing the full simulation.
- Report processes, tasks, modules, execution order, and message connections when available through Basilisk.
- Report unsupported information honestly rather than guessing.
- Run scenario loading and inspection in a child process.
- Initially allow deep inspection to require the optional instrumented-scenario contract.

#### `bsk verify`

- Run deterministic checks declared by an instrumented scenario or evaluation fixture.
- Return individual check results and an overall pass/fail status.
- Include expected values, actual values, tolerances, and units where relevant.
- Avoid pretending that arbitrary Python scenarios can be semantically verified automatically.

### 3. Scenario Support Levels

Support two explicit levels:

#### Standard scenarios

Any trusted Python scenario can be executed with `bsk run`. The CLI captures process-level results but does not promise deep inspection, automatic telemetry discovery, or semantic verification.

#### Instrumented scenarios

A small optional Python contract exposes the configured Basilisk simulation, registered telemetry, artifacts, and verification checks. This enables deeper `inspect` and `verify` behavior while scenario construction remains normal Basilisk Python.

The contract must remain small and should be designed from the needs of the reference example rather than as a general plugin framework.

### 4. Orbit-Propagation Demonstration

Create one polished, manually reviewed reference scenario that supports:

- A low Earth orbit around Earth.
- Point-mass gravity.
- J2 gravity perturbation.
- Configurable propagation duration and sampling interval.
- Position and velocity telemetry.
- Classical orbital elements over time.
- Orbit and orbital-element plots.
- Machine-readable metrics.
- Explicit frames, units, assumptions, and tolerances.

Verification should cover, as applicable:

- Correct initial orbital elements.
- Bounded specific orbital energy and angular-momentum drift in the two-body case.
- Expected qualitative and quantitative secular RAAN behavior with J2.
- Finite telemetry with monotonically increasing time.
- Repeatable results within stated numerical tolerances.

The demonstration should make claim boundaries clear. It should distinguish expected physical behavior from numerical error and avoid claiming validation beyond the implemented checks.

### 5. Agent Evaluations

Create four small evaluation cases:

1. Create a two-body orbit-propagation scenario.
2. Add J2 and explain the resulting orbital behavior.
3. Find and repair a kilometer-versus-meter error.
4. Find and repair missing or incorrectly configured telemetry.

Each case should include:

```text
evals/<case>/
├── prompt.md
├── starting_files/
├── expected.toml
└── verify.py
```

Run each case, where practical, with:

- Codex without the skill.
- Codex with the skill and CLI.
- Claude Code without the skill.
- Claude Code with the skill and CLI.

Record:

- Whether the task completed.
- Whether deterministic checks passed.
- Failed simulation attempts.
- Human intervention required.
- Elapsed time.
- Technical correctness of the explanation.
- Tool or token usage when reliably available.

This is a small evaluation study, not a comprehensive scientific benchmark. Report the method and limitations honestly.

### 6. Repository Presentation

The GitHub repository should include:

- A concise README with a clear value proposition.
- Reproducible installation and quick-start instructions.
- An architecture diagram.
- A short demonstration recording or animated image.
- Example terminal and JSON output.
- Orbit plots and an explanation of the observed behavior.
- Evaluation method and results.
- Automated tests and visible CI status.
- Clear project limitations and future work.

## Run Artifact Contract

Store runs under the current project by default:

```text
.bsk/runs/<run-id>/
├── result.json
├── metadata.json
├── stdout.log
├── stderr.log
├── telemetry.csv
└── artifacts/
```

Not every run must contain telemetry or additional artifacts. JSON files must include `schema_version: 1`. Large telemetry should be referenced rather than embedded in command output.

Do not capture the entire environment because it may contain secrets. Scenarios are treated as trusted local code.

## Technical Stack

- Python 3.11 for the initial development and CI target.
- Standard `pyproject.toml` packaging with `uv` for local environments and locking.
- Typer for the CLI and Rich for human-readable output.
- Standard-library JSON for machine-readable output.
- AVS Basilisk as the simulation source of truth.
- NumPy for numerical analysis.
- Matplotlib for plots.
- CSV for v1 telemetry interchange.
- Dataclasses and enums for internal result models.
- pytest and pytest-cov for testing.
- Ruff for formatting and linting.
- GitHub Actions for CI.
- Markdown and Mermaid for repository documentation.

Do not add a web application, database, LLM SDK, or agent orchestration framework in v1.

## Proposed Repository Structure

```text
basilisk-tools/
├── src/
│   └── basilisk_tools/
│       ├── cli.py
│       ├── doctor.py
│       ├── runner.py
│       ├── inspection.py
│       ├── verification.py
│       ├── results.py
│       └── worker.py
├── skills/
│   └── basilisk/
├── examples/
│   └── orbit_propagation/
├── evals/
├── tests/
├── docs/
├── pyproject.toml
├── uv.lock
├── README.md
├── PLAN.md
└── REFERENCE.md
```

Create modules only when their responsibility is needed. Avoid reproducing this structure mechanically before implementation requires it.

## Incremental Build Milestones

Each step is intentionally similar in scope and ends with a working, verifiable checkpoint. Complete and test one step before expanding the project in the next.

### Step 1: Project foundation

**Status:** Complete.

- Set up `pyproject.toml`, the `src` package, pytest, Ruff, and GitHub Actions.
- Define the initial result models and JSON schema version.
- Add minimal success and failure scenario fixtures.
- Confirm the package installs and the empty CLI runs.

**Milestone:** A clean Python project installs locally and passes its first automated checks.

### Step 2: Reference orbit scenario

**Status:** Complete.

- Build a minimal point-mass low-Earth-orbit scenario.
- Record position and velocity telemetry.
- Calculate classical orbital elements.
- Add deterministic checks for initial conditions, finite telemetry, and time ordering.

**Milestone:** The reference scenario runs directly and produces verified telemetry without using the CLI.

### Step 3: Perturbation and analysis

**Status:** Complete.

- Add the J2 gravity configuration.
- Calculate energy, angular momentum, and RAAN metrics.
- Establish justified numerical tolerances.
- Produce the initial orbit and orbital-element plots.

**Milestone:** Point-mass and J2 runs produce repeatable results with documented physical and numerical behavior.

### Step 4: Deterministic execution

**Status:** Complete.

- Implement `bsk doctor`.
- Implement `bsk run` with child-process isolation.
- Create run directories, logs, metadata, and structured results.
- Test success, Python failure, timeout, and JSON output.

**Milestone:** The CLI reliably runs arbitrary trusted Python scenarios and preserves auditable results.

### Step 5: Basilisk-aware tooling

**Status:** Complete.

- Define the smallest useful instrumented-scenario contract.
- Implement `bsk inspect` using available Basilisk runtime information.
- Implement `bsk verify` for declared deterministic checks.
- Integrate the reference orbit scenario with both commands.

**Milestone:** The CLI can inspect and verify the project’s instrumented Basilisk scenario without guessing.

### Step 6: Portable agent skill

**Status:** Complete.

- Write the core `SKILL.md`.
- Add only the reference documents required by the planned agent tasks.
- Document installation for Codex and Claude Code.
- Test explicit invocation, implicit invocation, and the core workflow.

**Milestone:** Both Codex and Claude Code can load the same canonical skill and use the CLI correctly.

### Step 7: Agent evaluations

**Status:** Evaluation suite complete; controlled agent runs pending.

- Finish the four evaluation fixtures and deterministic verifiers.
- Run baseline and skill-assisted cases where practical.
- Preserve raw outputs and score the results consistently.
- Improve instructions or tooling in response to repeated failures.

**Milestone:** The repository contains reproducible evidence showing where the skill and tools help agents and where they do not.

### Step 8: Portfolio release

**Status:** Release candidate complete; controlled agent results and first GitHub CI run pending.

- Complete tests and CI coverage for the demonstrated workflow.
- Add final architecture, workflow, and result visuals.
- Document installation, evaluation results, and limitations.
- Record a concise end-to-end demonstration and perform a fresh-user review.

**Milestone:** A new visitor can understand, install, run, and evaluate the complete project from the GitHub repository.

## Acceptance Criteria

v1 is complete when:

- A new user can install the project from GitHub using documented steps.
- `bsk doctor` clearly reports a working or broken environment.
- `bsk run` handles successful, failed, and timed-out Python scenarios and writes valid run artifacts.
- The reference orbit scenario runs in point-mass and J2 configurations.
- The reference numerical checks pass within documented tolerances.
- `bsk inspect` reports useful Basilisk structure for the reference scenario.
- The Basilisk skill can be loaded by Codex and Claude Code.
- All four evaluation cases have deterministic pass/fail checks.
- Baseline and skill-assisted results are documented without overstating conclusions.
- Automated tests pass in GitHub Actions.
- The repository contains a clear, compelling demonstration of the complete workflow.

## Non-Goals

v1 will not:

- Wrap every Basilisk module in CLI commands.
- Replace the Basilisk Python API or official documentation.
- Guarantee deep inspection of arbitrary Python scenarios.
- Infer units or useful telemetry from arbitrary code.
- Provide exhaustive semantic validation.
- Build a universal engineering-solver framework.
- Support cloud or distributed execution.
- Provide a GUI or web dashboard.
- Include a database, plugin ecosystem, or agent runtime.
- Automate large parameter sweeps or Monte Carlo campaigns.
- Promise support for every operating system and Basilisk release.

## Risks and Controls

### Instrumentation becomes a framework

Keep the optional scenario contract limited to what the reference scenario and evaluation cases require.

### The skill becomes rewritten documentation

Favor operational instructions, decision rules, and targeted references. Link to official documentation for exhaustive API details.

### The CLI becomes a generic subprocess wrapper

Prioritize useful Basilisk-specific inspection, verification, and result metadata after the runner is reliable.

### Evaluation claims become too broad

Publish fixtures, scoring logic, raw outcomes, and limitations. Compare agents only within clearly described conditions.

### Portfolio polish consumes implementation time

Maintain a working end-to-end demonstration from the first week. Treat additional commands and generalized abstractions as lower priority than documentation, tests, and numerical credibility.

## Future Direction

The v1 project can serve as a reference implementation for an engineering-solver agent enablement pack: portable skills, deterministic adapters, validation cases, and reproducible artifacts.

Only generalize that pattern after implementing it for a second real solver. Potential future work includes richer telemetry, run comparison, parameter sweeps, visualization, additional Basilisk domains, and contract work adapting the method to other open-source engineering tools.
