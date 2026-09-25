"""Write the Phase E environmental constraint model and handoff documents."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
METADATA = ROOT / "data" / "metadata"
RESULTS = ROOT / "results" / "environmental_constraints"
MODEL_OUTPUT = ROOT / "docs" / "ENVIRONMENTAL_CONSTRAINT_MODEL.md"
HANDOFF_OUTPUT = ROOT / "docs" / "PHASE_E_HANDOFF.md"


def _markdown_table(data: pd.DataFrame) -> str:
    columns = list(data.columns)
    header = "| " + " | ".join(columns) + " |"
    divider = "| " + " | ".join("---" for _ in columns) + " |"
    rows = [
        "| "
        + " | ".join(
            str(value).replace("|", "\\|").replace("\n", " ") for value in record
        )
        + " |"
        for record in data.itertuples(index=False, name=None)
    ]
    return "\n".join([header, divider, *rows])


def main() -> None:
    parameters = pd.read_csv(
        METADATA / "environmental_parameters.csv",
        dtype=str,
        keep_default_na=False,
    )
    receiving = pd.read_csv(
        RESULTS / "receiving_class_constraints.csv",
        dtype=str,
        keep_default_na=False,
    )
    pathways = pd.read_csv(
        RESULTS / "frontier_pathway_assessment.csv",
        dtype=str,
        keep_default_na=False,
    )
    storage = pd.read_csv(RESULTS / "storage_capacity_sensitivity.csv")
    indexed = parameters.set_index("parameter_id")
    missing = parameters.loc[parameters["value_kind"].eq("missing_required")]
    external = pathways.loc[
        pathways["new_external_thermal_discharge"].eq("yes"),
        ["pathway_id", "pathway_label", "assessment_status", "conclusion"],
    ]
    practical = pathways.loc[
        pathways["pathway_id"].isin(["A", "B", "C", "D", "E"]),
        [
            "pathway_id",
            "pathway_label",
            "assessment_status",
            "binding_constraints",
            "conclusion",
        ],
    ]
    minimum_capacity = storage["capacity_mwh_th"].min()
    maximum_capacity = storage["capacity_mwh_th"].max()

    model = f"""# Environmental receiving-capacity constraint model

## Scope and claim boundary

This Phase E model replaces population-only safety logic with conservative
capacity or exclusion rules. It does not claim that any new environmental heat
sink is safe. Global atmospheric-slab results remain theoretical diagnostics.
Practical Frontier pathways are restricted to closed-loop heat service or
enclosed storage; residual heat must be returned to the existing rejection
system unless a separately permitted and assessed receiving pathway exists.

## Constraint hierarchy

1. Avoid a new external thermal discharge.
2. Bound useful heat by measured receiving demand.
3. Bound enclosed storage by physical volume, operating temperature difference,
   charge/discharge power, and temperature limits.
4. Track residual rejection and storage losses at every dispatch timestep.
5. Exclude direct release to land, cryosphere, inland water, coastal water, or
   open ocean when site-specific capacity evidence is absent.

## Receiving classes

{_markdown_table(receiving)}

## Tennessee surface-water constraints

The registered Tennessee standard limits change relative to an upstream control
to {indexed.loc["tn_max_temperature_change_c", "value"]} deg C, absolute water
temperature to {indexed.loc["tn_max_water_temperature_c", "value"]} deg C, and
the rate of change to
{indexed.loc["tn_max_temperature_rate_c_per_hour", "value"]} deg C/hour.
Recognized trout waters have a
{indexed.loc["tn_trout_water_max_temperature_c", "value"]} deg C maximum.
These values are criteria, not a generic heat-load allowance. Flow, upstream
temperature, an approved mixing zone, aquatic biology, and cumulative impacts
remain required. Therefore the model assigns zero admissible practical capacity
to a new surface-water discharge until those inputs exist.

The screening envelope is

\\[
\\Delta T_{{allowed}} =
\\max\\left(0,\\min\\left(3,30.5-T_{{upstream}}\\right)\\right),
\\]

and a hydraulic heat-load calculation would then require

\\[
P_{{thermal}} = \\rho c_p \\dot V \\Delta T_{{allowed}}.
\\]

This relation is not evaluated for Frontier because receiving-water flow,
upstream temperature, fluid properties, outfall geometry, and a permitted
mixing zone are not defined. Even with those inputs it would be a hydraulic
screen, not a permit or ecological safety demonstration.

