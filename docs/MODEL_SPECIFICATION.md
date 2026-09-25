# Conserved-heat allocation model

## Control volume and conserved quantity

Each grid cell \(i\) has area \(A_i\). The reduced-order atmospheric control
volume has configured mixing height \(h\), density \(\rho\), and specific heat
\(c_p\), giving sensible heat capacity

\[
C_i = A_i h \rho c_p.
\]

The decision variable \(Q_{itjt'}\) is thermal energy removed from source
cell-time \((i,t)\) and released at sink cell-time \((j,t')\). Unless a
separate radiative-loss experiment is explicitly activated, the model imposes

\[
\sum_{it} Q^{out}_{it} = \sum_{jt'} Q^{in}_{jt'}.
\]

Thus relocation changes the distribution of heat but does not cool the planet.
The local reduced-order temperature response is

\[
\Delta T_i = Q_i / C_i.
\]

This is a screening approximation, not a resolved atmospheric response.

## Thermal stress and human burden

Specific humidity \(q\) and surface pressure \(p\) give vapor pressure

\[
e = \frac{q p}{0.622 + 0.378q}.
\]

With \(e\) expressed in hPa, the primary thermal metric is

\[
H = T_C + \frac{5}{9}(e - 10),
\]

where \(H\) is Humidex and \(T_C\) is air temperature in degrees Celsius.
The stress excess is \(s_{it}=\max(H_{it}-H_0,0)\). The primary human burden is

\[
B_{it}=P_i s_{it}^{\gamma},
\]

using population count \(P_i\), reference \(H_0\), and curvature \(\gamma\).
This is an exposure-burden index, not an epidemiological mortality model.

For an infinitesimal heat addition with humidity and pressure held fixed,
\(\partial H/\partial T=1\), and the marginal burden per GJ is

\[
m_{it} =
P_i\gamma s_{it}^{\gamma-1}\frac{10^9}{C_i}
\quad \text{for }s_{it}>0,
\]

and zero otherwise. Removal from a stressed source has marginal benefit
\(m_{it}\); addition to a sink has marginal burden \(m_{jt'}\).

The Stull wet-bulb approximation is retained as a sensitivity metric only.
Values outside its validation domain of \(-20\) to \(50\) degrees Celsius and
5% to 99% relative humidity are stored as missing rather than extrapolated.

## One-unit objective

For one GJ moved from \((i,t)\) to \((j,t')\), the screening objective is

\[
V_{itjt'} =
m_{it} - m_{jt'}
- c_d d_{ij}
- c_s(t'-t),
\]

where \(d_{ij}\) is great-circle distance, \(c_d\) is transport penalty per
GJ-km in burden-objective units, and \(c_s\) is storage penalty per
GJ-time-step in the same units. These are explicit decision penalties, not
energy losses: one GJ is still removed and one GJ released. Same-time spatial,
same-location later-time, and joint spatiotemporal cases are evaluated
separately. A negative best feasible \(V\) is retained and means that the
no-relocation option dominates under the stated assumptions.

## Primary feasibility rules

The primary sink set requires land fraction ≥0.5 and excludes observed
cryosphere cells, defined by sea-ice fraction ≥0.15 or snow water equivalent
≥1 kg m^-2. Population absence alone never establishes environmental
acceptability. Distance, storage window, local temperature-change, and
load-cap constraints are imposed progressively rather than embedded in the
unconstrained prescribed-slab bound. Polar, desert, ocean, cryosphere,
nighttime, and winter optima are reported as pathological diagnostics even
where they are excluded from the primary constrained scenario.

All three one-unit solvers retain the best feasible pair even when its
objective value is negative. The explicit no-relocation option is therefore
evaluated in reporting rather than introduced by discarding inconvenient
solver outputs.

Observed outgoing longwave radiation is descriptive context only. It is not
used as the causal derivative of radiative loss with respect to an imposed
surface heat increment.
