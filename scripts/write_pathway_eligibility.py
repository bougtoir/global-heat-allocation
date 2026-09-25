# ruff: noqa: E501
"""Write practical pathway eligibility from the case-specific evidence ledger."""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "provenance" / "case_specific_evidence.csv"
OUTPUT = ROOT / "docs" / "PATHWAY_ELIGIBILITY.md"

REQUIRED_EVIDENCE = {
    "ornl_receiving_hourly_demand_profile": "NOT_FOUND",
    "hydraulic_network_design_inputs": "NOT_FOUND",
    "receiving_water_flow_temperature": "NOT_FOUND",
    "approved_mixing_zone_outfall": "NOT_FOUND",
    "equipment_embodied_co2e": "NOT_FOUND",
    "cost_and_price_year": "FOUND_BOUND_ONLY",
    "source_capture_efficiency": "FOUND_BOUND_ONLY",
    "balance_of_plant_auxiliary_electricity": "FOUND_BOUND_ONLY",
    "case_storage_design": "NOT_FOUND",
}


def _status(evidence: pd.DataFrame, evidence_id: str) -> str:
    matches = evidence.loc[evidence["evidence_id"].eq(evidence_id), "status"]
    if len(matches) != 1:
        raise ValueError(f"Expected one evidence row for {evidence_id}")
    return str(matches.iloc[0])


def _validate_evidence(evidence: pd.DataFrame) -> None:
    for evidence_id, expected in REQUIRED_EVIDENCE.items():
        actual = _status(evidence, evidence_id)
        if actual != expected:
            raise ValueError(
                f"Unexpected status for {evidence_id}: {actual}; expected {expected}"
            )


def main() -> None:
    evidence = pd.read_csv(EVIDENCE).fillna("")
    _validate_evidence(evidence)

    text = """# Practical pathway eligibility

This document classifies practical Frontier-to-ORNL heat-management claims after
the authoritative case-specific evidence search in
`provenance/case_specific_evidence.csv`.

Eligibility statuses:

- `SUPPORTED`: directly supported by measured or auditable case-specific public
  evidence.
- `CONDITIONAL`: permitted only as an explicitly labeled bound or generic
  sensitivity, not as a measured Frontier-specific project result.
- `EXCLUDED`: not defensible under the current public evidence ledger.

## Classification table

| Pathway or claim | Eligibility | Evidence basis | Allowed use |
|---|---:|---|---|
| Measured Frontier source heat quantity, temperature grade, and 10-minute temporal profile | `SUPPORTED` | `frontier_source_timeseries` is `FOUND_MEASURED`. | Use as measured source input with explicit unavailable intervals. |
| ORNL demand summary evidence | `SUPPORTED` | `ornl_receiving_demand_summary` is `FOUND_MEASURED`. | Use average/maximum demand summaries as bounds and narrative evidence. |
| Observed or calibrated annual Frontier-to-ORNL useful-heat delivery | `EXCLUDED` | `ornl_receiving_hourly_demand_profile` is `NOT_FOUND`. | Do not claim observed/calibrated annual delivery; use demand-bound sensitivities only. |
| Constant lower/upper demand-bound dispatch | `CONDITIONAL` | Source is measured, but the receiving-demand trace is missing. | Keep as explicitly bounded sensitivity, not observed operation. |
| Calibrated Frontier hot-water thermal-network transport | `EXCLUDED` | `hydraulic_network_design_inputs` is `NOT_FOUND`; `route_length_and_path` is only `FOUND_BOUND_ONLY`. | Do not claim route-specific losses, pumping energy, or network CAPEX. |
| Generic near-site heat-pump transport concept | `CONDITIONAL` | Existing steam distance and map context bound locality but do not define the new route. | Discuss only as a conceptual/site-proximity sensitivity. |
| New external receiving-water residual-heat discharge | `EXCLUDED` | `receiving_water_flow_temperature` and `approved_mixing_zone_outfall` are `NOT_FOUND`. | Do not calculate or claim site-specific receiving-water thermal capacity. |
| Ambient land, coastal water, open-ocean, inland-water, or cryosphere disposal | `EXCLUDED` | Phase E excludes these without site-specific safety evidence; cryosphere is categorically excluded. | Do not use as practical supported endpoints. |
| Case-specific heat-recovery storage design | `EXCLUDED` | `case_storage_design` is `NOT_FOUND`. | Do not present tank volume or operating Delta-T as a Frontier/ORNL design. |
| Generic or formula storage dispatch | `CONDITIONAL` | Storage parameters are generic comparator inputs, not case design evidence. | Keep as explicitly labeled storage sensitivity. |
| Heat-pump COP and three-unit capacity bound | `CONDITIONAL` | `heat_pump_cop_capacity` is `FOUND_DERIVABLE`. | Use for bounded conversion/dispatch, with missing BOP and network evidence stated. |
| Frontier source-capture efficiency into a new recovery exchanger | `EXCLUDED` | `source_capture_efficiency` is only `FOUND_BOUND_ONLY`. | Do not treat 97%-99% cooling-loop heat removal as measured recovery capture. |
| Existing accessory/cooling power as project auxiliary electricity | `EXCLUDED` | `balance_of_plant_auxiliary_electricity` is only `FOUND_BOUND_ONLY`. | Do not substitute facility accessory power for incremental heat-recovery auxiliary load. |
| Case-specific lifecycle CO2e | `EXCLUDED` | `equipment_embodied_co2e` is `NOT_FOUND`. | Do not claim lifecycle CO2e for the project. |
| Operational emissions comparator | `CONDITIONAL` | Operational emission factors exist, but auxiliary/project inventory is incomplete. | Keep as generic operational sensitivity only. |
| Frontier-specific LCOH, NPC, or payback | `EXCLUDED` | `cost_and_price_year` is only `FOUND_BOUND_ONLY`. | Do not claim Frontier-specific economics from equipment-only cost. |
| Equipment-only cost context | `CONDITIONAL` | ORNL reports a unit capital cost but lacks price year and balance-of-plant scope. | Use only as partial cost context. |
| Route/footprint environmental clearance | `EXCLUDED` | `route_footprint_environmental_clearance` is only `FOUND_BOUND_ONLY`. | Do not claim route clearance or absence of ecological conflict. |

## Gate implications

- No defensible route/hydraulics means no calibrated thermal-network transport
  claim.
- No outfall, flow, or upstream-temperature evidence means external
  receiving-water heat discharge remains excluded.
- No lifecycle inventory means no case-specific lifecycle CO2e.
- No complete installed-cost evidence means no Frontier-specific LCOH, NPC, or
  payback.
- No auditable receiving-demand trace means no observed or calibrated annual
  Frontier-to-ORNL delivery claim.

Generic comparator analyses may remain only when labeled as generic
sensitivities or upper/lower bounds.
"""

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    temporary = OUTPUT.with_name(f".{OUTPUT.name}.tmp")
    temporary.write_text(text, encoding="utf-8")
    with temporary.open("r+", encoding="utf-8") as handle:
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, OUTPUT)
    print(f"Wrote {OUTPUT.relative_to(ROOT)}.")


if __name__ == "__main__":
    main()
