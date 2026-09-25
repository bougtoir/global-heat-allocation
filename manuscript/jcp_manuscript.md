# Abstract

Thermal-energy management can reduce heat at a source while relocating conserved heat to an unevaluated receiving environment. We develop a conservation-aware, evidence-gated framework to detect the resulting risk of environmental problem shifting. The framework joins a global one-unit screening model, which conserves heat between source removal and sink release, to an auditable real pathway based on measured Frontier supercomputer waste heat and documented Oak Ridge National Laboratory demand bounds. The global model minimizes a population-weighted Humidex burden under progressively stricter receiving-class, distance, temporal, and local-capacity constraints. Its unconstrained optimum selects open ocean because the objective rewards low population exposure, illustrating a free-sink pathology rather than a safe destination. For a matched source event, the constrained spatial screening value is {{value:matched_spatial_value}} burden units/GJ; same-location temporal delay retains {{value:matched_temporal_fraction}} of that value. The measured source contains {{value:frontier_observed_heat}} MWh-th across {{value:frontier_valid_intervals}} valid ten-minute intervals. Six reuse or storage modes remain conditional, and zero practical endpoints are supported, because synchronized demand, capture, route, auxiliary-energy, storage-design, complete-cost, lifecycle, and receiving-environment evidence do not all close. The main contribution is not a proposed sink, a quantified ecosystem-damage estimate, or a deployable relocation scheme. It is a reproducible method that flags when local thermal relief moves conserved heat beyond the validated objective boundary and prevents unsupported engineering or environmental conclusions.

Keywords: cleaner production; problem shifting; waste heat; thermal pollution; industrial ecology; heat allocation; evidence gating

# 1. Introduction

Cleaner production is preventive: environmental pressure should be reduced at its origin or by system redesign, not transferred across places, media, life-cycle stages, or actors. Industrial ecology and life-cycle assessment apply this boundary discipline across connected processes and impact categories.{{cite:glavic2007sustainability,shi2016cleanerproduction,chertow2007symbiosis,hellweg2014lca,finnveden2009lca}} Thermal management is a direct test because energy conservation makes transfer explicit. Heat removed from a source persists until it is converted, stored, used, or rejected through a characterized pathway.

Problem shifting is established in sustainability research. Carbon-only and partial-boundary rules can displace other pressures; single-objective energy optimization can improve one indicator while worsening others; data-centre cooling has water-energy-carbon trade-offs; and rebound, circular-economy, planetary-boundary, and environmental-justice research shows why low measured exposure does not establish safety.{{cite:laurent2012carbonfootprint,ryberg2018absolute,moncaster2019burdenshifting,gonzalezgaray2019burdenshifting,li2026datacenterburden,zink2017rebound,korhonen2018circular,steffen2015boundaries,mohai2009justice}} The narrower gap is an operational test for conserved heat when an optimizer chooses its release place and time.

Waste heat is an important cleaner-production resource, but technical availability is not usable supply. Feasibility depends on temperature, temporal coincidence, demand, distance, heat-pump performance, networks, storage, auxiliary energy, economics, and environmental conditions. High-temperature heat pumps, district storage, low-temperature networks, and allocation methods expand the feasible set only under explicit parameters and matched boundaries.{{cite:forman2016wasteheat,papapetrou2018wasteheat,brueckner2015wasteheat,ebrahimi2014datacenter,wahlroos2018datacenter,ebrahimi2019datacenterwhr,zhang2024datacentermismatch,fang2018industrycity,yang2021exergoenvironmental,arpagaus2018heatpumps,guelpa2019storage,lund2014district,li2022allocation}} Neither source magnitude nor favorable abstract allocation establishes a cleaner-production outcome.

Receiving conditions are equally consequential. Thermal discharges alter river temperatures; thermoelectric cooling creates material thermal-pollution pressure; oceans absorb rather than eliminate anthropogenic heat; and cryosphere regions respond through coupled feedbacks.{{cite:raptis2016thermalpollution,madden2013thermaleffluent,cheng2017oceanheat,serreze2011arctic}} Sparse population, open water, snow, sea ice, or a remote atmospheric cell can look attractive because their ecological and Earth-system responses are absent from a human-exposure objective. “Sink” identifies an accounting destination, not assimilative capacity, permission, safety, or sustainability.

Anthropogenic heat is small relative to the planetary mean energy budget but can matter where concentrated. Heat tolerance depends jointly on temperature and humidity, and heat-stress indices differ in meaning and applicability.{{cite:flanner2009anthropogenic,chen2004anthropogenic,sherwood2010adaptability,raymond2020heat,mora2017deadlyheat,buzan2015heatstress,liljegren2008wbgt,stull2011wetbulb}} These facts motivate a population-weighted thermal-stress screen, not a mortality, morbidity, ecological, or climatic damage model.

The model must therefore conserve heat between source removal and sink release, then pass independent receiving-pathway and practical-evidence gates. Without both controls, apparent benefit can arise from deleting heat or exploiting an unevaluated domain, and a screening value can be mistaken for delivered energy, avoided emissions, economic value, or environmental safety.

