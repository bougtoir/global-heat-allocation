from zipfile import ZipFile

import pandas as pd

from scripts.validate_data import (
    _phase_d_xlsx_inventory,
    _sonderborg_csv_inventory,
    _technology_xlsx_inventory,
    _validate_environmental_tables,
    _validate_techno_economic_tables,
    _validate_technology_tables,
    _zip_inventory,
)


def test_sonderborg_inventory_disambiguates_autumn_dst_hour(tmp_path) -> None:
    path = tmp_path / "sonderborg.csv"
    timestamps = [
        "2019-10-27 02:00:00",
        "2019-10-27 02:15:00",
        "2019-10-27 02:30:00",
        "2019-10-27 02:45:00",
        "2019-10-27 02:00:00",
        "2019-10-27 02:15:00",
        "2019-10-27 02:30:00",
        "2019-10-27 02:45:00",
    ]
    data: dict[str, object] = {"date": timestamps}
    for plant in range(1, 8):
        data[f"plant{plant}_heat_load"] = [float(plant)] * len(timestamps)
        data[f"plant{plant}_temp_feed_flow"] = [80.0] * len(timestamps)
        data[f"plant{plant}_temp_back_flow"] = [40.0] * len(timestamps)
    pd.DataFrame(data).to_csv(path, sep=";", index=False)

    inventory = _sonderborg_csv_inventory(path, "sonderborg")

    assert inventory["status"] == "valid"
    assert inventory["valid_count"] == 56
    assert inventory["time_start"] == "2019-10-27T00:00:00+00:00"
    assert inventory["time_end"] == "2019-10-27T01:45:00+00:00"


def test_generic_zip_inventory_does_not_require_shapefile_members(tmp_path) -> None:
    path = tmp_path / "workbooks.zip"
    with ZipFile(path, "w") as archive:
        archive.writestr("raw data/measurements.xlsx", b"placeholder")

    inventory = _zip_inventory(path, "workbooks")

    assert inventory["format"] == "ZIP"
    assert inventory["valid_count"] == 1
    assert inventory["status"] == "valid"


def test_technology_workbook_requires_expected_sheets(tmp_path) -> None:
    path = tmp_path / "storage.xlsx"
    with pd.ExcelWriter(path) as writer:
        pd.DataFrame({"parameter": ["capacity"], "value": [290]}).to_excel(
            writer,
            sheet_name="141a TTES",
            index=False,
        )
        pd.DataFrame({"parameter": ["capacity"], "value": [2880]}).to_excel(
            writer,
            sheet_name="141b Large TTES",
            index=False,
        )

    inventory = _technology_xlsx_inventory(
        path,
        "denmark_energy_storage_datasheets_v0011",
    )

    assert inventory["status"] == "valid"
    assert inventory["valid_count"] == 2
    assert "141a TTES" in str(inventory["dimensions"])


def test_phase_c_technology_tables_are_valid() -> None:
    ledger = pd.read_csv("data/metadata/data_snapshots.csv", dtype=str)

    _validate_technology_tables(ledger)


def test_phase_d_workbook_inventory_accepts_required_records() -> None:
    path = (
        "data/raw/techno_economic_sources/phase_d_20260924/"
        "egrid2023_summary_tables_rev2.xlsx"
    )

    inventory = _phase_d_xlsx_inventory(
        path,
        "epa_egrid_summary_tables_2023_rev2",
    )

    assert inventory["status"] == "valid"
    assert inventory["valid_count"] == 5


def test_phase_d_techno_economic_tables_are_valid() -> None:
    ledger = pd.read_csv("data/metadata/data_snapshots.csv", dtype=str)

    _validate_techno_economic_tables(ledger)


def test_phase_e_environmental_tables_are_valid() -> None:
    ledger = pd.read_csv("data/metadata/data_snapshots.csv", dtype=str)

    _validate_environmental_tables(ledger)
