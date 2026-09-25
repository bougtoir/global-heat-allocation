from pathlib import Path

import pandas as pd

from scripts import build_case_specific_evidence

ROOT = Path(__file__).resolve().parents[1]


def test_case_specific_evidence_matches_generator() -> None:
    actual = pd.read_csv(ROOT / "provenance" / "case_specific_evidence.csv").fillna("")
    expected = pd.DataFrame(build_case_specific_evidence._rows()).fillna("")

    pd.testing.assert_frame_equal(
        actual[build_case_specific_evidence.FIELDS],
        expected[build_case_specific_evidence.FIELDS],
        check_like=False,
    )


def test_case_specific_evidence_statuses_and_required_items() -> None:
    rows = pd.DataFrame(build_case_specific_evidence._rows()).fillna("")
    required_ids = {
        "ornl_receiving_hourly_demand_profile",
        "source_capture_efficiency",
        "balance_of_plant_auxiliary_electricity",
        "route_length_and_path",
        "hydraulic_network_design_inputs",
        "case_storage_design",
        "source_outage_availability",
        "cost_and_price_year",
        "receiving_water_flow_temperature",
        "approved_mixing_zone_outfall",
        "route_footprint_environmental_clearance",
    }

    assert required_ids.issubset(set(rows["evidence_id"]))
    assert set(rows["status"]).issubset(build_case_specific_evidence.STATUS_VALUES)
    assert not rows["evidence_id"].duplicated().any()
    assert (
        rows.loc[
            rows["evidence_id"].eq("ornl_receiving_hourly_demand_profile"),
            "status",
        ].iloc[0]
        == "NOT_FOUND"
    )
    assert (
        rows.loc[
            rows["evidence_id"].eq("frontier_source_timeseries"),
            "status",
        ].iloc[0]
        == "FOUND_MEASURED"
    )
    assert (
        rows.loc[
            rows["status"].isin({"NOT_FOUND", "FOUND_BOUND_ONLY"}),
            "claim_limit",
        ]
        .str.len()
        .gt(0)
        .all()
    )