This study develops a two-scale no-free-heat-sink framework. A global one-unit model exposes pathological optima, adds receiving constraints, compares spatial relocation with same-location delay, and tests structural and finite-capacity behavior. An applied branch pairs a measured low-grade source with official demand bounds and classifies each required input and endpoint by evidence state. Human burden and environmental eligibility remain separate, as do burden units, heat, cost, and emissions.

We ask where a conserved one-unit objective finds apparent opportunity; which receiving classes reveal omitted impacts; how much matched spatial value same-location delay retains; whether the diagnostic persists across structural and finite-capacity tests; and how far a measured pathway advances without invented data. The framework flags problem-shifting risk when modeled source relief releases conserved heat to a pathway whose relevant receiving impacts are neither represented nor independently validated. The flag diagnoses an objective-boundary failure, not realized ecological damage.

[[FIGURE:1]]

# 2. Methods

## 2.1 Study design and analytical separation

The study used a sequential, evidence-gated design. The first branch quantified a theoretical marginal screening bound in burden space. The second branch quantified measured and conditional thermal-energy flows in MWh-th. The branches were connected only by a constraint waterfall describing which claims survived; no conversion factor mapped burden units/GJ to MWh-th, USD, CO2e, health outcomes, or a composite sustainability score. This separation prevents a numerical global optimum from acquiring an unsupported practical meaning.

The sequence defined the burden objective, exposed the unconstrained receiver, added locality and environmental masks, compared spatial and temporal responses, tested structure and finite capacity, audited measured source and demand evidence, ran conditional dispatch, and classified endpoints. Analyses were prespecified and frozen before final manuscript framing.

Problem-shifting risk was operationally flagged when three conditions coincided: the intervention reduced the modeled source-side burden, the same conserved heat entered a receiving pathway, and impacts relevant to that receiver were omitted from the objective and remained unevidenced by an independent gate. A flag therefore denotes an incomplete sustainability claim, not a measured magnitude of ecosystem harm. Conversely, passing the numerical objective did not count as passing environmental eligibility.

Table 1 summarizes principal inputs and settings; full inventories are in the supplement. Table 2 separates receiving classes from evidence needed for practical eligibility. Low modeled burden can coexist with failed ecological, regulatory, physical, or engineering tests, while closed-loop reuse can remain conditional because its demand, route, capture, auxiliaries, or residual rejection are unresolved.

[[TABLE:1]]

## 2.2 Global data and harmonization

The meteorological baseline used 2023 NCEP/NCAR Reanalysis 1 on its 94 by 192 T62 Gaussian grid at six-hour resolution.{{cite:kalnay1996ncep}} Two-metre air temperature, specific humidity, surface pressure, ten-metre winds, radiative fields, sea-ice fraction, snow water equivalent, and land fraction were harmonized to a common analysis cube. WorldPop 2020 unconstrained population was conservatively aggregated to the climate grid,{{cite:tatem2017worldpop}} and Natural Earth supplied descriptive country labels. Acquisition manifests retain source identifiers, retrieval conditions, sizes, checksums, licenses, and completeness. The full variable-level inventory is reported in Table S1.

Grid-cell area was computed on the Gaussian latitude-longitude grid. For cell area A, prescribed atmospheric mixing height h, air density rho, and specific heat cp, the slab heat capacity was C = A h rho cp. The canonical h was 100 m, rho was 1.225 kg/m3, and cp was 1005 J/kg/K. A heat increment Q generated delta T = Q/C. This is a controlled screening perturbation, not a boundary-layer simulation. It does not represent advection, entrainment, land or water heat uptake, cloud feedback, precipitation, or circulation adjustment.

The primary mask required land fraction of at least 0.5 and excluded cells with sea-ice fraction of at least 0.15 or snow water equivalent of at least 1 kg/m2. Candidate distance was limited to 5000 km. An ordered ablation retained unrestricted, distance-only, cryosphere-excluded, ocean-excluded, and joint masks so that changes in objective value and receiving class could be distinguished. The unrestricted result diagnosed what the incomplete objective exploited; it was never interpreted as a recommendation or a physical disposal proposal.

## 2.3 Population-weighted thermal-burden objective

Specific humidity q and pressure p defined vapour pressure e = qp/(0.622 + 0.378q). Humidex was H = TC + (5/9)(ehPa - 10). With reference H0 and curvature gamma, stress excess was s = max(H - H0, 0), and cell-time burden was B = P s^gamma, where P is population. The canonical setting used H0 = 26 and gamma = 2. For a one-GJ perturbation, the marginal burden was m = P gamma s^(gamma-1) 10^9/C. Air temperature and a validity-masked Stull wet-bulb proxy were evaluated as alternative thermal metrics.

The function measures population-weighted change in a thermal-stress proxy, not deaths, disease, productivity, welfare, adaptation, within-cell distribution, economics, or ecosystems. Zero modeled burden is therefore not zero environmental impact; that omission makes the unconstrained sink diagnostic informative.

