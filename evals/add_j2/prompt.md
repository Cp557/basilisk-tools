# Add J2 Gravity

The starter propagates a correct point-mass low Earth orbit. Modify it to use
Basilisk's supported degree-2 Earth gravity data so the recorded trajectory
includes J2. Preserve the initial orbit, timing, telemetry schema, and artifact
registration.

Use official Basilisk APIs and support data rather than adding a custom J2
acceleration. Run the scenario through `bsk run` and use the case verifier.

In `explanation.md`, explain the expected sign of the secular RAAN rate for this
prograde orbit, compare the observed rate with first-order theory, state the
frame and units, and explain why two-body Keplerian energy is not the right J2
conservation diagnostic.
