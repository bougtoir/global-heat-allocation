# NO-GO gate closure plan

## Purpose

This plan governs the transition from the current global theoretical screening
study to a two-scale *Applied Energy* paper. Gate status is evidence based. A
gate is not closed by adding narrative, weakening an acceptance criterion, or
substituting an arbitrary scenario for auditable data.

The two scales are:

1. a global conserved-heat allocation bound; and
2. a real thermal-energy case with an auditable source, temperature grade,
   time profile, demand or receiving pathway, technology, losses, finite
   operation, costs, emissions, and environmental constraints.

The current framework remains a prescribed atmospheric-slab screening model.
It is not a heat network, health-effect model, environmental-safety
demonstration, or planetary-cooling mechanism.

## Verified baseline

The canonical machine-readable outputs currently establish:

- 94 allocation scenarios, of which 93 favor relocation over no relocation;
- a matched-event spatial screening bound of 777.7645 burden units/GJ;
- a same-location 18-hour value of 419.3294 burden units/GJ, equal to 53.9147%
  of that event-specific spatial bound;
- 422 exactly co-optimal spatial candidates and 808 candidates within 1% of
  the matched-event optimum;
- loss of local feasibility at 1,000,000 GJ under the configured 0.1 K
  perturbation cap; and
- representative ocean, cryosphere, and zero-population sinks when relevant
  constraints are absent.

These values are conditional model outputs, not technology performance or
policy recommendations.

## Gate matrix

### Gate 1 — Real heat source and demand or receiving pathway

- **Current evidence:** No operational heat stream is represented.
- **Missing evidence:** Auditable heat quantity, temperature grade, time
  profile, location, baseline rejection, and demand or defensible receiving
  pathway.
- **Proposed analysis:** Compare multiple public-data candidates and select one
  primary case using prespecified criteria. Add a contrasting case only if the
  same evidentiary standard can be met.
- **Required data:** Public plant/system records, measured or reconstructable
  load, temperatures, operating schedule, location, and local weather or
  demand context.
- **Acceptance criterion:** At least one case can be reconstructed without a
  proprietary indispensable input and supports finite hourly dispatch.
- **Fallback:** Narrow the paper to a theoretical methods contribution and
  retain NO-GO for *Applied Energy*.
- **Essential for Applied Energy:** Yes.

### Gate 2 — Technology calibration

- **Current evidence:** Transport and storage are represented by abstract
  burden penalties and lag limits.
- **Missing evidence:** Case-specific technology, efficiency, standing and
  transport losses, charge/discharge power, storage capacity, pumping or fan
  energy, heat-pump COP where applicable, lifetime, and degradation.
- **Proposed analysis:** Compare baseline rejection, same-location temporal
  storage or reuse, local reuse, plausible-distance transport, and combined
  storage/transport using verified parameter ranges.
- **Required data:** Standards, government reports, peer-reviewed engineering
  studies, and manufacturer data only when methods and conditions are
  transparent.
- **Acceptance criterion:** Every parameter is sourced, transparently derived,
  or explicitly labeled as a sensitivity variable; energy balances close.
- **Fallback:** Exclude unsupported modes rather than assign invented
  parameters.
- **Essential for Applied Energy:** Yes.

### Gate 3 — Finite operation and dispatch

- **Current evidence:** Phase G implements seven 10-minute repeated-dispatch
  sensitivities over the measured 2023 Frontier source calendar. It preserves
  missing source intervals, storage state of charge, power limits, losses,
  unmet demand, and residual rejection.
- **Missing evidence:** Measured receiving demand, case source-capture
  efficiency, case storage design, route losses, outage schedule, and
  environmental receiving capacity.
- **Implemented analysis:** The dispatch engine applies the published 1-2 MW
  demand bounds as constant sensitivities, not as an observed ORNL load trace.
  It evaluates direct reuse and two explicitly generic storage capacities.
- **Required data:** Source and demand profiles, technology parameters, system
  sizing, and environmental capacity.
- **Acceptance criterion:** Conservation is satisfied at every timestep and
  annual totals reconcile; saturation and rejection remain visible.
- **Fallback:** Report a shorter representative period and retain a structural
  limitation; if annual claims are impossible, do not make them.
- **Essential for Applied Energy:** Yes.
- **Current status:** **PARTIAL—OPEN.** The algorithmic conservation criterion
  is met, but no practical Frontier/ORNL annual dispatch claim is permitted
  without the missing measured demand and case design inputs.

### Gate 4 — Losses, auxiliary energy, exergy, cost, and emissions

- **Current evidence:** Phase D implements dimensionally closed source,
  heat-pump, storage, transport, residual-rejection, operational-emissions,
  CAPEX, OPEX, replacement, discounting, LCOH, and NPC accounting with a
  3,888-case sensitivity grid. Negative economic and emissions outcomes are
  retained.