## Sensitive-area rule

The Oak Ridge Reservation environmental report identifies
{indexed.loc["orr_potential_wetland_area_ha", "value"]} hectares of potential
wetlands and protected biological resources. Sparse land is therefore not
treated as an unconstrained sink. Any new tank or pipeline footprint requires a
route-level wetland, habitat, and protected-species review.

## Enclosed tank-storage capacity

For the generic tank sensitivity only,

\\[
E = E_{{ref}} \\frac{{V}}{{V_{{ref}}}}
    \\frac{{\\Delta T}}{{\\Delta T_{{ref}}}},
\\]

using the validated Danish catalogue reference capacity, volume, temperature
difference, medium, and availability. The source-backed grid spans
{minimum_capacity:.1f} to {maximum_capacity:.1f} MWh-th. It is not a
Frontier-specific design because tank volume and the ORNL operating temperature
difference are missing.

## Frontier pathway assessment

{_markdown_table(practical)}

The two external-discharge alternatives are categorically excluded:

{_markdown_table(external)}

## Cumulative-load accounting required for Phase G

Finite dispatch must report at minimum:

- annual residual rejected heat, MWh-th/year;
- peak residual rejection, MW-th;
- annual storage standing loss, MWh-th/year;
- heat-pump and auxiliary electricity;
- storage state of charge and temperature limits;
- for any permitted water discharge, discharge temperature, receiving-water
  flow and upstream temperature, mixing-zone compliance, and cumulative impact.

No annual residual-load value is reported in Phase E because synchronized
source, demand, storage, and outage dispatch does not yet exist.
The required annual accounting identity is

\\[
L_{{residual}} = \\sum_t P_{{residual,t}}\\Delta t,
\\]

with the same timestep accounting applied to useful delivery, storage losses,
and auxiliary energy.

## Open case-specific evidence

{_markdown_table(missing[["parameter_id", "parameter_name", "unit", "limitation"]])}

## Gate decision

The constraint model is implemented, and direct environmental dumping pathways
are excluded rather than assigned arbitrary low penalties. Gate 5 remains
**PARTIAL—OPEN** because case-specific storage design, route clearance, finite
dispatch, and cumulative residual rejection are unresolved. Local closed-loop
reuse is the environmentally preferred practical mode, but it is not yet an
operational recommendation.
"""
    MODEL_OUTPUT.write_text(model, encoding="utf-8")

    handoff = f"""# Phase E handoff: environmental receiving capacity

## Scope completed

Phase E defines conservative receiving-class rules for populated land, sparse
land, sensitive ecosystems, cryosphere, inland water, coastal water, and open
ocean. It registers EPA, Tennessee, and Oak Ridge environmental sources,
separates regulatory criteria from physical capacity, excludes unsupported
external thermal sinks, and provides a source-backed generic tank-capacity
sensitivity.

## Reproducible outputs

- `data/metadata/environmental_parameter_sources.csv`
- `data/metadata/environmental_parameters.csv`
- `results/environmental_constraints/receiving_class_constraints.csv`
- `results/environmental_constraints/frontier_pathway_assessment.csv`
- `results/environmental_constraints/storage_capacity_sensitivity.csv`
- `docs/ENVIRONMENTAL_CONSTRAINT_MODEL.md`

The generic storage grid contains {len(storage)} source-backed sensitivity
points spanning {minimum_capacity:.1f}–{maximum_capacity:.1f} MWh-th. It does
not define a Frontier tank.

## Practical pathway decision

- New surface-water, coastal, ocean, and ambient-land thermal disposal are
  excluded without site-specific permits, physical capacity, ecological review,
  and cumulative-impact evidence.
- Pathway C local reuse is retained only as a closed-loop conditional pathway;
  residual heat returns to the existing rejection system.
- Pathways B, D, and E remain blocked by tank, route, demand, or footprint
  evidence.

## Open evidence gates

{_markdown_table(missing[["parameter_id", "parameter_name", "limitation"]])}

## Decision

**NO-GO remains in force.** Phase E closes the model-definition portion of the
environmental gate, but cumulative environmental load cannot be evaluated until
finite repeated dispatch and case design are available.

## Rebuild

```bash
make environmental-constraints
make phase-e-handoff
```
"""
    HANDOFF_OUTPUT.write_text(handoff, encoding="utf-8")
    print("Wrote Phase E environmental model and handoff documents.")


if __name__ == "__main__":
    main()
