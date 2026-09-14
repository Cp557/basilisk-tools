# Orbit Propagation: Point Mass vs J2

This scenario propagates the same low Earth orbit with point-mass and degree-2
J2 Earth gravity. The default five-hour window makes J2 nodal regression visible.

Run it directly from the repository root:

```bash
uv run python examples/orbit_propagation/scenario.py
```

Inspect its structure or run its declared checks:

```bash
uv run bsk inspect examples/orbit_propagation/scenario.py
uv run bsk verify examples/orbit_propagation/scenario.py
```

The first J2 run downloads Basilisk's versioned gravity file. Outputs are written
beneath `.bsk/examples/orbit_propagation/`:

- `point-mass/` and `j2/` contain CSV telemetry and JSON verification.
- `comparison.json` contains energy, angular-momentum, and RAAN metrics.
- `orbit_comparison.png` and `orbital_elements.png` visualize both runs.

Use `--help` to select a gravity model, duration, integration step, sample
interval, or output directory.

The model uses SI units in an Earth-centered inertial frame and excludes drag,
third-body gravity, and solar radiation pressure. See the
[result summary](../../docs/orbit-results.md) for metrics and claim boundaries.

Generate offline playback files for the separate Vizard desktop application:

```bash
uv run bsk run examples/orbit_propagation/vizard.py --json
```

See the [Vizard guide](../../docs/vizard.md) to open the generated `.bin` files.
