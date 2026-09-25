# JCP claim architecture

This architecture governs the JCP rewrite. Claims are separated into directly
supported results, interpretive but defensible framing, and unsupported claims that
must be excluded.

## Level 1: directly supported

| Claim ID | Claim | Evidence status | Allowed use |
|---|---|---|---|
| L1_global_screening_bound | The frozen global model identifies positive one-unit relocation screening value in 93 of 94 canonical scenarios. | MODEL_OUTPUT | Report as a theoretical screening result. |
| L1_spatial_temporal_values | The matched-event spatial screening value is 777.7645 burden units/GJ; the same-location temporal value is 419.3294 burden units/GJ. | MODEL_OUTPUT | Compare frozen burden-space bounds. |
| L1_free_sink_pathology | The unconstrained human-burden objective selects an open-ocean mathematical sink: True. | MODEL_OUTPUT | Use as the no-free-sink diagnostic. |
| L1_measured_source | The measured Frontier source contains 49,869 valid intervals and 75,573.6 MWh-th. | FOUND_MEASURED | Use as measured source availability. |
| L1_zero_supported_endpoint | 0 practical modes are evidence-supported; 6 modes remain conditional; final endpoint status is EXCLUDED. | EVIDENCE_GATE | Report zero supported delivered-heat endpoint. |

## Level 2: interpretive but defensible

| Claim ID | Claim | Evidence status | Allowed use |
|---|---|---|---|
| L2_burden_shifting_framework | Optimizing local thermal burden can shift environmental burden when the receiving environment is treated as free. | MODEL_OUTPUT_PLUS_LITERATURE | Use as the JCP contribution framing. |
| L2_jcp_novelty | The contribution is a conservation-aware, evidence-gated thermal-allocation framework for detecting problem shifting. | LITERATURE_POSITIONING | Use as novelty claim if scoped to detection and gating. |

These claims require cautious wording. The contribution is detection and evidence
gating of environmental burden shifting in thermal-energy optimization, not proof
that any specific sink is safe or that a practical project is ready to deploy.

## Level 3: unsupported or prohibited

| Claim ID | Claim | Evidence status | Allowed use |
|---|---|---|---|
| L3_prohibited_safe_sink | A specific receiving sink is environmentally safe. | UNSUPPORTED | Exclude. |
| L3_prohibited_deployable_relocation | The study demonstrates deployable global heat relocation. | UNSUPPORTED | Exclude. |
| L3_prohibited_cost_or_lca | Case-specific LCOH, NPC, payback, or lifecycle CO2e is known. | NOT_FOUND_OR_BOUND_ONLY | Only identify as an evidence gap. |
| L3_prohibited_health_or_cooling | The burden proxy is mortality, morbidity, welfare, or planetary cooling. | PROHIBITED_BY_DESIGN | State the limitation explicitly. |

The following claims are prohibited in the manuscript, cover letter, graphical
abstract, highlights, and final handoff:

- A specific receiving sink is environmentally safe. — Any recommendation of ocean, cryosphere, land, or ambient discharge as safe.
- The study demonstrates deployable global heat relocation. — Do not state or imply operational global heat relocation.
- Case-specific LCOH, NPC, payback, or lifecycle CO2e is known. — Do not fabricate cost or embodied-emissions values.
- The burden proxy is mortality, morbidity, welfare, or planetary cooling. — Do not convert thermal-stress burden to health outcomes.

Additional prohibited overstatements:

- a specific environmentally safe sink;
- deployable global relocation;
- calibrated Frontier/ORNL annual operation;
- case-specific LCOH, NPC, or payback;
- case-specific lifecycle CO2e;
- health benefit;
- planetary cooling;
- space as a validated practical sink;
- comprehensive ecosystem-damage quantification.

## Permitted central claim

The permitted central claim is: a conservation-aware, evidence-gated framework can
detect when optimization of local thermal burden merely relocates environmental
burden to an unevidenced receiving pathway.
