from pathlib import Path

import pandas as pd

from scripts import build_constraint_waterfall

ROOT = Path(__file__).resolve().parents[1]


def test_constraint_waterfall_separates_units_and_has_no_supported_endpoint() -> None:
    rows = pd.read_csv(
        ROOT / "results" / "tables" / "global_to_real_constraint_waterfall.csv"
    ).fillna("")

    assert set(rows["waterfall_id"]) == {"burden_space", "physical_energy"}
    burden = rows.loc[rows["waterfall_id"].eq("burden_space")]
    physical = rows.loc[rows["waterfall_id"].eq("physical_energy")]
    assert set(burden["unit"]) == {"burden_units_per_GJ"}
    assert set(physical["unit"]) == {"MWh_th"}
    endpoints = rows.loc[rows["stage_id"].eq("practical_supported_endpoint")]
    assert endpoints["value"].eq("").all()
    assert endpoints["eligibility"].eq("EXCLUDED").all()


def test_constraint_waterfall_matches_canonical_and_dispatch_outputs() -> None:
    matched = pd.read_csv(build_constraint_waterfall.MATCHED)
    dispatch = pd.read_csv(build_constraint_waterfall.DISPATCH)
    expected_rows = pd.DataFrame(
        build_constraint_waterfall._burden_rows(matched)
        + build_constraint_waterfall._physical_rows(dispatch)
    ).fillna("")
    actual_rows = pd.read_csv(build_constraint_waterfall.OUTPUT).fillna("")

    pd.testing.assert_frame_equal(
        actual_rows[build_constraint_waterfall.FIELDS],
        expected_rows[build_constraint_waterfall.FIELDS],
        check_like=False,
    )
