# Orbit-Propagation Results

The reference scenario compares point-mass and degree-2 J2 Earth gravity using
the same initial osculating orbit and Basilisk 2.11.1.

## Configuration

| Quantity | Value |
| --- | ---: |
| Semi-major axis | 7,000,000 m |
| Eccentricity | 0.01 |
| Inclination | 55 degrees |
| Initial RAAN | 40 degrees |
| Argument of periapsis | 30 degrees |
| Propagation | 18,000 s |
| Integration step | 10 s |
| Telemetry interval | 60 s |
| Frame | Earth-centered inertial N |

The model excludes drag, third-body gravity, and solar radiation pressure. The
J2 case uses Basilisk's versioned `GGM03S-J2-only.txt` file at degree 2; it is
not a high-degree Earth gravity model.

## Verified metrics

| Check | Result | Limit/reference |
| --- | ---: | ---: |
| Point-mass relative Keplerian-energy drift | `7.97e-11` | `<= 1e-8` |
| Point-mass relative angular-momentum drift | `3.94e-11` | `<= 5e-9` |
| Point-mass absolute RAAN rate | `1.92e-19 rad/s` | `<= 1e-12 rad/s` |
| J2 fitted RAAN rate | `-8.348e-7 rad/s` | Theory: `-8.338e-7 rad/s` |
| J2 RAAN-rate relative error | `0.117%` | `<= 2%` |
| J2 relative angular-momentum-z drift | `3.95e-11` | `<= 5e-9` |

![Point-mass and J2 orbit comparison](assets/orbit_comparison.png)

![Osculating orbital-element histories](assets/orbital_elements.png)

## Interpretation

The point-mass state follows a fixed Keplerian orbital plane, and its energy
and angular-momentum drift remain far inside the calibrated numerical limits.

J2 produces short-period variation in the osculating semi-major axis,
eccentricity, and inclination, plus secular nodal regression. Because this is a
prograde orbit, first-order theory predicts a negative RAAN rate, matching the
simulation. The fitted rate differs from first-order theory by about `0.117%`
over the five-hour window.

The plotted J2 Keplerian-energy variation is not labeled numerical drift: the
two-body energy expression omits the J2 potential. For the axisymmetric J2
model, conservation of inertial angular momentum's z-component is the relevant
symmetry check used here.

These results validate the implemented reference checks for this documented
configuration. They do not validate Basilisk itself or establish accuracy for
different orbits, integrators, gravity degrees, or mission environments.
