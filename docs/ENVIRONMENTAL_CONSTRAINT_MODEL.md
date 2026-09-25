# Environmental receiving-capacity constraint model

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

| receiving_class | global_screening_role | practical_default | capacity_rule | required_evidence | rationale | source_ids |
| --- | --- | --- | --- | --- | --- | --- |
| populated_land | burden-weighted diagnostic | conditional_closed_loop_only | Useful heat must be bounded by measured demand or enclosed storage; ambient dumping receives no safety credit. | Demand trace, equipment limits, residual rejection, and local permits. | Population weights burden, not ecological capacity. | epa_npdes_thermal_framework |
| sparse_land | diagnostic_only | excluded_ambient_release | No positive practical ambient capacity is assigned. | Site-specific land, habitat, route, and local-climate assessment. | Population absence is not evidence of environmental safety. | orr_sensitive_environment |
| sensitive_ecosystem | unresolved_in_current_global_mask | excluded | Exclude unless project-level regulatory and ecological review authorizes the pathway. | Wetland, protected-species, habitat, and cumulative-impact review. | The case region contains wetlands and protected resources. | orr_sensitive_environment;tn_mixing_zone_protections |
| cryosphere | categorical_exclusion | excluded | No practical receiving capacity is assigned. | Not applicable; excluded by design. | Sea ice and snow are climate-sensitive and are not disposal sinks. | global_sea_ice_mask;global_snow_mask |
| inland_water | water_class_diagnostic_only | excluded_without_site_specific_permit | No capacity without flow, upstream temperature, permit limits, mixing-zone analysis, biology, and cumulative-load assessment. | NPDES pathway, receiving-water data, thermal model, and ecology. | Numeric temperature criteria are necessary but not sufficient. | epa_npdes_thermal_framework;tn_surface_water_temperature;tn_mixing_zone_protections |
| coastal_water | water_class_diagnostic_only | excluded_without_site_specific_permit | No generic capacity; require site hydrodynamics, ecology, permit, and cumulative-impact evidence. | Outfall, plume model, sensitive-species review, and permit limits. | Coastal mixing does not establish environmental safety. | epa_npdes_thermal_framework |
| open_ocean | theoretical_pathology_diagnostic | excluded | No engineering or environmental capacity is assigned. | A defined pathway, transport system, permits, and ocean-impact model. | The global mathematical sink is not a practical disposal option. | epa_npdes_thermal_framework;global_land_water_mask |

## Tennessee surface-water constraints

The registered Tennessee standard limits change relative to an upstream control
to 3 deg C, absolute water
temperature to 30.5 deg C, and
the rate of change to
2 deg C/hour.
Recognized trout waters have a
20 deg C maximum.
These values are criteria, not a generic heat-load allowance. Flow, upstream
temperature, an approved mixing zone, aquatic biology, and cumulative impacts
remain required. Therefore the model assigns zero admissible practical capacity
to a new surface-water discharge until those inputs exist.

The screening envelope is

\[
\Delta T_{allowed} =
\max\left(0,\min\left(3,30.5-T_{upstream}\right)\right),
\]

and a hydraulic heat-load calculation would then require

\[
P_{thermal} = \rho c_p \dot V \Delta T_{allowed}.
\]

This relation is not evaluated for Frontier because receiving-water flow,
upstream temperature, fluid properties, outfall geometry, and a permitted
mixing zone are not defined. Even with those inputs it would be a hydraulic
screen, not a permit or ecological safety demonstration.

## Sensitive-area rule

The Oak Ridge Reservation environmental report identifies
235 hectares of potential
wetlands and protected biological resources. Sparse land is therefore not
treated as an unconstrained sink. Any new tank or pipeline footprint requires a
route-level wetland, habitat, and protected-species review.

## Enclosed tank-storage capacity

For the generic tank sensitivity only,

\[
E = E_{ref} \frac{V}{V_{ref}}
    \frac{\Delta T}{\Delta T_{ref}},
\]

using the validated Danish catalogue reference capacity, volume, temperature
difference, medium, and availability. The source-backed grid spans
38.0 to 759.3 MWh-th. It is not a
Frontier-specific design because tank volume and the ORNL operating temperature
difference are missing.

## Frontier pathway assessment

| pathway_id | pathway_label | assessment_status | binding_constraints | conclusion |
| --- | --- | --- | --- | --- |
| A | Conventional rejection | baseline_only | Existing permit and cooling-system scope; residual stream not isolated. | Retain as the observed-system baseline; do not infer capacity for a new sink. |
| B | Same-location temporal storage and later reuse | conditional_open | Tank volume; operating delta T; demand trace; residual rejection. | Generic tank capacity can be screened, but no case-specific environmental recommendation is permitted. |
| C | Local direct reuse | conditional_open | Measured demand; heat-pump limits; residual returned to the existing rejection system. | Can be evaluated as a conditional least-assumption sensitivity; no environmental preference or project recommendation is permitted. |
| D | Near-distance transport without storage | excluded_pending_route_review | Undefined route, footprint, habitat clearance, hydraulics, and demand. | Exclude from practical recommendations until a route exists. |
| E | Storage plus near-distance transport | excluded_pending_design | All storage, route, footprint, demand, and residual-load gaps. | Exclude until storage and route designs are auditable. |

The two external-discharge alternatives are categorically excluded:

| pathway_id | pathway_label | assessment_status | conclusion |
| --- | --- | --- | --- |
| W | New direct surface-water thermal discharge | excluded | Not an admissible Frontier practical pathway. |
| G | New ambient land or atmospheric relocation | excluded | The global theoretical slab result is not a disposal recommendation. |

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

\[
L_{residual} = \sum_t P_{residual,t}\Delta t,
\]

with the same timestep accounting applied to useful delivery, storage losses,
and auxiliary energy.

## Open case-specific evidence

| parameter_id | parameter_name | unit | limitation |
| --- | --- | --- | --- |
| case_surface_water_flow_m3_s | candidate receiving-water flow | m3/s | Required to convert temperature criteria to a hydraulic heat-load bound. |
| case_surface_water_upstream_temperature_c | candidate receiving-water upstream temperature | deg_C | Required to evaluate the 30.5 deg C absolute criterion. |
| case_surface_water_mixing_zone | approved thermal mixing-zone definition | site_specific | No candidate outfall or approved mixing zone exists. |
| case_aquatic_biological_assessment | aquatic biological and cumulative-impact assessment | site_specific | Required before any practical thermal-discharge recommendation. |
| case_storage_volume_m3 | case-specific tank volume | m3 | Required to fix the practical storage capacity. |
| case_storage_operating_delta_temperature_k | case-specific storage temperature difference | K | ORNL return temperature and storage design remain unavailable. |
| case_route_sensitive_area_clearance | route and footprint environmental clearance | site_specific | No hot-water route or project footprint has been defined. |
| case_cumulative_residual_heat_mwh | annual residual rejected heat | MWh_th/year | Requires synchronized source, demand, storage, and outage dispatch. |

## Gate decision

The constraint model is implemented, and direct environmental dumping pathways
are excluded rather than assigned arbitrary low penalties. Gate 5 remains
**PARTIAL—OPEN** because case-specific storage design, route clearance, finite
dispatch, and cumulative residual rejection are unresolved. Local closed-loop
reuse is the environmentally preferred practical mode, but it is not yet an
operational recommendation.
