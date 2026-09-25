PYTHON ?= .venv/bin/python

.PHONY: install references verify-references download verify-data validate-data technology-parameters techno-economic phase-d-handoff environmental-constraints phase-e-handoff structural-replication phase-f-handoff finite-dispatch phase-g-handoff frozen-baseline case-specific-evidence pathway-eligibility constraint-waterfall practical-pareto manuscript-values applied-energy-audit jcp-audit jcp-submission jcp-qc phase-2-handoff preprocess validate-processed synthetic-validation phase-3-handoff analyze extended-analysis physical-diagnostics robustness figures tables results-handoff submission validate-analysis provenance test lint all clean

install:
	python3 -m venv .venv
	.venv/bin/python -m pip install --upgrade pip
	.venv/bin/python -m pip install -e ".[dev,manuscript]"

references:
	$(PYTHON) scripts/fetch_reference_metadata.py

verify-references:
	$(PYTHON) scripts/fetch_reference_metadata.py --verify

download:
	$(PYTHON) scripts/download_data.py

verify-data: download
	$(PYTHON) scripts/download_data.py --verify

validate-data: verify-data
	$(PYTHON) scripts/validate_data.py

technology-parameters: verify-data
	$(PYTHON) scripts/build_technology_parameters.py
	$(PYTHON) scripts/validate_data.py

techno-economic: technology-parameters
	$(PYTHON) scripts/build_techno_economic_analysis.py
	$(PYTHON) scripts/validate_data.py

phase-d-handoff: techno-economic
	$(PYTHON) scripts/write_phase_d_handoff.py

environmental-constraints: techno-economic
	$(PYTHON) scripts/build_environmental_constraints.py
	$(PYTHON) scripts/validate_data.py

phase-e-handoff: environmental-constraints
	$(PYTHON) scripts/write_phase_e_handoff.py

structural-replication: validate-data
	$(PYTHON) scripts/run_structural_replication.py
	$(PYTHON) scripts/validate_structural_replication.py

phase-f-handoff: structural-replication
	$(PYTHON) scripts/write_phase_f_handoff.py

finite-dispatch: technology-parameters
	$(PYTHON) scripts/run_finite_dispatch.py
	$(PYTHON) scripts/validate_finite_dispatch.py

phase-g-handoff: finite-dispatch
	$(PYTHON) scripts/write_phase_g_handoff.py

frozen-baseline:
	$(PYTHON) scripts/download_data.py --verify
	$(PYTHON) scripts/fetch_reference_metadata.py --verify
	$(PYTHON) scripts/write_frozen_baseline.py

case-specific-evidence: technology-parameters
	$(PYTHON) scripts/build_case_specific_evidence.py

pathway-eligibility: case-specific-evidence
	$(PYTHON) scripts/write_pathway_eligibility.py

constraint-waterfall: pathway-eligibility
	$(PYTHON) scripts/build_constraint_waterfall.py

practical-pareto: constraint-waterfall
	$(PYTHON) scripts/build_practical_pareto.py

manuscript-values: practical-pareto
	$(PYTHON) scripts/build_manuscript_values.py

applied-energy-audit: manuscript-values
	$(PYTHON) scripts/write_applied_energy_audit.py

jcp-audit:
	$(PYTHON) scripts/build_no_free_sink_outputs.py
	$(PYTHON) scripts/write_jcp_audit_and_claims.py

jcp-submission: jcp-audit
	$(PYTHON) scripts/build_jcp_submission.py

jcp-qc: jcp-submission
	$(PYTHON) scripts/validate_jcp_submission.py

phase-2-handoff:
	$(PYTHON) scripts/write_phase2_handoff.py

preprocess: validate-data
	$(PYTHON) scripts/preprocess.py

validate-processed: preprocess
	$(PYTHON) scripts/validate_processed.py

synthetic-validation: validate-processed
	$(PYTHON) scripts/run_synthetic_validation.py

phase-3-handoff:
	$(PYTHON) scripts/write_phase3_handoff.py

analyze: validate-processed
	$(PYTHON) scripts/run_global_analysis.py

extended-analysis: analyze
	$(PYTHON) scripts/run_extended_analysis.py

physical-diagnostics: analyze
	$(PYTHON) scripts/run_physical_diagnostics.py

robustness: analyze
	$(PYTHON) scripts/run_robustness_analysis.py

figures: validate-analysis
	$(PYTHON) scripts/make_analysis_figures.py

tables: validate-analysis
	$(PYTHON) scripts/make_analysis_tables.py

results-handoff: tables
	$(PYTHON) scripts/make_global_analysis_handoff.py

submission: figures tables results-handoff phase-g-handoff verify-references
	$(PYTHON) scripts/build_submission.py

validate-analysis: synthetic-validation extended-analysis physical-diagnostics robustness
	$(PYTHON) scripts/validate_global_analysis.py
	$(PYTHON) scripts/validate_extended_analysis.py

provenance: submission phase-e-handoff phase-f-handoff phase-g-handoff
	$(PYTHON) scripts/build_numerical_provenance.py

test:
	$(PYTHON) -m pytest

lint:
	$(PYTHON) -m ruff check src scripts tests workflows
	$(PYTHON) -m ruff format --check src scripts tests workflows

all: lint test provenance

clean:
	rm -rf build .pytest_cache .ruff_cache