The units are model-specific burden units rather than a standard health or environmental endpoint. Population enters multiplicatively, while the convex stress term increases marginal sensitivity above the reference. Alternative metrics test whether the diagnostic depends on Humidex alone, but they do not make the endpoint clinically interpretable. All comparisons therefore retain the named metric, reference, curvature, and atmospheric-capacity assumptions.

## 2.4 Conserved spatiotemporal allocation

A decision removed Q from source cell-time (i,t) and released the same Q at sink cell-time (j,t'). For the marginal one-GJ search, the net screening value was V = msource - msink - cd d - cs(t' - t), where d was great-circle distance, cd was a conditional distance penalty, and cs was a conditional storage-lag penalty per six-hour step. The coefficients were abstract screening terms. They were not transport-energy losses, costs, emissions, heat-pump efficiencies, or engineering performance.

Spatial allocation used the same source and sink time; temporal allocation retained the cell and delayed release by 6, 12, or 18 hours; joint allocation allowed both changes. A spherical nearest-neighbour search enumerated candidates within the distance limit before exact great-circle evaluation, avoiding a dense global pairwise matrix. The memory-bounded strategy resembles scalable optimal-transport computation but solves a one-unit pair search, not finite-mass transport.{{cite:peyre2019transport}} Candidate scores were evaluated in time order, and each source removal was paired with an equal sink release.

No-relocation had value zero, and negative candidates were not recast as benefits. Exact ties and candidates within one percent of the optimum were counted to distinguish objective value from a representative coordinate when mathematically equivalent receivers were environmentally heterogeneous.

## 2.5 Progressive receiving-environment constraints

The audit began with the human-burden objective, then added distance, cryosphere exclusion, ocean exclusion, and their joint mask. Distance tested locality, not environmental protection. Land candidates still required land-use, ecological, cumulative-load, dispersion, and authorization evidence absent from the global model.

Atmospheric and radiative concepts were treated with similar discipline. Observed outgoing longwave radiation is a descriptive state variable, not the derivative of incremental heat rejection. CERES-type radiation fields characterize the Earth radiation budget but do not establish how a proposed release would alter it.{{cite:loeb2018ceres}} Engineered radiative-cooling devices can reject heat through the atmospheric window under specified spectral, meteorological, geometric, and operating conditions.{{cite:raman2014radiative,zhai2017radiative}} That literature does not validate ambient atmosphere or “space” as an unrestricted practical sink. Accordingly, radiative concepts entered the failure matrix as conditional technology concepts rather than as a disposal term that removes heat from the Earth system.

The failure matrix recorded why low indexed burden was insufficient, required evidence, and the maximum permitted claim. Open ocean and cryosphere were excluded from practical interpretation; land required receptor-specific review; and engineered reuse or storage still required a documented energy balance and residual destination.

[[TABLE:2]]

## 2.6 Robustness, structural replication, and finite capacity

Parametric tests crossed three Humidex reference levels, three curvatures, and three mixing heights. Air-temperature and wet-bulb sensitivities varied reference values at fixed curvature and mixing height. Seasonal and local day-night summaries characterized the marginal field beyond the annual maximum, and progressive mask ablation traced how representative receiver geography changed as exclusions were introduced. Supporting source-hotspot, finite-transfer, wind-trajectory, seasonal, mask-ablation, and joint-penalty diagnostics are shown in Figures S1-S6.

Nine prespecified structural scenarios varied climate year, NCEP/NCAR Reanalysis 1 versus the related NCEP-DOE Reanalysis 2 product, population surface, factor-two grid aggregation, and Humidex, air-temperature, or wet-bulb formulation. Because the reanalyses share lineage and coarse resolution, this was structured sensitivity analysis rather than independent high-resolution replication. It tested persistence of positive constrained value, sink non-uniqueness, and pathological unrestricted receivers, not coordinate identity or numerical invariance.

Scenarios and dispatch cases were deterministic model evaluations, not independent statistical samples. Counts, ranges, ties, residuals, and envelopes are descriptive; no inferential statistics were assigned to the ensemble.

Finite-energy tests recomputed exact quadratic burden changes for 1, 1000, 100000, and 1000000 GJ under an energy cap and 0.1-K maximum local perturbation. They locate where the one-unit marginal approximation becomes infeasible or nonlinear; they do not model repeated planetary transfer or infrastructure. A reduced-order seven-day wind trajectory diagnosed downstream class changes without computing plume concentration, temperature fields, exposure, or ecological effects.

## 2.7 Measured source and receiving-demand evidence

The real source was the public 2023 Frontier facility dataset and versioned Figshare deposit.{{cite:frontier2024dataset,frontier2024figshare}} Ten-minute heat, coolant temperature, flow, compute, accessory, and total power were aligned to a complete calendar. Missing observations remained unavailable, without interpolation or clipping; heat was integrated only over valid intervals.

