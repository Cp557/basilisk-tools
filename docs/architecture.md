# Architecture

Basilisk Tools is deliberately small: a portable instruction layer helps an AI
agent use Basilisk correctly, while a deterministic execution layer gathers the
facts needed to check its work.

```mermaid
flowchart TB
    P[User prompt] --> SK[skills/basilisk/SKILL.md]
    SK --> AG[Codex, Claude Code, or compatible agent]
    AG --> PY[Trusted Basilisk Python scenario]

    subgraph CLI[Deterministic bsk boundary]
        D[doctor]
        I[inspect]
        R[run]
        V[verify]
    end

    PY --> I
    PY --> R
    PY --> V
    D --> AG
    I --> AG
    R --> AG
    V --> AG

    I --> IW[Inspection subprocess]
    R --> RW[Execution subprocess]
    V --> VW[Verification subprocess]
    IW --> B[AVS Basilisk]
    RW --> B
    VW --> B
    B --> OUT[Versioned JSON, logs, CSV, plots]
    OUT --> AG
```

## Responsibilities

| Component | Responsible for | Not responsible for |
| --- | --- | --- |
| Basilisk skill | Domain workflow, warnings, source routing, evidence discipline | Numerical truth or executing code |
| `bsk` CLI | Isolation, runtime facts, structured output, artifact preservation | Replacing the Basilisk Python API |
| Scenario contract | Exposing configured cases, telemetry declarations, and checks | General plugin lifecycle or arbitrary-code inference |
| AVS Basilisk | Simulation execution and runtime behavior | Deciding whether the user's engineering claim is justified |

## Scenario support levels

A standard trusted Python scenario runs through `bsk run`. The tool records its
hash, versions, timing, exit status, logs, and registered artifacts, but does not
claim to understand its physics.

An instrumented scenario additionally defines `basilisk_tools_scenario()`. The
factory returns configured, unexecuted cases for inspection and a deterministic
verification callback. This enables `bsk inspect` and `bsk verify` without
pretending arbitrary Python can be interpreted safely or completely.

## Process and data flow

```mermaid
sequenceDiagram
    participant Agent
    participant CLI as bsk parent
    participant Worker as child process
    participant BSK as AVS Basilisk
    participant Disk as run directory

    Agent->>CLI: run scenario.py --json
    CLI->>Disk: metadata.json + directories
    CLI->>Worker: current Python + trusted scenario
    Worker->>BSK: configure and execute
    BSK-->>Worker: telemetry and runtime result
    Worker->>Disk: stdout, stderr, registered artifacts
    Worker-->>CLI: private structured outcome
    CLI->>Disk: result.json
    CLI-->>Agent: clean JSON result
```

Child stdout is never used as structured transport, so arbitrary scenario
logging cannot corrupt CLI JSON. Timeouts and interruptions stop the child
process group. The complete environment is not captured because it may contain
secrets.

## Trust and claim boundaries

- Scenarios are trusted local code and can do anything the current user can do.
- Units and frames are declared, never inferred from variable names.
- `inspect` reports available Basilisk runtime structure and declared metadata.
- `run` success is process evidence only.
- Numerical claims require recorded telemetry and checks with stated tolerances.
- Point-mass Keplerian energy is not treated as a J2 conservation invariant.
