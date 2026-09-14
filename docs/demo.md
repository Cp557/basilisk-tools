# End-to-End Demonstration

The README animation is a concise rendering of this workflow. Run the commands
below for the complete live demonstration.

## 1. Establish the environment

```bash
uv sync --locked --all-groups
export BSK_SUPPORT_DATA_CACHE=.bsk/support-data
uv run bsk doctor
```

Point out the exact Python, Basilisk, and Basilisk Tools versions. An unhealthy
environment exits nonzero with an actionable error.

## 2. Inspect before execution

```bash
uv run bsk inspect examples/orbit_propagation/scenario.py
```

Show the point-mass and J2 cases, the `leoSpacecraft` and state-recorder
execution order, their message connection, the 10-second task period, and the
declared SI telemetry in the Earth-centered inertial N frame.

## 3. Run with auditable artifacts

```bash
uv run bsk run examples/orbit_propagation/scenario.py --json
```

Open the returned run directory. `result.json` and `metadata.json` contain
structured evidence; scenario output is isolated in logs; CSV, verification,
comparison, and plot files are registered under `artifacts/`.

## 4. Verify the physics claims

```bash
uv run bsk verify examples/orbit_propagation/scenario.py
```

Highlight initial-condition and telemetry-integrity checks, point-mass energy
and angular-momentum drift, and the J2 RAAN-rate comparison. Explain that a
successful process alone would not prove these claims.

## 5. Show optional 3D playback

```bash
uv run bsk run examples/orbit_propagation/vizard.py --json
```

Open either registered `.bin` artifact in Vizard to compare the point-mass and
J2 trajectories in 3D. Vizard is optional and does not participate in the
numerical checks.

## Animation source

Regenerate the checked-in terminal animation after changing command names,
versions, or calibrated metrics:

```bash
uv run python docs/render_demo.py
```

The animation is a curated walkthrough backed by current command behavior and
reference metrics.