The candidate receiving pathway used the official Oak Ridge National Laboratory waste-heat-recovery report.{{cite:ornl2024wasteheatreport}} The report documents annual average and maximum space-heating demand for building groups and describes heat-pump configurations. It does not provide a synchronized hourly or sub-hourly receiving-demand trace. The reported values were therefore used only as constant lower and upper sensitivity bounds. They were not converted into a reconstructed annual demand profile.

Evidence items were classified as FOUND_MEASURED, FOUND_DERIVABLE, FOUND_BOUND_ONLY, or NOT_FOUND; pathways as SUPPORTED, CONDITIONAL, or EXCLUDED. Existing source-side cooling removal was not treated as recovery-system capture efficiency. Facility accessory power was not treated as incremental recovery electricity. Existing steam-line distance and loss were not assigned to an unbuilt hot-water route. Equipment price was not represented as installed-project cost, and an existing discharge permit was not treated as authorization for a new thermal discharge. The full item-level registry and claim limits are in Table S2.

Tables 3 and 4 summarize structural and real-case evidence; complete item and scenario registries are in Table S2 and Table S3, respectively. The asymmetry is intentional: reproducible global outputs can coexist with unresolved project inputs.

[[TABLE:3]]

[[TABLE:4]]

## 2.8 Constraint waterfall and conditional finite dispatch

The global-to-real waterfall began with the theoretical burden-space opportunity and then applied receiving-environment, geographic, pathway, technology, storage, demand, dispatch, cost, lifecycle, and authorization gates. A gate could retain a claim, narrow it, render it conditional, or exclude it. The terminal endpoint required evidence sufficient to claim delivered useful heat through a defined pathway; it did not require the burden-space and energy-space quantities to share a scalar unit.

Finite dispatch used the measured ten-minute source, explicit unavailable intervals, documented heat-pump COP and capacity, constant demand bounds, and no-storage, formula-sized, and generic-storage sensitivities. It conserved thermal energy each timestep and tracked useful heat, storage charging and discharging, conversion and standing losses, heat-pump and storage electricity, unmet demand, and residual rejection. A no-demand case tested source closure. Thirty-one checks covered timestep and annual balance, non-negativity, component capacities, unavailable intervals, demand saturation, visible residual rejection, and aggregation; all checks are listed in Table S4.

Six practical modes combined lower and upper demand bounds with direct reuse, formula storage, and generic storage. Mode comparison retained useful heat, demand served, residual rejection, electricity, storage capacity, and storage losses as separate columns. No case-specific LCOH, net present cost, payback, or lifecycle CO2e was used to select a mode because installed-cost scope, price year, route, auxiliary, operational, and embodied-impact evidence was incomplete. Pareto status within the bounded sensitivity set therefore described numerical trade-offs but did not establish a project recommendation.

The conditional calculations used unit-consistent thermal and electrical balances, but their demand inputs were reported constants rather than timestamped observations. Storage sizes and performance parameters were sensitivity constructs, not selected equipment. This distinction prevents a numerically closed dispatch from being described as an empirically calibrated annual project simulation. It also keeps residual source rejection visible instead of treating useful delivery as if it consumed the full measured source.

## 2.9 Reproducibility and claim control

The repository retains acquisition code, immutable raw snapshots or durable manifests, checksums, processed cubes, frozen canonical outputs, structural and dispatch tables, figure-generation code, and machine-readable manuscript values. Numeric statements were resolved from the value registry or result tables. Missing source observations remain explicit throughout processing, and generated submission assets are rebuilt from the frozen analysis tree rather than edited manually.

A machine-readable matrix separated directly supported claims, interpretive claims consistent with the evidence, and prohibited claims. The prohibited level included a specific safe sink, deployable global relocation, calibrated annual Frontier/ORNL operation, case-specific economics or lifecycle performance, health benefits, planetary cooling, validated disposal to space, and comprehensive ecological damage. This control was applied before packaging so that rhetorical strength could not exceed stored evidence.

Independent validation scripts also check reference order, figure and table sequence, unresolved value tokens, prohibited language, archive membership, and deterministic regeneration of the submission package.

Additional source-hotspot, mask-ablation, finite-transfer, burden-shifting, practical-mode, and waterfall details are reported in Tables S5-S10.

# 3. Results

## 3.1 Heterogeneous marginal burden and apparent opportunity

The canonical analysis evaluated {{value:global_scenarios_evaluated}} one-unit scenarios; {{value:global_relocation_positive_scenarios}} were relocation-positive. Peak marginal burden concentrated where heat, humidity, population, and prescribed curvature coincided. This burden-space opportunity implied neither practical capture nor an acceptable receiver.

For the matched event, the land and non-cryosphere search produced {{value:matched_spatial_value}} burden units/GJ. The representative source was at {{value:matched_source_latitude}}, {{value:matched_source_longitude}}, and its representative sink was {{value:matched_source_sink_distance}} km away. With {{value:matched_cooptimal_sink_count}} exact co-optima and {{value:matched_near_optimal_sink_count}} candidates within one percent, the result was a broad low-indexed-burden set, not a privileged destination.

