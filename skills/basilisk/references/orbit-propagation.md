# Orbit Propagation

Read this reference for orbital initial conditions, gravity configuration,
classical elements, and perturbation claims.

## Declare conventions

For every state or result, identify:

- central body and gravitational parameter;
- origin and reference frame;
- meters versus kilometers and seconds versus nanoseconds;
- radians versus degrees;
- osculating versus mean elements;
- included and excluded perturbations.

Basilisk spacecraft translational states such as `r_BN_N` and `v_BN_N` are
normally SI values expressed in the inertial `N` frame, but confirm the payload
and scenario documentation rather than relying on naming alone.

## Initialize an orbit

`orbitalMotion.ClassicElements` uses semi-major axis `a`, eccentricity `e`,
inclination `i`, right ascension of the ascending node `Omega`, argument of
periapsis `omega`, and true anomaly `f`. Angles are radians. Convert to a state
with `orbitalMotion.elem2rv(mu, elements)` and assign the spacecraft hub initial
position and velocity. Element distances must use units consistent with `mu`.
With Basilisk's standard Earth gravity data, `mu` is in m^3/s^2, so use
`elements.a = 7_000_000.0` for a 7,000 km semi-major axis, not `7_000`.

Avoid classical-element claims near singular cases: RAAN is undefined for an
equatorial orbit, and argument of periapsis is undefined for a circular orbit.
Use nonsingular elements or state-vector checks when the requested orbit is near
those conditions.

## Configure gravity

- Create the body's gravity object with `simIncludeGravBody.gravBodyFactory()`.
- Mark the intended origin body with `isCentralBody = True`.
- Add the gravity bodies to the spacecraft through the factory.
- For spherical harmonics, use a Basilisk-supported coefficient file and the
  intended maximum degree. Record the filename and degree in outputs.
- Do not manually add a second copy of an acceleration already supplied by the
  configured gravity model.

## Analyze point mass and J2

For a two-body point-mass model, useful numerical checks include bounded drift
in Keplerian specific energy and angular-momentum magnitude. These are
integration diagnostics after confirming the initial state.

For a prograde orbit under an axisymmetric J2 model, first-order secular theory
predicts

```text
dOmega/dt = -(3/2) n J2 (Re/p)^2 cos(i)
p = a(1-e^2)
```

Compare a fitted, unwrapped RAAN rate over multiple orbits with this estimate.
Do not call Keplerian specific-energy variation a numerical error in the J2
case: the two-body energy expression omits the J2 potential. The inertial
angular-momentum z-component is the relevant symmetry diagnostic for this
axisymmetric model.

Use `examples/orbit_propagation/scenario.py` as the maintained point-mass/J2
reference and preserve its documented claim boundaries when adapting it.

## Sources

- [Basilisk basic orbit scenario](https://avslab.github.io/basilisk/_modules/scenarioBasicOrbit.html)
- [Basilisk orbitalMotion utility](https://avslab.github.io/basilisk/Documentation/utilities/orbitalMotion.html)
- [Basilisk gravity setup](https://avslab.github.io/basilisk/Documentation/utilities/simIncludeGravBody.html)