- **Missing evidence:** Case capture efficiency and auxiliaries, synchronized
  delivered heat, full installed cost, transport-network CAPEX, and equipment
  embodied emissions. Case LCOH, NPC, and lifecycle CO2e remain withheld.
- **Implemented analysis:** Normalized case and generic comparator accounting
  separates electricity, fuel displacement, losses, and residual rejection and
  does not monetize the thermal-burden proxy.
- **Required data:** The missing-required parameters in
  `data/metadata/techno_economic_parameters.csv` and finite dispatch.
- **Acceptance criterion:** Results are dimensionally consistent, source
  traced, sensitivity reported, and free of benefit or emissions double
  counting.
- **Fallback:** Preserve negative economics or emissions; if inputs are not
  auditable, retain NO-GO.
- **Essential for Applied Energy:** Yes.
- **Current status:** **PARTIAL—OPEN.**

### Gate 5 — Environmental receiving capacity

- **Current evidence:** Phase E now distinguishes populated land, sparse land,
  sensitive ecosystems, cryosphere, inland water, coastal water, and open
  ocean. Unsupported external sinks are excluded. EPA thermal-discharge
  guidance, Tennessee temperature and mixing-zone rules, Oak Ridge
  environmental context, and generic tank-storage capacity are registered in
  reproducible tables.
- **Missing evidence:** Case-specific tank volume and operating temperature
  difference, route and footprint clearance, synchronized finite dispatch,
  cumulative residual rejection, and—if any new water discharge were ever
  proposed—flow, upstream temperature, permit limits, mixing zone, biology,
  and cumulative-impact assessment.
- **Implemented analysis:** Closed-loop local reuse is retained only as a
  conditional pathway with residual heat returned to the existing rejection
  system. Direct release to land, water, cryosphere, coast, or ocean receives
  no arbitrary positive capacity. Generic tank sensitivity is explicitly not
  a Frontier design.
- **Required data:** Case design and finite-dispatch inputs listed in
  `data/metadata/environmental_parameters.csv`; any external thermal discharge
  additionally requires a site-specific regulatory and ecological assessment.
- **Acceptance criterion:** The practical recommendation uses only pathways
  with evidence-based capacity or exclusion logic and reports cumulative load.
- **Fallback:** Exclude pathways that cannot be credibly assessed.
- **Essential for Applied Energy:** Yes for the practical pathway.
- **Current status:** **PARTIAL—OPEN.** The constraint and exclusion model is
  complete. Phase G reports cumulative residual rejection for explicit
  sensitivities, but the case-specific cumulative environmental load remains
  unavailable without measured demand and a permitted receiving design.

### Gate 6 — Structural uncertainty of global claims

- **Current evidence:** The prespecified Phase F matrix is complete across four
  climate years, NCEP/NCAR Reanalysis 1 and NCEP-DOE Reanalysis 2, WorldPop and
  GHS-POP, native and conservatively coarsened grids, and Humidex,
  air-temperature, and wet-bulb-proxy metrics. Machine-readable results are in
  `results/tables/structural_replication.csv`; the generated interpretation is
  in `docs/STRUCTURAL_UNCERTAINTY.md`.
- **Missing evidence:** A modern independent high-resolution reanalysis such as
  ERA5 remains unavailable through an anonymous reproducible acquisition path.
  NCEP-DOE Reanalysis 2 shares lineage and resolution with Reanalysis 1.
- **Completed analysis:** Tested prespecified structural conclusions rather
  than exact source/sink geography across years, reanalysis products,
  resolutions, population representations, and metrics.
- **Required data:** Complete for the scoped Phase F claim. ERA5 or an
  equivalent independent product would strengthen, but is not required for,
  the narrowed product-conditional conclusion.
- **Acceptance criterion:** The manuscript reports which structural
  conclusions replicate and which geography or magnitudes are unstable.
- **Fallback:** Narrow global claims to the products and years actually
  replicated.
- **Essential for Applied Energy:** Yes for global claims; scope narrowing is
  possible.
- **Current status:** **CLOSED WITH SCOPE LIMITATIONS.** Structural conclusions
  replicate within the prespecified matrix, while magnitudes and selected
  locations remain product-, metric-, and resolution-dependent. This gate does
  not establish practical admissibility or close any real-case dispatch gate.

### Gate 7 — Global-to-real constraint survival

- **Current evidence:** Marginal mask and penalty ablations are available, but
  they are not linked to a real heat stream.
- **Missing evidence:** A monotone or explained non-monotone sequence from the
  global bound through environmental, geographic, technology, storage,
  demand, dispatch, and economic constraints.
- **Proposed analysis:** Construct a case-specific constraint waterfall and
  report the fraction of theoretical thermal-burden value surviving each step.
- **Required data:** Outputs from Gates 1–6.
- **Acceptance criterion:** Every waterfall step is generated from an explicit
  constraint and unexpected increases are investigated.
