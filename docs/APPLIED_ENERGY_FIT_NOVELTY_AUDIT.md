# Post-freeze Applied Energy fit and novelty audit

## Decision

**NO-GO for submission to Applied Energy at the current evidence state.**

The topic fits the journal's interests in optimal energy-resource use, thermal
storage, heat decarbonization, energy-system optimization, and environmental
consequences. The current evidence does not yet bridge research to
implementation strongly enough for the journal's applied-energy emphasis:
0 practical mode is supported, while all 6
evaluated practical modes remain conditional.

## Defensible contribution after the value freeze

The strongest contribution is a reproducible **two-scale constraint-attrition
framework**:

1. a conserved-heat global marginal screening bound;
2. an auditable measured waste-heat source and documented receiving-demand
   bounds;
3. an explicit waterfall showing where environmental, geographic, technology,
   storage, demand, and dispatch evidence removes practical claim eligibility;
4. a mode comparison that retains negative and conditional outcomes.

The frozen global values are 777.7645 burden units/GJ for matched-event
spatial screening and 419.3294 burden units/GJ for same-location temporal
screening (53.9147% of the spatial bound). The measured Frontier
source contributes 75,573.6 MWh-th over valid intervals. These quantities
belong to different spaces and must not be collapsed into a single efficiency,
welfare, or monetized-benefit ratio.

The defensible novelty is **not** a first global heat-redistribution model, a
new optimal-transport algorithm, a safe planetary heat-disposal design, or a
completed Frontier-to-ORNL project appraisal. It is the auditable comparison
between a theoretical conserved-allocation bound and the evidence loss incurred
when attempting to instantiate that bound in a real thermal-energy pathway.

## Reviewer-perspective critical assessment

### 1. Manuscript

- **Novelty:** The rewritten manuscript now makes the two-scale
  constraint-attrition framework, rather than a geographically extreme
  optimum, the principal contribution.
- **Focus:** The real-case evidence chain, constraint waterfall, and zero
  supported practical modes are now central.
- **Logic:** Burden-space screening and physical-energy dispatch remain
  explicitly separate; no conversion, monetization, or welfare bridge is used.
- **Methods gap:** The practical case lacks synchronized measured receiving
  demand and an integrated project design.
- **Conclusion alignment:** The conclusion retains the negative practical
  endpoint and does not recommend an unsupported project.

### 2. Statistical and analytical design

- The canonical scenario count is a deterministic model grid, not a sample
  size; inferential p-values are neither available nor appropriate.
- Structural replication supports persistence across prespecified products,
  years, grids, population surfaces, and metrics, but it does not quantify
  epistemic uncertainty comprehensively.
- The finite-dispatch cases are demand-bound sensitivities, not validation
  against observed coincident operation.
- Co-optimal sinks and near-optimal sets must be emphasized to avoid presenting
  one representative coordinate as uniquely optimal.
- Effect sizes, feasible ranges, infeasible cases, and balance diagnostics
  should be reported without converting the thermal-stress proxy to mortality,
  welfare, or currency.

### 3. Figures and tables

- Six focused main figures now prioritize the two-scale framework, matched
  allocation bounds, measured source and demand bounds, constraint waterfall,
  and practical mode decision.
- Redundant global maps, safety ablation, penalty sweeps, and trajectory
  diagnostics are in the supplement.
- Theoretical burden-space and physical-energy panels remain separate.
- All six practical modes are shown as conditional without implying a
  supported preferred design.

### 4. Reproducibility

- Strengths: persisted public inputs, immutable snapshots, checksums, generated
  result tables, a manuscript-value ledger, deterministic rebuild targets, and
  automated tests.
- The current evidence ledger contains 3 measured, 1
  derivable, 5 bound-only, and 7 not-found case items.
- The rewritten package passed a clean generation, lint, formatting, test,
  archive-integrity, DOCX-to-PDF rendering, figure/table citation, and visual
  pagination check.
- Remaining reproducibility and submission risks are the live author-guide
  recheck, permanent repository DOI, and author-controlled metadata.

### 5. Strength of claims

- **Supported:** conserved marginal screening, matched spatial/temporal
  comparison, structural persistence, measured Frontier source availability,
  documented ORNL demand summary bounds, and conditional dispatch behavior.
- **Conditional only:** local reuse, storage, transport, operational emissions,
  and generic economics.
- **Excluded:** calibrated annual Frontier-to-ORNL delivery, route-specific
  network performance, case-specific LCOH/NPC/payback, lifecycle CO2e,
  environmentally admissible external rejection, mortality benefit, and
  planetary cooling.

## Prioritized revisions

| Priority | Finding | Fatality | Expected effect | Feasibility | Required action |
|---|---|---|---|---|---|
| Mandatory before submission | No practical mode is supported by case-specific evidence. | High major-revision risk | High | New data needed for closure | Retain NO-GO unless synchronized demand and integrated route, capture, auxiliary, storage, and environmental evidence appear. |
| Mandatory before submission | The live author guide and submission metadata remain incomplete. | Administrative rejection risk | High | Author action required | Recheck the live guide and confirm authorship, affiliation, funding, conflicts, publication route, repository DOI, reviewers, and declarations. |
| High | Applied Energy fit remains vulnerable without a realizable integrated case. | High desk-reject risk | High | Requires new evidence or journal repositioning | Position the article as a methods-and-evidence contribution or target a journal that accepts a transparent negative case result. |
| High | Receiving demand is not synchronized with the measured source. | Major-revision risk | High | Requires external data | Acquire or reconstruct an auditable hourly or sub-hourly demand trace before claiming calibrated useful-heat delivery. |
| Medium | Structural scenarios do not exhaust model-form uncertainty. | Moderate revision risk | Medium | Feasible to disclose | Describe replication as prespecified structural sensitivity, not probabilistic uncertainty quantification. |
| Medium | Conditional storage modes use non-case-specific design inputs. | Moderate revision risk | Medium | Feasible to disclose; closure requires design evidence | Keep storage results as sensitivities and do not identify a preferred design. |
| Optional | A synchronized demand trace and project design could calibrate the applied case. | Not required for a methods-focused fallback | Potentially high | Requires external data | Acquire an auditable load profile and route/equipment design only if pursuing a stronger Applied Energy claim. |

## Journal-fit conclusion

The study is thematically relevant to Applied Energy, but the present evidence
supports a **theoretical screening plus transparent practical-gate diagnosis**,
not a realizable heat-allocation project. The rewritten manuscript is now a
coherent methods-and-evidence paper with the negative constraint result at its
center. The stronger claim that a material fraction of the global value
survives in a physically and economically realizable system remains unproven;
therefore the post-rewrite journal-fit gate does not close.

The final submission audit must re-read the live Applied Energy guide because
the retained guide-for-authors acquisition is explicitly incomplete due to a
Cloudflare challenge.