Figure 2 maps the heterogeneity exploited by the objective, not a route. Its pattern depends on the climate year, population, metric, slab, and burden parameters; regions with little population-weighted burden can still be environmentally sensitive.

[[FIGURE:2]]

## 3.2 Free-sink pathology

Without receiving-class exclusion, the optimizer selected open ocean. The 5000-km limit shortened relocation but did not add receiving evidence; cryosphere exclusion retained the value because the selected ocean cell was not snow or sea ice. The diagnostic is objective incompleteness: unrepresented impacts receive no penalty.

Ocean exclusion moved the representative optimum to land without changing value because many zero-burden candidates remained. The joint mask defined the canonical screen but did not establish safe land. The apparent solution migrated across classes while assimilative capacity, ecology, justice, and authorization remained outside the scalar objective.

This behavior is the computational diagnostic behind the phrase “no free heat sink.” The phrase does not assert that every heat-management intervention causes unacceptable harm or that productive reuse is impossible. It states a decision rule: a receiving environment receives no automatic sustainability credit merely because the optimized local human-burden increment is low. The full receiving pathway must be specified and evaluated before local relief can be called cleaner production.

## 3.3 Progressive environmental constraints

The cascade ordered the unconstrained optimum, locality and environmental masks, same-location delay, finite capacity, and real-pathway evidence gates. The final stages tested whether source, demand, technology, route, storage, residual rejection, environment, cost, and lifecycle evidence supported an applied endpoint.

Figure 3 shows that the cascade is not a scalar degradation curve. Some global constraints leave burden-space value unchanged while changing admissible interpretation or representative geography. Later practical gates operate in physical-energy and evidence space and therefore have no legitimate conversion into burden units. The terminal result is categorical: a reproducible theoretical screen, six conditional practical modes, and zero supported endpoints. This structure prevents visual or numerical continuity from implying that theoretical burden reduction is a measured quantity of delivered heat.

The failure matrix gave class-specific outcomes: land required receptor review; ocean and cryosphere were excluded; atmospheric or radiative concepts required a causal device model; and reuse or storage remained conditional pending demand, route, capture, auxiliary, storage, and rejection evidence.

[[FIGURE:3]]

## 3.4 Temporal versus spatial response

Same-location temporal management retained a substantial share of the matched spatial value. An {{value:matched_temporal_lag}}-hour delay produced {{value:matched_temporal_value}} burden units/GJ, equal to {{value:matched_temporal_fraction}} of the simultaneous spatial screening value. Because the comparison used the same source event, the ratio reflects temporal variation in the local burden field rather than a different source opportunity.

The temporal result is important for problem-shifting interpretation. Delaying release at the source avoids choosing a remote geographic recipient, but it does not eliminate the energy. Storage has its own materials, losses, capacity, auxiliary energy, and eventual rejection requirements. Temporal management is therefore an alternative allocation mode, not a proof of impact-free disposal. Its cleaner-production relevance depends on whether delay enables productive use, lower-impact rejection, or better alignment with a validated demand.

At high abstract transport penalties, no-relocation dominated spatial-only transfer, whereas the joint model selected a same-location temporal option. This qualitative transition shows that an optimizer can switch modes when movement is penalized. Because the penalties were not calibrated to a route, cost, loss, or emissions inventory, the transition is a sensitivity result rather than an engineering threshold. Figure 4 presents the matched comparison without converting it into practical efficiency.

[[FIGURE:4]]

## 3.5 Structural replication and finite capacity

Across {{value:structural_replication_scenario_count}} structural scenarios, positive constrained spatial value and unrestricted pathological sinks persisted while selected coordinates varied. The constrained value ranged from {{value:structural_spatial_value_min}} to {{value:structural_spatial_value_max}} burden units/GJ. The stable conclusion was structural rather than geographic: heterogeneous marginal burden creates apparent opportunity, and incomplete objectives direct release toward unevaluated receiving classes. Table 3 summarizes these invariants; Table S3 retains all scenario-level values.

Metric and population choices affected source and sink details because each changed the burden surface. Grid aggregation changed cell heat capacity and spatial resolution. Reanalysis-year changes altered weather states. These shifts are expected and argue against presenting a single coordinate as the result. The replication supports the framework’s diagnostic logic, not universal quantitative transferability.

Finite-energy analysis showed that 1, 1000, and {{value:finite_q_largest_feasible}} GJ transfers were feasible under the local cap, whereas {{value:finite_q_smallest_infeasible}} GJ was infeasible. Benefit per GJ declined as source cooling moved away from the marginal state. The finding prevents indefinite scaling of the one-GJ result and reinforces the distinction between an infinitesimal screening bound and a finite thermal project.

## 3.6 Measured waste-heat case