- **Fallback:** If the units cannot be made comparable, report separate
  physical and burden waterfalls without combining them.
- **Essential for Applied Energy:** Yes for the proposed two-scale novelty.

### Gate 8 — Decision and Pareto evidence

- **Current evidence:** Abstract penalty sweeps indicate mode switching.
- **Missing evidence:** Practical trade-offs among rejection, temporal
  storage, local reuse, nearby transport, and combined pathways.
- **Proposed analysis:** Report non-dominated outcomes for useful energy,
  auxiliary electricity, cost, emissions, environmental load, and
  thermal-burden change without an arbitrary welfare scalar.
- **Required data:** Calibrated case simulations.
- **Acceptance criterion:** Preferred modes and their parameter dependence are
  transparent; dominated and negative results remain visible.
- **Fallback:** Report a comparative outcome table when a stable Pareto front
  is not informative.
- **Essential for Applied Energy:** Yes.

### Gate 9 — Novelty and journal fit

- **Current evidence:** The global marginal bound, pathology diagnostics, and
  matched temporal/spatial comparison are distinct but insufficiently applied.
- **Missing evidence:** A frozen-results comparison against recent
  waste-heat, thermal-storage, district-energy, heat-stress, and constrained
  allocation literature.
- **Proposed analysis:** Repeat the novelty audit after the real-case results
  are fixed.
- **Required data:** Verified publisher and DOI metadata.
- **Acceptance criterion:** The contribution demonstrably exceeds a standard
  waste-heat recovery or storage-optimization case and remains focused on
  applied energy.
- **Fallback:** Retain NO-GO or narrow to a methods-focused paper without
  overstating novelty.
- **Essential for Applied Energy:** Yes.

### Gate 10 — Traceability and reproducibility

- **Current evidence:** Public-data ledgers, checksums, generated canonical
  outputs, tests, and a successful clean rebuild are available for the current
  model.
- **Missing evidence:** Equivalent provenance and clean-build evidence for all
  new case, technology, dispatch, environmental, economic, and replication
  outputs.
- **Proposed analysis:** Extend the acquisition ledger, artifact provenance,
  manuscript-value registry, tests, and clean-build report.
- **Required data:** All new raw snapshots and exact generation commands.
- **Acceptance criterion:** Every manuscript number maps to a canonical output;
  all feasible outputs regenerate without hidden files or manual edits.
- **Fallback:** Remove untraceable results.
- **Essential for Applied Energy:** Yes.

### Gate 11 — Scientific review and claim control

- **Current evidence:** The existing package has passed a prior adversarial
  review, but not for the two-scale extension.
- **Missing evidence:** Review by climate, thermodynamic, heat-transfer,
  energy-system, optimization, environmental, statistical, and
  reproducibility perspectives after results freeze.
- **Proposed analysis:** Conduct structured hostile review, classify findings,
  implement justified high- and medium-severity fixes, and re-audit all claims.
- **Required data:** Frozen outputs and complete draft.
- **Acceptance criterion:** No unresolved high-severity scientific defect and
  all claims match the evidence.
- **Fallback:** WEAK GO with explicit claim narrowing or NO-GO.
- **Essential for Applied Energy:** Yes.

### Gate 12 — Health-outcome interpretation

- **Current evidence:** The endpoint is a population-weighted thermal-stress
  proxy, not mortality or morbidity.
- **Missing evidence:** None if health effects are not claimed.
- **Proposed analysis:** Preserve the exposure-burden label and avoid causal
  health-effect conversion.
- **Required data:** No new epidemiological data are required under the
  restricted claim.
- **Acceptance criterion:** Abstract, manuscript, figures, highlights, and
  cover letter contain no mortality, morbidity, or causal health-effect claim.
- **Fallback:** Remove any unsupported health wording.
- **Essential for Applied Energy:** Claim-control gate, not a requirement for a
  mortality model.

### Gate 13 — Submission administration

- **Current evidence:** Placeholder author and declaration fields remain.
- **Missing evidence:** Final authorship, affiliations, funding, competing
  interests, originality and author approval, publication route, and a
  permanent repository identifier.
- **Proposed analysis:** Keep explicit placeholders until author confirmation;
  never infer these items.
- **Required data:** Author-supplied confirmations and repository archival DOI.
- **Acceptance criterion:** All mandatory submission declarations and metadata
  are confirmed by the authors.
- **Fallback:** Science may reach GO or WEAK GO, but the package remains blocked
  from actual submission.
- **Essential for Applied Energy:** Administratively essential; not a
  scientific-validity gate.

## Fixed decision rule

**GO** requires closure of Gates 1–11 with claims matched to the available
evidence and a reproducible end-to-end build. **WEAK GO** is permitted only
when a narrower methods- or systems-focused claim remains defensible and the
remaining limitation is stated precisely. Otherwise the decision remains
**NO-GO**. Gate 13 must be closed before actual journal submission even if the
scientific decision is GO.
