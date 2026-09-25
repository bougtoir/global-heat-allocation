"""Build a machine-readable code-to-artifact numerical provenance manifest."""

from __future__ import annotations

import csv
import hashlib
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "provenance" / "NUMERICAL_PROVENANCE.csv"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _hash_listing(paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths):
        digest.update(str(path.relative_to(ROOT)).encode())
        digest.update(_sha256(path).encode())
    return digest.hexdigest()


def _git_revision() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _environment() -> str:
    freeze = subprocess.run(
        [sys.executable, "-m", "pip", "freeze", "--all"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.encode()
    return (
        f"python={platform.python_version()};"
        f"platform={platform.platform()};"
        f"pip_freeze_sha256={hashlib.sha256(freeze).hexdigest()}"
    )


def _inputs(paths: list[Path]) -> str:
    return ";".join(
        f"{path.relative_to(ROOT)}={_sha256(path)}" for path in sorted(paths)
    )


def _generator(path: Path) -> tuple[str, str]:
    name = path.name
    relative = str(path.relative_to(ROOT))
    if relative.startswith("results/canonical/"):
        if name == "one_unit_allocations.csv":
            return "scripts/run_global_analysis.py", "make analyze"
        if name == "source_hotspot_robustness.csv":
            return "scripts/run_robustness_analysis.py", "make robustness"
        if name == "natural_redistribution_summary.csv":
            return "scripts/run_physical_diagnostics.py", "make physical-diagnostics"
        return "scripts/run_extended_analysis.py", "make extended-analysis"
    if relative.startswith("results/diagnostics/"):
        if name == "finite_dispatch_validation.csv":
            return (
                "scripts/validate_finite_dispatch.py",
                "make finite-dispatch",
            )
        if "validation" in name:
            return (
                (
                    "scripts/validate_global_analysis.py"
                    if name == "global_analysis_validation.csv"
                    else "scripts/validate_extended_analysis.py"
                ),
                "make validate-analysis",
            )
        return "scripts/run_physical_diagnostics.py", "make physical-diagnostics"
    if relative.startswith("results/dispatch/"):
        return "scripts/run_finite_dispatch.py", "make finite-dispatch"
    if relative.startswith("results/figures/"):
        return "scripts/make_analysis_figures.py", "make figures"
    if relative.startswith("results/tables/"):
        if name == "structural_replication.csv":
            return (
                "scripts/run_structural_replication.py",
                "make structural-replication",
            )
        return "scripts/make_analysis_tables.py", "make tables"
    if relative == "docs/GLOBAL_ANALYSIS_RESULTS.md":
        return "scripts/make_global_analysis_handoff.py", "make results-handoff"
    if relative == "docs/STRUCTURAL_UNCERTAINTY.md":
        return "scripts/run_structural_replication.py", "make structural-replication"
    if relative == "docs/PHASE_F_HANDOFF.md":
        return "scripts/write_phase_f_handoff.py", "make phase-f-handoff"
    if relative == "docs/PHASE_G_HANDOFF.md":
        return "scripts/write_phase_g_handoff.py", "make phase-g-handoff"
    if relative.startswith("submission/"):
        return "scripts/build_submission.py", "make submission"
    raise ValueError(f"No provenance generator mapping for {relative}")


def main() -> None:
    config = ROOT / "config" / "model.yml"
    structural_config = ROOT / "config" / "structural_replication.yml"
    dispatch_config = ROOT / "config" / "finite_dispatch.yml"
    snapshots = ROOT / "data" / "metadata" / "data_snapshots.csv"
    cube = ROOT / "data" / "processed" / "analysis_cube_2023.nc"
    reference_ledger = ROOT / "provenance" / "reference_verification.csv"
    technology_parameters = ROOT / "data" / "metadata" / "technology_parameters.csv"
    source_workbook = (
        ROOT
        / "data"
        / "raw"
        / "real_heat_cases"
        / "frontier_figshare_v4_20260924T115656Z"
        / "frontier_hpc_facility_data_v4.xlsx"
    )
    canonical = sorted((ROOT / "results" / "canonical").glob("*.csv"))
    diagnostics = sorted((ROOT / "results" / "diagnostics").glob("*.csv"))
    dispatch = sorted(
        path for path in (ROOT / "results" / "dispatch").glob("*") if path.is_file()
    )
    figures = sorted((ROOT / "results" / "figures").glob("*.*"))
    tables = sorted((ROOT / "results" / "tables").glob("*.csv"))
    handoff = [
        ROOT / "docs" / "GLOBAL_ANALYSIS_RESULTS.md",
        ROOT / "docs" / "STRUCTURAL_UNCERTAINTY.md",
        ROOT / "docs" / "PHASE_F_HANDOFF.md",
        ROOT / "docs" / "PHASE_G_HANDOFF.md",
    ]
    submission = sorted(
        path for path in (ROOT / "submission").rglob("*") if path.is_file()
    )
    artifacts = (
        canonical + diagnostics + dispatch + figures + tables + handoff + submission
    )
    required = [
        config,
        structural_config,
        dispatch_config,
        snapshots,
        cube,
        reference_ledger,
        technology_parameters,
        source_workbook,
        *artifacts,
    ]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing provenance inputs: {missing}")

    canonical_inputs = [cube, config, snapshots]
    global_diagnostics = [
        path for path in diagnostics if path.name != "finite_dispatch_validation.csv"
    ]
    result_inputs = canonical + global_diagnostics + [config]
    structural_inputs = [structural_config, snapshots]
    structural_result = ROOT / "results" / "tables" / "structural_replication.csv"
    dispatch_summary = ROOT / "results" / "dispatch" / "finite_dispatch_summary.csv"
    dispatch_timeseries = (
        ROOT / "results" / "dispatch" / "finite_dispatch_timeseries.csv.gz"
    )
    dispatch_validation = (
        ROOT / "results" / "diagnostics" / "finite_dispatch_validation.csv"
    )
    dispatch_inputs = [
        dispatch_config,
        technology_parameters,
        source_workbook,
    ]
    submission_inputs = (
        figures + tables + canonical + global_diagnostics + [reference_ledger]
    )
    revision = _git_revision()
    environment = _environment()
    verified = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    rows: list[dict[str, str]] = []
    for artifact in artifacts:
        generator, command = _generator(artifact)
        relative = str(artifact.relative_to(ROOT))
        is_structural = relative in {
            "results/tables/structural_replication.csv",
            "docs/STRUCTURAL_UNCERTAINTY.md",
            "docs/PHASE_F_HANDOFF.md",
        }
        is_dispatch = relative.startswith("results/dispatch/") or relative in {
            "results/diagnostics/finite_dispatch_validation.csv",
            "docs/PHASE_G_HANDOFF.md",
        }
        if relative == "docs/PHASE_G_HANDOFF.md":
            inputs = [dispatch_summary, dispatch_validation]
        elif relative == "results/diagnostics/finite_dispatch_validation.csv":
            inputs = [dispatch_summary, dispatch_timeseries]
        elif relative.startswith("results/dispatch/"):
            inputs = dispatch_inputs
        elif relative == "docs/PHASE_F_HANDOFF.md":
            inputs = [structural_result, structural_config]
        elif is_structural:
            inputs = structural_inputs
        elif relative.startswith(("results/canonical/", "results/diagnostics/")):
            inputs = canonical_inputs
        elif relative.startswith(
            ("results/figures/", "results/tables/", "docs/GLOBAL_ANALYSIS_RESULTS.md")
        ):
            inputs = result_inputs
        else:
            inputs = submission_inputs
        rows.append(
            {
                "artifact": relative,
                "field_or_claim": "entire generated artifact",
                "canonical_source": _hash_listing(inputs),
                "generating_code": generator,
                "config_sha256": _sha256(
                    structural_config
                    if is_structural
                    else dispatch_config
                    if is_dispatch
                    else config
                ),
                "code_revision": revision,
                "command": command,
                "environment": environment,
                "input_hashes": _inputs(inputs),
                "output_sha256": _sha256(artifact),
                "verified_utc": verified,
            }
        )

    claim_sources = {
        "matched temporal-versus-spatial fraction": (
            ROOT / "results" / "canonical" / "matched_event_allocations.csv"
        ),
        "finite-Q source-removal nonlinearity": (
            ROOT / "results" / "canonical" / "finite_q_sensitivity.csv"
        ),
        "conditional source-hotspot scenarios": (
            ROOT / "results" / "canonical" / "source_hotspot_robustness.csv"
        ),
        "exclusion-mask-ablation sink geography": (
            ROOT / "results" / "canonical" / "safety_ablation.csv"
        ),
    }
    manuscript = ROOT / "submission" / "manuscript_applied_energy.docx"
    for claim, source in claim_sources.items():
        rows.append(
            {
                "artifact": str(manuscript.relative_to(ROOT)),
                "field_or_claim": claim,
                "canonical_source": f"{source.relative_to(ROOT)}={_sha256(source)}",
                "generating_code": "scripts/build_submission.py",
                "config_sha256": _sha256(config),
                "code_revision": revision,
                "command": "make submission",
                "environment": environment,
                "input_hashes": _inputs([source, config]),
                "output_sha256": _sha256(manuscript),
                "verified_utc": verified,
            }
        )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    temporary = OUTPUT.with_name(f".{OUTPUT.name}.tmp")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, OUTPUT)
    print(f"Wrote {len(rows)} numerical provenance rows.")


if __name__ == "__main__":
    main()
