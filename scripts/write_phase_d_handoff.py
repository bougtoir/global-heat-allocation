"""Write the Phase D techno-economic and emissions handoff."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results" / "techno_economic"
PARAMETERS = ROOT / "data" / "metadata" / "techno_economic_parameters.csv"
OUTPUT = ROOT / "docs" / "PHASE_D_HANDOFF.md"


def main() -> None:
    energy = pd.read_csv(RESULTS / "energy_emissions.csv")
    economics = pd.read_csv(RESULTS / "economics.csv")
    sensitivity = pd.read_csv(RESULTS / "sensitivity.csv")
    source = pd.read_csv(RESULTS / "frontier_source_potential.csv").set_index("metric")
    parameters = pd.read_csv(PARAMETERS, dtype=str, keep_default_na=False)
    gates = parameters.loc[
        parameters["value_kind"].eq("missing_required"),
        ["parameter_id", "limitation"],
    ]
    generic = economics.loc[economics["scenario_id"].eq("C_generic_full_system")].iloc[
        0
    ]
    case_average = energy.loc[
        energy["scenario_id"].eq("C_case_cop_SRTV_total_output")
    ].iloc[0]

    gate_lines = "\n".join(
        f"- `{row.parameter_id}`: {row.limitation}"
        for row in gates.itertuples(index=False)
    )
    content = f"""# Phase D handoff: techno-economics and operational emissions

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

The broad sensitivity grid contains {len(sensitivity):,} cases. It preserves
unfavorable results: avoided operational emissions range from
{sensitivity["avoided_operational_co2e_kg_per_mwh"].min():.2f} to
{sensitivity["avoided_operational_co2e_kg_per_mwh"].max():.2f} kg CO2e per MWh
useful heat, while incremental NPC ranges from
USD {sensitivity["incremental_npc_usd2025"].min():,.0f} to
USD {sensitivity["incremental_npc_usd2025"].max():,.0f}.

On the normalized case-C energy-only calculation using the eGRID SRTV
total-output factor, avoided operational emissions are
{case_average["avoided_operational_co2e_kg"]:.2f} kg CO2e per MWh useful heat.
The generic full-system comparator has LCOH
USD {generic["lcoh_usd2025_per_mwh_th"]:.2f}/MWh-th; it is not a
Frontier-specific project estimate.

The measured Frontier workbook contains
{int(source.loc["valid_waste_heat_observations", "value"]):,} valid waste-heat
observations totaling
{source.loc["observed_waste_heat_energy", "value"]:,.1f} observed MWh-th.
{int(source.loc["missing_timestamps", "value"]):,} expected ten-minute
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

{gate_lines}

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
"""
    OUTPUT.write_text(content, encoding="utf-8")
    print(f"Wrote {OUTPUT.relative_to(ROOT)}.")


if __name__ == "__main__":
    main()