The Frontier calendar contained {{value:frontier_expected_intervals}} expected ten-minute intervals, {{value:frontier_valid_intervals}} valid source observations, and {{value:frontier_missing_intervals}} missing intervals. Valid observed waste heat totaled {{value:frontier_observed_heat}} MWh-th. Waste-heat power ranged from {{value:frontier_waste_heat_min}} to {{value:frontier_waste_heat_max}} MW, with median {{value:frontier_waste_heat_median}} MW, mean {{value:frontier_waste_heat_mean}} MW, and 95th percentile {{value:frontier_waste_heat_p95}} MW. Median supply and return temperatures were {{value:frontier_supply_temperature_median}} degrees C and {{value:frontier_return_temperature_median}} degrees C.

The ORNL evidence provided average and maximum space-heating demand of {{value:ornl_case_a_average}} and {{value:ornl_case_a_maximum}} MW-th for the 5600-5700-5800 complex. The selected larger building set provided bounds of {{value:ornl_case_b_selected_average}} and {{value:ornl_case_b_selected_maximum}} MW-th. These data establish demand magnitude but not temporal coincidence. The source series and receiving summaries therefore cannot support a calibrated annual heat-reuse simulation.

Documented heat-pump evidence included a COP of approximately {{value:heat_pump_case_cop}}, total thermal capacity of {{value:heat_pump_case_total_capacity}} MW-th, and a sink temperature near {{value:heat_pump_case_sink_temperature}} degrees C for the cited configuration. Equipment cost evidence was limited to a unit price without a complete installed scope or reliable project price-year basis. No Frontier-specific route, hydraulic design, recovery heat-exchanger capture performance, incremental balance-of-plant electricity, storage design, or lifecycle inventory was found.

The measured case replaced an abstract source with a traceable time series and temperature grade while making missing links auditable. It identifies which observations would change endpoint classification without claiming that the project case is closed.

## 3.7 Global-to-real evidence waterfall

The global-to-real waterfall retained the global screening results as theoretical burden-space outputs. Environmental constraints narrowed the admissible interpretation but did not create an engineered pathway. The measured source and bounded demand entered the physical-energy branch as supported inputs. Technology, finite dispatch, and equipment evidence allowed conditional calculations. Route, capture, auxiliary, storage-design, complete-cost, lifecycle, and new-discharge evidence remained unresolved.

Figure 5 and Table 5 show claim attrition without converting theoretical burden value into delivered heat. Each stage retains its own quantity and evidence state: the burden field is heterogeneous, but current public evidence does not support a complete practical endpoint.

The terminal zero means zero evidence-supported modes under the prespecified standard, not zero heat, demand, technical possibility, or proof of failure. The categorical endpoint keeps uncertainty decision-relevant.

[[FIGURE:5]]

[[TABLE:5]]

## 3.8 Zero supported practical endpoint and conditional modes

All thirty-one finite-dispatch validation checks passed. The maximum absolute timestep thermal-balance error was {{value:dispatch_max_balance_error}} MWh. Across nonzero-demand sensitivities, served demand ranged from {{value:dispatch_served_fraction_min}} to {{value:dispatch_served_fraction_max}}, while residual source rejection remained {{value:dispatch_residual_rejection_min}} to {{value:dispatch_residual_rejection_max}} MWh-th. These results establish numerical closure for the conditional model but not calibration to observed receiver operation.

Direct lower- and upper-demand modes delivered {{value:dispatch_direct_lower_demand_bound_useful_heat_delivered}} and {{value:dispatch_direct_upper_demand_bound_useful_heat_delivered}} MWh-th, serving {{value:dispatch_direct_lower_demand_bound_demand_served}} and {{value:dispatch_direct_upper_demand_bound_demand_served}} of their imposed bounds. Generic storage increased service but represented temporal-matching sensitivity, not a selected design.

All six modes were conditional. Direct reuse still lacked synchronized demand, capture, route hydraulics, and auxiliary power; storage added capacity, material, loss, and operational requirements. No mode closed cost, lifecycle, environmental, and authorization gates. Figure 6 retains separate outputs rather than a synthetic score.

No reuse, storage, or remote-disposal mode is recommended. Conditional performance can be balanced, but practical selection requires a measured and validated receiving pathway.

[[FIGURE:6]]

# 4. Discussion

## 4.1 Cleaner-production interpretation

Optimization of local thermal burden becomes problem shifting when the receiver is treated as free. The unconstrained model correctly minimized its stated objective by moving heat from high population-weighted stress to zero indexed burden. The failure was not computational; environmental eligibility, ecological sensitivity, lifecycle effects, and authorization were outside the objective.

Cleaner production instead asks which full pathway prevents or productively uses the burden without unvalidated pressure elsewhere. Source reduction, efficiency, recovery, demand matching, storage, and lower-impact rejection can be compared, but their labels confer no automatic benefit: reuse has electricity, material, infrastructure, and residual-heat consequences; storage can defer rejection; radiative technology requires a specified device and operating environment.

The framework complements LCA, industrial ecology, environmental-flow assessment, and engineering design by identifying where they are required. A case-specific LCA was impossible without route, equipment, operational, and embodied-impact inventories; gating that claim is preferable to importing unauditable generic values.

