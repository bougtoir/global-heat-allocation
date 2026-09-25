# JCP analysis freeze

## Freeze identity

- JCP retargeting starts from repository commit
  `c81a2469859b069d99291d413b757d971f49ce90`.
- The frozen `global_heat_allocation` tree is
  `0ca0d594f7f22e5dce3f5cc75084a16b5051660b`.
- The last analytical-content commit before the retargeting pass is
  `aa2a0a98` (`global_heat: finalize two-scale evidence package`).
- The earlier canonical-analysis freeze is `365f144f`, and the validated
  baseline inventory is `8d9667de`.

The JCP pass may change framing, literature, derived evidence classifications,
figures, manuscript text, and submission assets. It must not change validated
global analyses, structural replication, measured Frontier source values,
environmental exclusions, finite-dispatch sensitivities, or practical-mode
results merely to improve journal fit.

## Frozen analytical outputs

| Domain | Canonical artifact | Frozen statement |
|---|---|---|
| Global marginal screening | `results/canonical/one_unit_allocations.csv` | 94 canonical scenarios; 93 relocation-positive |
| Matched spatial/temporal screening | `results/canonical/matched_event_allocations.csv` | 777.7645 burden units/GJ spatial; 419.3294 burden units/GJ temporal |
| Finite quantity | `results/canonical/finite_q_sensitivity.csv` | 1, 1,000, and 100,000 GJ feasible; 1,000,000 GJ infeasible under the local cap |
| Structural replication | `results/tables/structural_replication.csv` | 9 prespecified scenarios retain positive constrained spatial value, sink non-uniqueness, and pathological unrestricted sinks |
| Measured source | `data/raw/real_heat_cases/frontier_figshare_v4_20260924T115656Z/frontier_hpc_facility_data_v4.xlsx` | 49,869 valid 10-minute observations, 2,691 unavailable timestamps, and 75,573.6 MWh-th observed source heat |
| Finite dispatch | `results/dispatch/finite_dispatch_summary.csv` | 7 demand-bound sensitivity scenarios; all 31 validation checks pass |
| Environmental eligibility | `results/environmental_constraints/frontier_pathway_assessment.csv` | Unsupported ambient, water, ocean, and cryosphere disposal pathways remain excluded |
| Global-to-real waterfall | `results/tables/global_to_real_constraint_waterfall.csv` | Burden-space and physical-energy branches remain separate; no practical burden-space endpoint is quantified |
| Conditional modes | `results/techno_economic/practical_pareto_modes.csv` | 6 conditional modes and 0 supported practical modes |
| Claim traceability | `provenance/manuscript_values.csv` | 76 values with source hashes, selectors, derivations, eligibility, and claim limits |

## Frozen headline interpretation

1. Heat is conserved. Removal from a source location is not disappearance of
   energy or environmental consequence.
2. A population-weighted thermal-stress objective can make low-population,
   ocean, cryosphere, or otherwise remote receiving regions appear
   mathematically attractive without establishing environmental safety.
3. The same-location temporal screening value is 53.9147% of the matched-event
   spatial screening value; this is a burden-space comparison, not a project
   efficiency or environmental-damage score.
4. Measured Frontier heat is an auditable source input, while the ORNL
   receiving evidence supplies summary bounds rather than a synchronized
   demand trace.
5. The finite-dispatch branches are conditional demand-bound sensitivities,
   not observed annual Frontier-to-ORNL operation.
6. Zero supported practical modes is a negative evidence result. It must not be
   converted into a recommendation, concealed, or repaired with generic
   pseudo-precision.

## Frozen evidence boundaries

- Low population is not environmental safety.
- Redistribution is not planetary cooling.
- Population-weighted thermal-stress burden is not mortality, morbidity,
  welfare, currency, total environmental burden, or ecosystem damage.
- Observed outgoing longwave radiation is descriptive context, not a validated
  incremental heat-disposal pathway or efficiency.
- Space is not a practical sink without a specified physical pathway,
  achievable flux, efficiency, system boundary, and terrestrial consequences.
- No case-specific LCOH, NPC, payback, lifecycle CO2e, route performance,
  hydraulic design, storage design, or calibrated annual delivery may be
  claimed from the current evidence.

## Frozen file hashes

| Artifact | SHA-256 |
|---|---|
| `provenance/manuscript_values.csv` | `80e5d7683bb6d9ba6fe2555280f6da0132baba870712eef7bcc2e080fbc66627` |
| `results/tables/global_to_real_constraint_waterfall.csv` | `d5d9cc8e299bc928065866c1e0fca2cbbf09d7d4c82df1e294caeb0bad890cb8` |
| `results/techno_economic/practical_pareto_modes.csv` | `a525d3903c66bc15b90052c8a83b971369c7f8d887e82444ad66728e07a43796` |
| Frontier source workbook | `56a48dd66382896890dfc2e4940ec90f894bb85795ee8e85ea2708dda05796bf` |

## Validated QC at freeze

- Ruff check passed.
- Ruff format check passed for 71 files.
- Pytest passed: 78 tests.
- The submission archive passed exact ZIP integrity checking.
- The inline manuscript and standalone decision report passed
  DOCX-to-PDF conversion, text extraction, and visual pagination review.
- PR 494 was mergeable, CI passed, and the public synchronized audit matched
  the local artifact hash.

## Narrow conditions for reopening analysis

Analysis may be reopened only when one of the following is documented before
editing:

1. a reproducible defect in a frozen equation, implementation, input mapping,
   unit conversion, balance check, or reported number;
2. a mismatch between a manuscript claim and its canonical source;
3. corruption or non-reproducibility of a frozen artifact;
4. a minimal JCP-specific summary that is deterministically derived from
   existing canonical outputs without changing them.

Any reopening must identify the defect or derivation, limit the rerun to
affected downstream outputs, preserve previous artifacts and hashes, and
update provenance. Journal fit, rhetorical appeal, or a desire for a different
result is not a valid reason to reopen the analysis.
