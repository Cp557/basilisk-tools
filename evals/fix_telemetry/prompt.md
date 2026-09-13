# Repair Missing Telemetry

The starter configures and executes a valid point-mass orbit, but its telemetry
artifact is empty or unusable. Find and repair the Basilisk recorder setup. Do
not synthesize states, alter the intended orbit, or weaken the output contract.

Preserve the exact telemetry columns, record at least every 60 seconds, and
register the CSV as `telemetry`. Use `bsk run` and its captured output,
telemetry, and artifacts as evidence.

In `explanation.md`, identify the recorder lifecycle problem, explain why the
original history was empty, and state the resulting sampling interval, units,
and inertial frame.