A problem does not disappear when it crosses the system boundary. Reducing burden inside a modeled domain can externalize the same conserved energy, or its associated infrastructure and auxiliary burdens, to an unmodeled receiver. Local heat removal therefore does not establish environmental burden removal. Cleaner-production assessment must follow the receiving pathway far enough to evaluate its relevant physical, ecological, engineering, and governance consequences.

## 4.2 What is novel and what is not

Problem shifting, thermal pollution, waste-heat recovery, industrial symbiosis, optimization, and energy conservation are not new. The contribution is their integration into a reproducible thermal-allocation test with explicit claim control. The global branch lets an incomplete objective reveal its preferred receiver; the applied branch shows why measured source evidence can coexist with a zero-supported endpoint. The framework detects structural risk, not ecological damage from hypothetical releases.

Three design choices distinguish the framework. First, source removal and sink release are explicitly paired, so apparent benefit cannot arise from deleting heat. Second, receiving-class eligibility is evaluated independently of the human-burden scalar, allowing low objective value to fail an environmental gate. Third, global screening and practical energy quantities remain in separate units, joined by categorical evidence states rather than an invented common score. Together, these choices turn problem shifting from a general warning into a traceable objective-boundary diagnostic that can be inspected at each stage.

The negative results are substantive: the ocean optimum rejects minimum human burden as a safety criterion; finite capacity rejects indefinite scaling; and the evidence audit rejects calibrated annual operation and project economics under current data.

## 4.3 Spatial versus temporal management

An eighteen-hour delay retained slightly more than half of the matched spatial bound without selecting a distant receiver. This does not prove storage is preferable, but it motivates matching heat to time-varying demand or lower-burden release conditions before remote relocation.

Practical storage depends on temperature, stratification, losses, power, footprint, materials, auxiliaries, controls, and demand. The conditional dispatch bridges to physical energy and losses, but remains a sensitivity without a measured demand trace and case-specific store.

Spatial and temporal allocation create different pathways, not merely different penalties. The former requires a route and receiver; the latter requires storage and eventual use or rejection. Both must be followed to their endpoints.

## 4.4 Population burden versus environmental burden

Population-weighted thermal stress can screen human sensitivity to an incremental atmospheric perturbation, but it is not a total environmental objective. Ocean, cryosphere, and sparse land have low population burden by construction, not necessarily small ecological or Earth-system responses.

The model ranks a narrow marginal burden; it does not aggregate biodiversity, water temperature, land disturbance, climate feedback, justice, or cumulative industrial load. Describing its result as environmental damage avoided would exceed the evidence.

The framework instead sets a minimum validity condition: relevant receiving impacts must be represented or independently gated. Future multi-receptor extensions should keep their weights and trade-offs explicit.

## 4.5 Connecting global screening and the measured case

The global and Frontier/ORNL scales are linked by receiving-pathway logic, not direct calibration or proposed global relocation of Frontier heat. The global model diagnoses where an incomplete objective sends heat; the measured case operationalizes evidence needed before local reuse is supported.

The measured source preserves missing intervals, variability, temperature grade, and magnitude. Demand summaries bound receiver scale but cannot establish coincidence, storage cycling, peak constraints, or annual service.

Zero supported modes is an applied result: source magnitude and plausible equipment do not determine capture, delivery, electricity, rejection, infrastructure, cost, lifecycle impacts, or environmental eligibility. Those unresolved observations control the classification.

This interpretation also prevents the two scales from being joined through a false conversion. The global result is a marginal change in a modeled burden index per GJ, whereas the applied result is a finite thermal-energy balance under bounded demand. Their connection is the sequence of questions asked of the receiver, not a coefficient that converts theoretical burden value into MWh-th, money, emissions, or health benefit.

## 4.6 Implications for optimization practice

Optimization studies can reduce problem-shifting risk through four controls. First, conserve the targeted flow explicitly between source and destination. Second, separate objective value from destination eligibility. Third, expose unconstrained or weakly constrained solutions as diagnostics before presenting a preferred design. Fourth, attach practical conclusions to machine-readable evidence states. These controls are applicable beyond heat wherever an objective can export a conserved flow or unpriced burden beyond its represented receptors.

Zeros created by missing receptors are especially hazardous. A zero-population cell, unpriced emission, unmodeled ecosystem, or externalized life-cycle stage can act as an artificial free sink. Distance cost can change geography without validating the receiver, as the ablation showed.

Tie counts, near-optimal sets, replications, and evidence classes prevent precise coordinates or modes from obscuring uncertainty. Here sink identity was weakly determined despite precise objective value, and sensitivity-set Pareto efficiency did not justify recommendation. Reporting only one optimizer-selected coordinate or one nondominated mode would have overstated both geographic certainty and applied readiness.

## 4.7 Limitations

