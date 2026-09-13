# Create a Two-Body Orbit Scenario

Implement `scenario.py` as an AVS Basilisk point-mass Earth orbit propagation.
Use the constants already provided in the starter and ordinary Basilisk Python
APIs. Do not replace the simulation with hand-written orbital equations.

Requirements:

- Configure one spacecraft in a 7,000 km semi-major-axis orbit using SI units.
- Use Earth as the central point-mass gravity body.
- Propagate at least 1,200 seconds with a step no larger than 10 seconds.
- Record inertial position and velocity at least every 60 seconds.
- Write `telemetry.csv` with the exact columns already declared in the starter.
- Select the output directory with `registered_output_directory()` and register
  the CSV as the `telemetry` artifact so `bsk run` can preserve it.
- Do not embed fabricated states or evaluator-specific pass values.

Use `bsk doctor` and `bsk run`; base the explanation on their captured output,
telemetry, and artifacts. In `explanation.md`, state the units, frame, gravity
assumptions, evidence used, and important limitations.
