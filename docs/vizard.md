# Vizard Playback

[Vizard](https://github.com/AVSLab/vizard) is AVS Laboratory's separate Unity
application for three-dimensional Basilisk visualization. Basilisk Tools keeps
it optional: simulations and numerical verification do not require the desktop
application.

## Generate the playback files

The `bsk` package already contains Basilisk's `vizInterface`. Generate verified
offline recordings for both reference gravity cases with:

```bash
export BSK_SUPPORT_DATA_CACHE=.bsk/support-data
uv run bsk run examples/orbit_propagation/vizard.py --json
```

The returned JSON registers two additional artifacts:

```text
point_mass_vizard -> artifacts/point-mass/vizard.bin
j2_vizard         -> artifacts/j2/vizard.bin
```

The run also preserves the normal telemetry, checks, comparison JSON, and plots,
so the 3D presentation and numerical evidence come from the same executions.

You can instead run the scenario directly with `--vizard`:

```bash
uv run python examples/orbit_propagation/scenario.py --vizard
```

## Open a recording

1. Download the Vizard application for macOS, Linux, or Windows from the
   [official Basilisk download page](https://avslab.github.io/basilisk/Vizard/VizardDownload.html).
2. Start Vizard and choose the option to open a saved scenario file.
3. Select either generated `vizard.bin` artifact.
4. Use planet-centric view and enable true trajectory or osculating orbit lines
   to make the J2-driven plane change visible.

Vizard playback files are presentation artifacts, not independent numerical
evidence. Use the registered telemetry and verification report for engineering
claims.

## Why offline playback is the v1 boundary

Basilisk can also live-stream with
`enableUnityVisualization(..., liveStream=True)`, normally over
`tcp://localhost:5556`. That mode requires coordinating a running desktop app,
socket connection, and simulation pacing. It is useful for interactive mission
demos but unnecessary for this repository's reproducible agent workflow, so it
remains future work.
