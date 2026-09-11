# Orbit Propagation: Point Mass vs J2

This reference scenario propagates the same low Earth orbit using AVS Basilisk's
`Spacecraft` model with point-mass and J2 Earth gravity. Its default three-orbit
window makes J2-driven nodal regression visible without turning the example into
a high-fidelity mission model.

Run it directly from the repository root:

```bash
uv run python examples/orbit_propagation/scenario.py
```

Inspect the configured structure or run the declared checks through the
optional scenario contract:

```bash
uv run bsk inspect examples/orbit_propagation/scenario.py
uv run bsk verify examples/orbit_propagation/scenario.py
```

The first J2 run downloads Basilisk's versioned `GGM03S-J2-only.txt` support file
through Basilisk's data fetcher. Outputs are written beneath
`.bsk/examples/orbit_propagation/`:

- `point-mass/` and `j2/` contain CSV telemetry and JSON verification.
- `comparison.json` contains energy, angular-momentum, and RAAN metrics.
- `orbit_comparison.png` and `orbital_elements.png` visualize both runs.

Use `--gravity-model point-mass`, `--gravity-model j2`, or
`--gravity-model both`. The script's `--help` option also exposes propagation
duration, integration step, sampling interval, and output location.

The scenario assumes an Earth-centered inertial frame and excludes drag,
third-body gravity, and solar radiation pressure. The J2 case includes only the
degree-2 zonal term; it is not a complete Earth gravity model.

Keplerian specific energy excludes the J2 potential, so it is a conservation
check only for the point-mass run. J2 verification instead checks nodal regression
against first-order secular theory and conservation of the inertial z-component
of specific angular momentum.

See the repository's [result summary](../../docs/orbit-results.md) for the
checked-in plots, calibrated metrics, interpretation, and claim boundaries.

Generate offline playback files for the separate Vizard desktop application:

```bash
uv run bsk run examples/orbit_propagation/vizard.py --json
```

See the [Vizard guide](../../docs/vizard.md) for the artifact paths and playback
workflow. Vizard is optional and is not used as numerical verification evidence.