The global model is deliberately simplified. Its 100-m slab, instantaneous response, static population, and six-hour grid omit boundary-layer dynamics, advection, surface heat storage, urban form, clouds, precipitation, and circulation feedback. The one-GJ result is marginal; finite-energy tests bound local scaling but do not simulate sustained infrastructure or cumulative release. Consequently, absolute burden values are screening outputs under the stated model, not forecasts of realized atmospheric response.

Thermal indices and the convex burden function are proxies with normative choices. Population aggregation obscures inequality and adaptation; no health outcome is estimated. Related coarse reanalyses broaden sensitivity but do not substitute for independent high-resolution or coupled modeling.

Receiving constraints are categorical, not impact-quantitative. Ocean and cryosphere exclusions prevent unsupported interpretations without measuring damage; land lacks habitat, land-use, dispersion, cumulative-load, and justice layers; the trajectory does not model plume heat. A pathway-specific assessment would require transport, exposure, assimilation capacity, thresholds, cumulative conditions, and uncertainty at the actual receiver.

The real case lacks synchronized demand, capture efficiency, route and hydraulics, incremental auxiliaries, storage design, installed cost, lifecycle inventory, recovery-system availability, and permitting. Constant bounds are sensitivities, not measured operation; case-specific economics, lifecycle CO2e, and design selection are unsupported.

“No free heat sink” has a narrow meaning: no receiving pathway receives an automatic zero-impact or sustainability assumption because modeled local human burden is low. It neither declares every sink harmful nor denies terrestrial radiation, engineered radiative cooling, or regulated assimilation.

## 4.8 Research and decision agenda

The next applied step is a synchronized site campaign: measure receiving load, survey the route, establish capture and auxiliaries, define thermal and hydraulic design, size storage, account for residual heat, specify installed cost and price year, build the lifecycle inventory, and complete environmental and authorization review.

Future work could add explicit multi-receptor constraints, robust treatment of unknown receiving effects, and coupled atmospheric or hydrological models while preserving unit and claim separation.

Decision makers should track heat, auxiliary energy, infrastructure, emissions, and residual rejection beyond the source boundary, applying the same evidence discipline to reuse and storage as to direct discharge.

Reclassification should be prospective: evidence requirements should be fixed before evaluating candidate modes, and missing items should remain visible rather than being replaced selectively with favorable generic assumptions. Once synchronized demand and route-specific engineering are available, the same dispatch architecture can test measured operation, and a case-specific lifecycle inventory can evaluate whether productive use reduces total burden rather than only source-side rejection.

# 5. Conclusions

This study shows how a locally beneficial thermal objective can produce environmental problem shifting when the receiving environment is treated as free. A conserved one-unit global model found strong heterogeneity in population-weighted thermal burden and selected open ocean under an incomplete objective. Progressive constraints changed admissible interpretation and geography; they did not transform low human exposure into environmental safety. Same-location temporal delay retained {{value:matched_temporal_fraction}} of the matched spatial value, but storage likewise requires a complete eventual pathway.

The measured Frontier source and official ORNL demand bounds demonstrate that the framework can proceed beyond a toy example without inventing missing engineering evidence. Finite dispatch balanced under explicit sensitivities, yet six modes remained conditional and zero practical endpoints were supported. This categorical outcome is not evidence that recovery is impossible. It is evidence that source magnitude and numerical feasibility are insufficient for a cleaner-production claim.

Thermal management should optimize and validate the full receiving pathway, not merely remove heat from the source environment. The framework provides a reproducible way to expose nominal free sinks, separate human burden from environmental eligibility, preserve unit integrity, identify decision-critical evidence gaps, and report zero supported modes when those gaps remain open.

The phrase “no free heat sink” therefore denotes a modeling rule, not a universal assertion of harm: no receiving pathway is entitled to a zero-impact or sustainability assumption merely because local indexed human burden is low. A supported pathway must specify where conserved heat ultimately goes and provide evidence appropriate to that receiving domain.

# Data and code availability

Analysis code, configurations, processed result tables, checksums, figure-generation scripts, and claim-evidence files are available at https://github.com/bougtoir/global-heat-allocation. Large public raw files are represented by durable local snapshots and acquisition manifests with source URLs, retrieval conditions, file sizes, SHA-256 checksums, and licenses. AUTHOR ACTION: archive the final repository release and insert its permanent DOI before submission.

# Funding

AUTHOR ACTION: confirm and insert the complete funding statement before submission.

# Declaration of competing interest

AUTHOR ACTION: confirm and insert the competing-interest declaration before submission.

# Ethics and consent

The study used public environmental, population, facility, and report data and did not involve human participants or identifiable personal data. AUTHOR ACTION: confirm whether the target journal requires any additional institutional statement.

# CRediT authorship contribution statement

AUTHOR ACTION: confirm and insert the complete CRediT authorship contribution statement before submission.

# Declaration of generative AI and AI-assisted technologies

During preparation of this work, the author used Devin (Cognition AI) to assist with code generation, analysis-workflow development, reference checking, figure preparation, and language drafting. The author reviewed and edited all outputs, verified the underlying data, analyses, and citations, and takes full responsibility for the content.
