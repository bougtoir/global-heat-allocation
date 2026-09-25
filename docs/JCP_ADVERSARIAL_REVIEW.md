# JCP adversarial review

## Review scope and verdict

This review attacks the frozen JCP retargeting as an editor and as reviewers in
cleaner production, industrial ecology, environmental systems, thermal energy,
optimization, climate/heat transfer, and reproducibility/statistics. It assesses
the manuscript and submission assets generated from the frozen analysis; it does
not reopen the validated global calculations.

**Post-fix verdict: WEAK GO.** The manuscript has a defensible JCP contribution as
a conservation-aware method for detecting objective-boundary and evidence-gate
failures. Desk-rejection risk remains material because the global model is a
deliberately simplified screening calculation, the real pathway has zero supported
modes, and no case-specific LCA can be completed from the public evidence.

## Findings and disposition

| ID | Perspective | Severity | Attack | Classification | Disposition |
|---|---|---:|---|---|---|
| JCP-01 | Editor / cleaner production | High | “Environmental burden shifting” could imply quantified receiving damage, while the global model quantifies only population-weighted thermal burden. | CLARIFY | The abstract, introduction, methods, discussion, and novelty text now define detection as a structural risk flag: source relief plus conserved release to a receiver whose relevant impacts are omitted and unevidenced. The manuscript explicitly states that the flag does not quantify realized ecosystem damage. |
| JCP-02 | Editor | High | The two scales may look like unrelated studies joined after the fact. | CLARIFY | The discussion now states that the link is receiving-pathway logic, not calibration, and explicitly rejects interpreting Frontier as participating in the hypothetical global relocations. |
| JCP-03 | Optimization | High | A one-GJ pair search may be oversold as optimal transport or a deployable allocation solution. | REJECT WITH EVIDENCE | The methods already identify it as a marginal pair search, not a finite-mass transport plan; finite-capacity tests prevent indefinite scaling; operational relocation claims remain prohibited in the claim matrix. |
| JCP-04 | Environmental systems | High | Ocean and cryosphere exclusions are not environmental-impact models and cannot establish that land is safe. | MOVE TO LIMITATION | The manuscript treats these as categorical eligibility exclusions, states that constrained land remains unevidenced, and identifies pathway-specific ecological models as future work. |
| JCP-05 | Industrial ecology / LCA | High | Without a case-specific LCA, the paper may not support a cleaner-production conclusion. | REJECT WITH EVIDENCE | The paper does not claim a favorable cleaner-production endpoint. Missing lifecycle inventory is a binding gate, and the zero-supported endpoint is the reported result. Generic LCA values are not substituted for the absent case inventory. |
| JCP-06 | Thermal energy | High | The Frontier/ORNL pathway lacks synchronized demand, capture, route, hydraulics, auxiliary power, and storage design; therefore dispatch outputs may appear falsely project-specific. | CLARIFY | These cases remain explicitly conditional sensitivities. The text prohibits calibrated annual-operation, design-selection, cost, and performance claims. |
| JCP-07 | Reproducibility / statistics | Medium | Ninety-four canonical scenarios and nine structural scenarios could be mistaken for independent observations supporting inferential statistics. | FIX | The methods now state that scenarios are deterministic prespecified evaluations, not independent samples, and that counts, ranges, and sensitivity envelopes are descriptive without p-values or confidence intervals. |
| JCP-08 | Climate / heat transfer | Medium | The 100-m slab, instantaneous response, and six-hour grid are too simple for physical prediction. | MOVE TO LIMITATION | The model is consistently labeled a controlled marginal screening perturbation. Boundary-layer dynamics, advection, surface uptake, clouds, hydrology, and circulation feedback are explicitly excluded. |
| JCP-09 | Editor | Medium | “No free heat sink” is rhetorically broader than the evidence and could be read as denying radiative rejection or assimilative capacity. | CLARIFY | The title is retained, but the limitations define it narrowly as a no-automatic-zero-impact decision rule and explicitly acknowledge radiative cooling and regulated assimilation. |
| JCP-10 | Cleaner production | Medium | Zero supported modes may be judged “no applied result.” | REJECT WITH EVIDENCE | The applied result is the auditable classification of a measured source, bounded demand, six conditional modes, and the exact evidence preventing reclassification. The manuscript does not claim that recovery is impossible. |
| JCP-11 | Optimization / decision analysis | Medium | Combining burden units, MWh-th, USD, and CO2e would create a false ranking. | REJECT WITH EVIDENCE | The waterfall preserves unit separation, later evidence stages are categorical, and no composite sustainability score is created. |
| JCP-12 | Climate / heat transfer | Medium | Discussion of atmosphere or space could become speculative and distract from JCP relevance. | CLARIFY | Radiative concepts remain device- and condition-specific; observed outgoing radiation is not treated as incremental disposal efficiency; space is not a validated sink. |
| JCP-13 | Figures and tables | Medium | The cascade could visually imply that categorical evidence gates are quantitatively commensurate with burden-space values. | FIX | Figure 3 visually separates burden-space screening from physical-energy evidence gates and states that later stages are not converted into burden units, MWh-th, USD, or CO2e. |
| JCP-14 | Reproducibility | Medium | Reference ordering, unsupported hard-coded values, or stale output packaging could undermine auditability. | FIX | References resolve in first-appearance order, the main list contains 48 verified records, manuscript numbers resolve through the value registry, and archive integrity is tested. |
| JCP-15 | Editor | Low | The title and graphical abstract could imply an engineering recommendation. | CLARIFY | Both emphasize validation of the receiving pathway and show zero evidence-supported modes; no sink or mode is recommended. |
| JCP-16 | Reproducibility | Low | Author-controlled metadata are incomplete. | MOVE TO LIMITATION | Affiliation, postal address, funding, competing interests, repository DOI, and final live-guide confirmation remain explicit `AUTHOR ACTION` items and block actual submission. |

## Reviewer-specific bottom lines

### JCP editor / desk review

The manuscript fits JCP only if read as a cleaner-production boundary-control
method, not as a climate-engineering proposal. The revised framing is adequate but
the negative applied endpoint and absence of LCA remain prominent desk risks.

### Cleaner production and industrial ecology

The strongest contribution is preventing source-boundary relief from being labeled
cleaner production before the receiving pathway is validated. The work complements
LCA and industrial ecology; it does not replace either.

### Environmental systems

The manuscript diagnoses missing receptors but does not quantify ecosystem damage.
That distinction is now explicit and must remain intact through submission.

### Thermal energy

The measured source is useful, but the practical modes are sensitivities rather
than designs. No case-specific performance, cost, route, storage, or lifecycle
recommendation is supportable.

### Optimization

The free-sink result is an objective-specification diagnostic. It is not a
finite-mass transport solution, and the exact sink coordinate is not a robust
decision.

### Climate and heat transfer

The global model is deliberately reduced order. Its acceptable role is to expose
objective behavior under conservation, not to predict a real atmospheric release.

### Reproducibility and statistics

The frozen values, immutable source snapshots, deterministic builds, unit
separation, and claim matrix are strengths. Scenario results are descriptive
sensitivity outputs rather than a statistical sample.

## Remaining submission blockers

- Author affiliation and postal address.
- Confirmed funding statement.
- Confirmed competing-interest declaration.
- Permanent DOI for the archived final repository release.
- Final check against the live JCP guide immediately before submission.
