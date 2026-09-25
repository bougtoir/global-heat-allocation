# Phase C Handoff: Practical Thermal-Management Calibration

## Status

Phase C is complete for technology calibration. It does **not** close the
finite-dispatch or submission-readiness gates.

The selected engineering case remains Frontier waste heat paired with the
ORNL 5600-5700-5800 complex. The calibrated technology is a local
high-temperature water-water heat pump. Atmospheric steel tank thermal energy
storage (TTES) and near-distance hot-water transport are retained only as
explicit sensitivities because the case-specific hydraulic and demand data
needed to calibrate them are unavailable.

The project remains **NO-GO** for journal submission.

## Reproducible outputs

Run:

```bash
make technology-parameters
```

This verifies the raw-data snapshots, validates their structure, and rebuilds:

- `data/metadata/technology_pathways.csv`
- `data/metadata/technology_parameters.csv`
- `data/metadata/technology_parameter_sources.csv`

The generator reads the current Danish Energy Agency Excel workbooks directly.
PDF-derived values are recorded with exact document locations and applicability
limits. Every parameter is labeled as a direct source value, transparent
derivation, scenario, definition, or missing required value.

## Current-source audit

The four initially collected Phase C PDFs were retained unchanged and
registered. Before freezing the calibration, the Danish Energy Agency source
pages were checked again. Newer official 2026 versions were available, so the
following were also preserved and registered:

- Energy Plants catalogue version 0019;
- August 2026 electricity and district-heat Excel data sheets;
- June 2026 large-heat-pump technology brief;
- Energy Storage catalogue and Excel data sheets version 0011;
- July 2026 tank-thermal-energy-storage technology brief.

The newer Excel data sheets are the controlling generic sources. Superseded
catalogues remain in the provenance ledger and are not overwritten.

## Pathway decisions

### A. Conventional rejection

Canonical baseline. Measured Frontier waste heat is rejected through the
existing cooling pathway, with zero useful heat credited and all source heat
remaining residual rejection. Existing cooling auxiliary electricity is not
separately identifiable from the facility accessory load.

### B. Same-location temporal storage and later reuse

Sensitivity only. Heat would be upgraded, stored in atmospheric TTES, and
released later to a co-located demand. The technology class is defensible, but
the ORNL heating-water return temperature, hydraulic design, tank size, and
hourly demand are unavailable. No canonical Frontier storage capacity or
benefit is claimed.

### C. Local direct reuse

Case-calibrated technology pathway. The ORNL assessment specifies three
1 MW Carrier 61XWHZE units, approximately 30°C source water, 85°C delivered
water, and COP 3.08. This pathway can enter Phase D, but finite dispatch remains
blocked by the missing receiving-demand trace and full installed project cost.

### D. Near-distance transport without storage

Sensitivity only. The maximum modeled distance is limited to 1 mile
(1.609344 km), derived from the existing ORNL steam-line comparator. No
Frontier-specific hot-water route or distance-loss function exists. Generic
COOL DH percentages remain labeled comparators and are not converted into a
per-kilometer loss.

### E. Storage plus near-distance transport

Sensitivity only. This combines the unresolved storage and transport elements,
so it cannot support a calibrated Frontier project claim.

Long-distance low-grade heat transport is excluded from quantitative practical
claims.

## Heat-pump calibration

Case-specific values:

- source condition: approximately 30°C;
- delivered-water temperature: 85°C;
- COP: 3.08;
- unit heating capacity: 1 MW;
- units: 3;
- total heating capacity: 3 MW;
- reported equipment cost: USD 200,000 per unit, with price year and complete
  installed-cost scope unspecified.

Manufacturer context:

- product range: 0.2-2.5 MW;
- delivered water: up to 85°C;
- cascades: at least 12 MW;
- compressor bearing life: 100,000 operating hours, not full-system lifetime.

Current Danish Energy Agency generic comparator:

