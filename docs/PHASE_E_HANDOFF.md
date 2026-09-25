# Phase E handoff: environmental receiving capacity

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

The generic storage grid contains 9 source-backed sensitivity
points spanning 38.0–759.3 MWh-th. It does
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

| parameter_id | parameter_name | limitation |
| --- | --- | --- |
| case_surface_water_flow_m3_s | candidate receiving-water flow | Required to convert temperature criteria to a hydraulic heat-load bound. |
| case_surface_water_upstream_temperature_c | candidate receiving-water upstream temperature | Required to evaluate the 30.5 deg C absolute criterion. |
| case_surface_water_mixing_zone | approved thermal mixing-zone definition | No candidate outfall or approved mixing zone exists. |
| case_aquatic_biological_assessment | aquatic biological and cumulative-impact assessment | Required before any practical thermal-discharge recommendation. |
| case_storage_volume_m3 | case-specific tank volume | Required to fix the practical storage capacity. |
| case_storage_operating_delta_temperature_k | case-specific storage temperature difference | ORNL return temperature and storage design remain unavailable. |
| case_route_sensitive_area_clearance | route and footprint environmental clearance | No hot-water route or project footprint has been defined. |
| case_cumulative_residual_heat_mwh | annual residual rejected heat | Requires synchronized source, demand, storage, and outage dispatch. |

## Decision

**NO-GO remains in force.** Phase E closes the model-definition portion of the
environmental gate, but cumulative environmental load cannot be evaluated until
finite repeated dispatch and case design are available.

## Rebuild

```bash
make environmental-constraints
make phase-e-handoff
```
