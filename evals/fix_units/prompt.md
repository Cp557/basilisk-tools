# Repair an Orbit Unit Error

The starter is intended to propagate a 7,000 km semi-major-axis Earth orbit,
but it produces an impossible state or fails numerical verification. Diagnose
and repair the root cause without changing the intended orbit or weakening the
evaluation checks.

Preserve the point-mass model, timing, telemetry schema, and registered
`telemetry` artifact. Use `bsk run` and its captured output, telemetry, and
artifacts as evidence.

In `explanation.md`, identify the faulty value and why it is physically
impossible, state the corrected Basilisk units, and distinguish successful
execution from numerical verification.