- 1 MW waste-heat heat pump;
- COP 3.1 at different reference temperatures;
- auxiliary electricity: 1% of heat output and already included in COP;
- technical lifetime: 25 years, with 15-40-year uncertainty range;
- 2025 total nominal investment: EUR 1.13 million/MW;
- 2025 heat-pump equipment investment: EUR 0.55 million/MW;
- fixed O&M: EUR 2,126.745436/MW/year;
- variable O&M: EUR 3.07/MWh.

These generic values are not silently substituted for the Carrier case. The
catalogue reference is an ammonia system at 13/8°C source and 35/70°C district
heat. Its note that 80°C systems cost 15% more is not extrapolated to 85°C.

## Storage calibration

The current Danish Energy Agency 2025 TTES control case reports:

- 5,000 m³ example volume;
- 290 MWh capacity at 55 K and 90% availability;
- 29 MW input and output capacity;
- 98% round-trip efficiency;
- 100% charge and discharge efficiency;
- 0.15%/day storage loss;
- 0.4% auxiliary electricity per unit output;
- 40-year technical lifetime;
- EUR 3.793103 million/GWh specific investment;
- EUR 10.344828/MWh-capacity/year fixed O&M;
- EUR 0.620320/MWh-output variable O&M.

The workbook's 2025 sensitivity columns are preserved as numeric minima and
maxima rather than interpreting the publisher's “Lower” and “Upper” labels as
monotonic for every metric. Key ranges are 210-315 MWh, 1.5-125 MW,
96-99% round-trip efficiency, 0.14-0.21%/day storage loss,
0.3-1.5% auxiliary electricity, 30-50 years, and
EUR 3.142857-7.464286 million/GWh.

The current cost equation is:

\[
P = 3055 V^{-0.309},
\]

where \(P\) is EUR2025/m³ and \(V\) is tank volume in m³. It is valid only for
900-12,000 m³. At the 900 m³ lower boundary, generic 55 K scaling gives
52.2 MWh and the formula gives approximately EUR 336,041. These are
sensitivity values, not a case-specific design. The formula excludes external
pumps, heat exchangers, and network connections.

The storage scenarios retain 6-, 12-, and 18-hour shifts for continuity with
the global analysis. The ORNL hot-water return temperature is missing, so the
actual usable temperature difference and case storage capacity remain open.

## Transport calibration

The ORNL report's 8% loss applies to an existing one-mile **steam** line. It is
context only and is not applied to hot-water transport.

COOL DH provides non-case-specific sensitivity comparators:

- 17% traditional high-density network loss;
- up to 35% traditional low-density network loss;
- 2% pumping electricity per supplied heat;
- 10.8% optimized Østerby network loss;
- 9% initial and 3% full-build Brunnshög network loss.

No central Frontier transport-loss value is selected. Phase D may show these
only as labeled sensitivities.

## Open evidence gates

The following remain explicitly missing:

1. measured hourly heat and hot-water demand for the receiving complex;
2. heating-water return temperature and hydraulic integration design;
3. a Frontier-specific hot-water route, pipe specification, and loss function;
4. a complete installed Carrier project cost with price year and scope;
5. case-specific storage sizing and balance-of-plant cost;
6. operational electricity price, marginal emissions factors, and lifecycle
   boundaries for Phase D.

The published ORNL payback, energy-saving, and emissions outcomes remain source
evidence only. They are not results of this repository.

## Phase D handoff

Phase D should:

1. compute useful heat, heat-pump electricity, residual rejection, and
   auxiliary electricity under explicit boundaries;
2. keep ORNL equipment-only cost separate from the generic full-system
   comparator;
3. calculate CAPEX, OPEX, replacement, NPC, and LCOH with explicit currency
   years and discount assumptions;
4. calculate operational and lifecycle emissions without double counting
   electricity already represented in COP;
5. report B, D, and E only as sensitivities until the open integration data
   are obtained;
6. retain negative and infeasible results and leave the submission decision
   at NO-GO unless all later gates close.
