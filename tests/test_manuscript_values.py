import hashlib
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "provenance" / "manuscript_values.csv"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def test_manuscript_value_ledger_rebuilds_from_current_results() -> None:
    before = LEDGER.read_bytes()
    subprocess.run(
        [sys.executable, "scripts/build_manuscript_values.py"],
        cwd=ROOT,
        check=True,
    )
    assert LEDGER.read_bytes() == before


def test_manuscript_values_have_unique_traceable_sources() -> None:
    ledger = pd.read_csv(LEDGER, dtype=str, keep_default_na=False)

    assert len(ledger) == 76
    assert ledger["value_id"].is_unique
    assert not ledger.eq("").any(axis=None)

    for row in ledger.itertuples(index=False):
        source = ROOT / row.source_artifact
        assert source.is_file()
        assert _sha256(source) == row.source_sha256


def test_frozen_key_values_match_analysis_outputs() -> None:
    ledger = pd.read_csv(LEDGER).set_index("value_id")
    matched = pd.read_csv(ROOT / "results/canonical/matched_event_allocations.csv")
    source = pd.read_csv(ROOT / "results/techno_economic/frontier_source_potential.csv")
    demand = pd.read_csv(ROOT / "data/metadata/ornl_demand_summary.csv")

    spatial = matched.loc[matched["analysis"].eq("spatial")].iloc[0]
    temporal = matched.loc[matched["analysis"].eq("temporal")].iloc[0]
    case_a_average = demand.loc[demand["record_id"].eq("case_a_average")].iloc[0]
    observed_heat = source.loc[
        source["metric"].eq("observed_waste_heat_energy"), "value"
    ].iloc[0]

    assert ledger.loc["matched_spatial_value", "value"] == pytest.approx(
        spatial["net_benefit"]
    )
    assert ledger.loc["matched_temporal_value", "value"] == pytest.approx(
        temporal["net_benefit"]
    )
    assert ledger.loc["frontier_observed_heat", "value"] == pytest.approx(observed_heat)
    assert ledger.loc["ornl_case_a_average", "value"] == pytest.approx(
        case_a_average["value_mw_th"]
    )
    assert ledger.loc["supported_practical_mode_count", "value"] == 0
    assert ledger.loc["supported_practical_mode_count", "eligibility"] == "EXCLUDED"
