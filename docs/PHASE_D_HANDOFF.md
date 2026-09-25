# Phase D handoff: techno-economics and operational emissions

## Scope completed

Phase D implements a normalized 1 MWh useful-heat accounting model for pathways
A-E. It separates recovered source heat, heat-pump electricity, storage and
delivery losses, storage auxiliary electricity, pumping electricity, avoided
natural gas, operating cost, capital cost, replacement, discounting, NPC, LCOH,
and operational CO2e. COP electricity is counted once.

Raw EIA, EPA, NIST, DOE, and Federal Reserve snapshots are retained in
`data/raw/techno_economic_sources/phase_d_20260924` and registered with hashes
in `data/metadata/data_snapshots.csv`.

## Reproducible outputs

- `data/metadata/techno_economic_parameter_sources.csv`
- `data/metadata/techno_economic_parameters.csv`
- `results/techno_economic/energy_emissions.csv`
- `results/techno_economic/economics.csv`
- `results/techno_economic/sensitivity.csv`
- `results/techno_economic/frontier_source_potential.csv`

The broad sensitivity grid contains 3,888 cases. It preserves
unfavorable results: avoided operational emissions range from
-26.35 to
149.25 kg CO2e per MWh
useful heat, while incremental NPC ranges from
USD -4,690,918 to
USD 6,806,848.

On the normalized case-C energy-only calculation using the eGRID SRTV
total-output factor, avoided operational emissions are
107.21 kg CO2e per MWh useful heat.
The generic full-system comparator has LCOH
USD 56.51/MWh-th; it is not a
Frontier-specific project estimate.

The measured Frontier workbook contains
49,869 valid waste-heat
observations totaling
75,573.6 observed MWh-th.
2,691 expected ten-minute
timestamps are absent, and no missing energy is imputed.

## System boundaries

- The baseline includes natural-gas fuel and existing steam delivery loss; sunk
  boiler and network capital are excluded.
- Operational emissions include combustion and purchased electricity.
- eGRID total-output is the average-factor case; grid-loss-adjusted and
  non-baseload rates are labeled sensitivities.
- Generic Danish heat-pump and storage costs are comparator inputs, not
  Frontier quotations.
- Normalized comparator rows assume unity source-capture efficiency and report
  zero source-side loss; the case-specific capture efficiency remains open.
- The existing steam-line loss is not reused as a Frontier hot-water network
  loss function.
- Equipment, construction, refrigerant, upstream fuel, and other lifecycle
  emissions are not claimed without supporting evidence.
- Population-weighted thermal-burden benefit is not monetized.

## Open evidence gates

- `case_auxiliary_electricity_fraction`: Do not add the generic 1% value to a COP that may already include unit auxiliaries.
- `case_source_capture_efficiency`: No measured source heat-exchanger loss is available.
- `case_full_installed_cost`: ORNL reports equipment-only cost with incomplete price-year and balance-of-plant scope.
- `transport_network_capex`: No route, hydraulics, or project quote is available.
- `equipment_embodied_co2e`: Operational factors do not support a cradle-to-grave LCA.
- `case_hourly_receiving_demand`: Annual dispatch and total residual rejection cannot be calculated.
- `case_total_residual_rejection`: Requires synchronized source, demand, storage, and outage dispatch.

## Decision

**NO-GO remains in force.** Phase D quantifies a transparent comparator and
sensitivity envelope, but case-specific LCOH, NPC, lifecycle CO2e, annual
delivery, and total residual rejection remain withheld until the open evidence
gates and finite dispatch are resolved.

## Rebuild

```bash
make techno-economic
make phase-d-handoff
```
