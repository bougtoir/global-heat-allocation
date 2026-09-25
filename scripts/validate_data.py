"""Validate acquired public-data files and generate a canonical inventory."""

from __future__ import annotations

import csv
import json
import os
import xml.etree.ElementTree as ET
from pathlib import Path
from zipfile import ZipFile

import numpy as np
import pandas as pd
import rasterio
import xarray as xr

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "data" / "metadata" / "data_snapshots.csv"
INVENTORY = ROOT / "data" / "metadata" / "data_inventory.csv"
TECHNOLOGY_PARAMETERS = ROOT / "data" / "metadata" / "technology_parameters.csv"
TECHNOLOGY_SOURCES = ROOT / "data" / "metadata" / "technology_parameter_sources.csv"
TECHNOLOGY_PATHWAYS = ROOT / "data" / "metadata" / "technology_pathways.csv"
TECHNO_ECONOMIC_PARAMETERS = (
    ROOT / "data" / "metadata" / "techno_economic_parameters.csv"
)
TECHNO_ECONOMIC_SOURCES = (
    ROOT / "data" / "metadata" / "techno_economic_parameter_sources.csv"
)
TECHNO_ECONOMIC_RESULTS = ROOT / "results" / "techno_economic"
ENVIRONMENTAL_PARAMETERS = ROOT / "data" / "metadata" / "environmental_parameters.csv"
ENVIRONMENTAL_SOURCES = (
    ROOT / "data" / "metadata" / "environmental_parameter_sources.csv"
)
ENVIRONMENTAL_RESULTS = ROOT / "results" / "environmental_constraints"
FIELDNAMES = [
    "source_key",
    "format",
    "dimensions",
    "variables",
    "units",
    "time_start",
    "time_end",
    "minimum",
    "maximum",
    "sum",
    "valid_count",
    "status",
    "notes",
]


def _netcdf_inventory(path: Path, source_key: str) -> dict[str, object]:
    with xr.open_dataset(path) as dataset:
        variables = [name for name in dataset.data_vars if name not in {"time_bnds"}]
        if not variables:
            raise ValueError(f"No analysis variable in {path}")
        variable = dataset[variables[0]]
        sample = variable.isel(time=0) if "time" in variable.dims else variable
        values = np.asarray(sample.values, dtype=np.float64)
        finite = np.isfinite(values)
        if not finite.any():
            raise ValueError(f"No finite values in {path}")
        time_start = ""
        time_end = ""
        if "time" in dataset:
            time_start = str(pd.Timestamp(dataset.time.values[0]).isoformat())
            time_end = str(pd.Timestamp(dataset.time.values[-1]).isoformat())
        return {
            "source_key": source_key,
            "format": "NetCDF",
            "dimensions": json.dumps(dict(dataset.sizes), sort_keys=True),
            "variables": ";".join(variables),
            "units": str(variable.attrs.get("units", "")),
            "time_start": time_start,
            "time_end": time_end,
            "minimum": float(values[finite].min()),
            "maximum": float(values[finite].max()),
            "sum": "",
            "valid_count": int(finite.sum()),
            "status": "valid",
            "notes": "Range statistics use the first time slice.",
        }


def _raster_inventory(path: Path, source_key: str) -> dict[str, object]:
    total = 0.0
    valid_count = 0
    minimum = np.inf
    maximum = -np.inf
    with rasterio.open(path) as dataset:
        for _, window in dataset.block_windows(1):
            values = dataset.read(1, window=window, masked=True)
            valid = values.compressed().astype(np.float64, copy=False)
            if valid.size == 0:
                continue
            total += float(valid.sum())
            valid_count += int(valid.size)
            minimum = min(minimum, float(valid.min()))
            maximum = max(maximum, float(valid.max()))
        if valid_count == 0:
            raise ValueError(f"No valid raster cells in {path}")
        return {
            "source_key": source_key,
            "format": "GeoTIFF",
            "dimensions": json.dumps(
                {"height": dataset.height, "width": dataset.width},
                sort_keys=True,
            ),
            "variables": "population_count",
            "units": "people per pixel",
            "time_start": "",
            "time_end": "",
            "minimum": minimum,
            "maximum": maximum,
            "sum": total,
            "valid_count": valid_count,
            "status": "valid",
            "notes": (
                f"CRS={dataset.crs}; bounds={tuple(dataset.bounds)}; "
                f"resolution={dataset.res}"
            ),
        }


def _zip_inventory(path: Path, source_key: str) -> dict[str, object]:
    with ZipFile(path) as archive:
        names = archive.namelist()
        bad_member = archive.testzip()
        if bad_member is not None:
            raise ValueError(f"Corrupt ZIP member in {path}: {bad_member}")
        present_extensions = {Path(name).suffix.lower() for name in names}
        if ".shp" in present_extensions:
            required_extensions = {".shp", ".shx", ".dbf", ".prj"}
            missing = required_extensions - present_extensions
            if missing:
                raise ValueError(
                    f"Missing shapefile members in {path}: {sorted(missing)}"
                )
            archive_format = "ZIP/Shapefile"
            notes = "Archive integrity and mandatory shapefile members verified."
        else:
            archive_format = "ZIP"
            notes = "Archive integrity verified."
    return {
        "source_key": source_key,
        "format": archive_format,
        "dimensions": "",
        "variables": ";".join(sorted(names)),
        "units": "",
        "time_start": "",
        "time_end": "",
        "minimum": "",
        "maximum": "",
        "sum": "",
        "valid_count": len(names),
        "status": "valid",
        "notes": notes,
    }


def _json_inventory(path: Path, source_key: str) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if source_key == "osti_record_2329591":
        if (
            not isinstance(payload, list)
            or len(payload) != 1
            or not isinstance(payload[0], dict)
            or str(payload[0].get("osti_id")) != "2329591"
        ):
            raise ValueError(f"Invalid OSTI record structure in {path}")
        return {
            "source_key": source_key,
            "format": "JSON/OSTI API v1",
            "dimensions": json.dumps({"records": len(payload)}),
            "variables": ";".join(sorted(payload[0])),
            "units": "",
            "time_start": "",
            "time_end": "",
            "minimum": "",
            "maximum": "",
            "sum": "",
            "valid_count": len(payload),
            "status": "valid",
            "notes": "OSTI record identifier and single-record response verified.",
        }
    if not isinstance(payload, dict):
        raise ValueError(f"Expected a JSON object in {path}")
    if source_key.startswith("eia_tennessee_commercial_"):
        response = payload.get("response")
        if not isinstance(response, dict) or not isinstance(response.get("data"), list):
            raise ValueError(f"Invalid EIA response structure in {path}")
        total = int(response.get("total", -1))
        if total != len(response["data"]):
            raise ValueError(
                f"Incomplete EIA response in {path}: "
                f"{len(response['data'])} of {total} rows"
            )
        variables = {
            key for row in response["data"] if isinstance(row, dict) for key in row
        }
        return {
            "source_key": source_key,
            "format": "JSON/EIA API v2",
            "dimensions": json.dumps({"rows": total}),
            "variables": ";".join(sorted(variables)),
            "units": "",
            "time_start": "",
            "time_end": "",
            "minimum": "",
            "maximum": "",
            "sum": "",
            "valid_count": total,
            "status": "valid",
            "notes": "EIA response structure and complete requested page verified.",
        }
    return {
        "source_key": source_key,
        "format": "JSON",
        "dimensions": json.dumps({"top_level_fields": len(payload)}),
        "variables": ";".join(sorted(payload)),
        "units": "",
        "time_start": "",
        "time_end": "",
        "minimum": "",
        "maximum": "",
        "sum": "",
        "valid_count": len(payload),
        "status": "valid",
        "notes": "JSON syntax and top-level object structure verified.",
    }


def _xml_inventory(path: Path, source_key: str) -> dict[str, object]:
    root = ET.parse(path).getroot()
    elements = list(root.iter())
    if not elements:
        raise ValueError(f"Empty XML document in {path}")
    return {
        "source_key": source_key,
        "format": "XML",
        "dimensions": json.dumps({"elements": len(elements)}),
        "variables": ";".join(sorted({element.tag for element in elements})),
        "units": "",
        "time_start": "",
        "time_end": "",
        "minimum": "",
        "maximum": "",
        "sum": "",
        "valid_count": len(elements),
        "status": "valid",
        "notes": "Well-formed XML response preserved as an immutable source snapshot.",
    }


def _pdf_inventory(path: Path, source_key: str) -> dict[str, object]:
    with path.open("rb") as handle:
        if handle.read(5) != b"%PDF-":
            raise ValueError(f"Invalid PDF signature: {path}")
    return {
        "source_key": source_key,
        "format": "PDF",
        "dimensions": "",
        "variables": "",
        "units": "",
        "time_start": "",
        "time_end": "",
        "minimum": "",
        "maximum": "",
        "sum": "",
        "valid_count": path.stat().st_size,
        "status": "valid",
        "notes": "PDF signature verified; valid_count reports bytes.",
    }


def _frontier_xlsx_inventory(path: Path, source_key: str) -> dict[str, object]:
    sheet = "Frontier2023"
    data = pd.read_excel(path, sheet_name=sheet, skiprows=[1])
    required = {
        "Date/Time",
        "Overall-average Coolant Return Temp",
        "Overall Coolant Supply Temp",
        "Overall_WasteHeat",
        "Frontier Total Power",
    }
    missing = required - set(data.columns)
    if missing:
        raise ValueError(f"Missing Frontier variables in {path}: {sorted(missing)}")
    timestamps = pd.to_datetime(data["Date/Time"], errors="raise")
    if timestamps.duplicated().any():
        raise ValueError(f"Duplicate Frontier timestamps in {path}")
    heat = pd.to_numeric(data["Overall_WasteHeat"], errors="raise")
    if (heat < 0).any():
        raise ValueError(f"Negative Frontier waste heat in {path}")
    return {
        "source_key": source_key,
        "format": "XLSX",
        "dimensions": json.dumps(
            {"rows": len(data), "columns": len(data.columns), "sheet": sheet},
            sort_keys=True,
        ),
        "variables": ";".join(str(column) for column in data.columns),
        "units": "Workbook units row: timestamp; deg C; gpm; MW",
        "time_start": timestamps.min().isoformat(),
        "time_end": timestamps.max().isoformat(),
        "minimum": float(heat.min()),
        "maximum": float(heat.max()),
        "sum": "",
        "valid_count": int(heat.notna().sum()),
        "status": "valid",
        "notes": "Required source, grade, heat, and power variables verified.",
    }


def _technology_xlsx_inventory(path: Path, source_key: str) -> dict[str, object]:
    workbook = pd.ExcelFile(path)
    expected_sheets = {
        "denmark_energy_plants_datasheets_2026_08": {"40 Comp. hp, waste heat 1 MW"},
        "denmark_energy_storage_datasheets_v0011": {
            "141a TTES",
            "141b Large TTES",
        },
    }.get(source_key)
    if expected_sheets is None:
        raise ValueError(f"Unsupported technology workbook: {source_key}")
    missing = expected_sheets - set(workbook.sheet_names)
    if missing:
        raise ValueError(f"Missing required sheets in {path}: {sorted(missing)}")
    dimensions = {
        sheet: list(pd.read_excel(path, sheet_name=sheet, header=None).shape)
        for sheet in sorted(expected_sheets)
    }
    return {
        "source_key": source_key,
        "format": "XLSX",
        "dimensions": json.dumps(dimensions, sort_keys=True),
        "variables": ";".join(workbook.sheet_names),
        "units": "Mixed technology-specific units documented in workbook",
        "time_start": "",
        "time_end": "",
        "minimum": "",
        "maximum": "",
        "sum": "",
        "valid_count": len(workbook.sheet_names),
        "status": "valid",
        "notes": "Workbook structure and required technology sheets verified.",
    }


def _phase_d_xlsx_inventory(path: Path, source_key: str) -> dict[str, object]:
    workbook = pd.ExcelFile(path)
    expected_sheets = {
        "epa_ghg_emission_factors_hub_2025": {"Emission Factors Hub"},
        "epa_egrid_summary_tables_2023_rev2": {
            "Contents",
            "Table 1",
            "Table 2",
            "Table 3",
            "Table 4",
        },
    }.get(source_key)
    if expected_sheets is None:
        raise ValueError(f"Unsupported Phase D workbook: {source_key}")
    missing = expected_sheets - set(workbook.sheet_names)
    if missing:
        raise ValueError(f"Missing required sheets in {path}: {sorted(missing)}")
    if source_key == "epa_ghg_emission_factors_hub_2025":
        data = pd.read_excel(path, sheet_name="Emission Factors Hub", header=None)
        required_text = {"Natural Gas", "Steam and Heat"}
    else:
        data = pd.read_excel(path, sheet_name="Table 1", header=None)
        required_text = {"SRTV"}
    text = set(data.astype(str).to_numpy().ravel())
    absent = required_text - text
    if absent:
        raise ValueError(f"Missing required records in {path}: {sorted(absent)}")
    return {
        "source_key": source_key,
        "format": "XLSX",
        "dimensions": json.dumps(
            {"sheets": len(workbook.sheet_names)},
            sort_keys=True,
        ),
        "variables": ";".join(workbook.sheet_names),
        "units": "Mixed source-specific units documented in workbook",
        "time_start": "",
        "time_end": "",
        "minimum": "",
        "maximum": "",
        "sum": "",
        "valid_count": len(workbook.sheet_names),
        "status": "valid",
        "notes": "Workbook structure and required Phase D records verified.",
    }


def _html_inventory(path: Path, source_key: str) -> dict[str, object]:
    text = path.read_text(encoding="utf-8")
    if source_key == "ornl_publication_page_2329591":
        required = {
            "ORNL Campus Sustainability and Decarbonization",
            "Publication",
            "04/16/2024",
        }
        variables = "ORNL publication title;publication type;publication date"
        units = ""
        time_start = ""
        time_end = ""
        notes = "ORNL publication identity records verified."
    else:
        required = {"Foreign Exchange Rates", "EURO", "1.1306"}
        variables = "2025 annual average EUR/USD exchange rate"
        units = "USD per EUR"
        time_start = "2025"
        time_end = "2025"
        notes = "Federal Reserve release title, currency, and value verified."
    missing = {value for value in required if value not in text}
    if missing:
        raise ValueError(f"Missing required HTML records in {path}: {sorted(missing)}")
    return {
        "source_key": source_key,
        "format": "HTML",
        "dimensions": "",
        "variables": variables,
        "units": units,
        "time_start": time_start,
        "time_end": time_end,
        "minimum": "",
        "maximum": "",
        "sum": "",
        "valid_count": path.stat().st_size,
        "status": "valid",
        "notes": notes,
    }


def _sonderborg_csv_inventory(path: Path, source_key: str) -> dict[str, object]:
    data = pd.read_csv(path, sep=";")
    required = {"date"}
    required.update(f"plant{plant}_heat_load" for plant in range(1, 8))
    required.update(f"plant{plant}_temp_feed_flow" for plant in range(1, 8))
    required.update(f"plant{plant}_temp_back_flow" for plant in range(1, 8))
    missing = required - set(data.columns)
    if missing:
        raise ValueError(f"Missing Sønderborg variables in {path}: {sorted(missing)}")
    local_timestamps = pd.to_datetime(data["date"], errors="raise")
    timestamps = local_timestamps.dt.tz_localize(
        "Europe/Copenhagen",
        ambiguous="infer",
        nonexistent="raise",
    ).dt.tz_convert("UTC")
    if timestamps.duplicated().any() or not timestamps.is_monotonic_increasing:
        raise ValueError(f"Invalid Sønderborg timestamp sequence in {path}")
    heat_columns = [f"plant{plant}_heat_load" for plant in range(1, 8)]
    heat = data[heat_columns].apply(pd.to_numeric, errors="raise")
    return {
        "source_key": source_key,
        "format": "CSV",
        "dimensions": json.dumps(
            {"rows": len(data), "columns": len(data.columns)}, sort_keys=True
        ),
        "variables": ";".join(str(column) for column in data.columns),
        "units": "MW for heat load; deg C for feed and return temperatures",
        "time_start": timestamps.min().isoformat(),
        "time_end": timestamps.max().isoformat(),
        "minimum": float(heat.min().min()),
        "maximum": float(heat.max().max()),
        "sum": "",
        "valid_count": int(heat.notna().sum().sum()),
        "status": "valid",
        "notes": (
            "Local timestamps were disambiguated with Europe/Copenhagen daylight "
            "saving rules; seven-plant heat/temperature schema verified."
        ),
    }


def _write_inventory(rows: list[dict[str, object]]) -> None:
    temporary = INVENTORY.with_name(f".{INVENTORY.name}.tmp")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, INVENTORY)


def _validate_technology_tables(ledger: pd.DataFrame) -> None:
    parameters = pd.read_csv(
        TECHNOLOGY_PARAMETERS,
        dtype=str,
        keep_default_na=False,
    )
    sources = pd.read_csv(
        TECHNOLOGY_SOURCES,
        dtype=str,
        keep_default_na=False,
    )
    pathways = pd.read_csv(
        TECHNOLOGY_PATHWAYS,
        dtype=str,
        keep_default_na=False,
    )
    if parameters["parameter_id"].duplicated().any():
        raise ValueError("Duplicate technology parameter IDs.")
    if sources["source_id"].duplicated().any():
        raise ValueError("Duplicate technology parameter source IDs.")
    if pathways["pathway_id"].duplicated().any():
        raise ValueError("Duplicate technology pathway IDs.")
    pathway_ids = set(pathways["pathway_id"])
    if pathway_ids != {"A", "B", "C", "D", "E"}:
        raise ValueError(f"Expected technology pathways A-E, found {pathway_ids}")
    if not set(pathways["finite_dispatch_ready"]) <= {"true", "false"}:
        raise ValueError("Invalid finite_dispatch_ready value.")
    valid_sources = set(sources["source_id"])
    valid_source_keys = set(
        ledger.loc[ledger["completion"].eq("complete"), "source_key"]
    )
    if not set(sources["source_key"]) <= valid_source_keys:
        missing = set(sources["source_key"]) - valid_source_keys
        raise ValueError(f"Technology source keys missing from data ledger: {missing}")
    for record in parameters.to_dict(orient="records"):
        referenced_pathways = set(str(record["pathways"]).split(";"))
        if not referenced_pathways <= pathway_ids:
            raise ValueError(
                f"Invalid pathway for {record['parameter_id']}: "
                f"{referenced_pathways - pathway_ids}"
            )
        referenced_sources = {
            source_id for source_id in str(record["source_ids"]).split(";") if source_id
        }
        if not referenced_sources <= valid_sources:
            raise ValueError(
                f"Invalid sources for {record['parameter_id']}: "
                f"{referenced_sources - valid_sources}"
            )
        value_kind = str(record["value_kind"])
        if value_kind not in {
            "definition",
            "direct_source",
            "derived",
            "scenario",
            "missing_required",
        }:
            raise ValueError(
                f"Invalid value kind for {record['parameter_id']}: {value_kind}"
            )
        if value_kind == "direct_source" and not referenced_sources:
            raise ValueError(f"Direct parameter lacks source: {record['parameter_id']}")
        if value_kind == "derived" and (
            not referenced_sources or not record["derivation"]
        ):
            raise ValueError(
                f"Derived parameter lacks provenance: {record['parameter_id']}"
            )
        if value_kind == "scenario" and not record["derivation"]:
            raise ValueError(
                f"Scenario parameter lacks definition: {record['parameter_id']}"
            )
        if value_kind == "missing_required" and (
            record["value"]
            or record["case_role"] != "exclusion_gate"
            or not record["limitation"]
        ):
            raise ValueError(
                f"Missing parameter is not an explicit gate: {record['parameter_id']}"
            )
    indexed = parameters.set_index("parameter_id")
    if indexed.loc["transport_case_loss_function", "value_kind"] != "missing_required":
        raise ValueError("Transport loss function must remain an open evidence gate.")
    if (
        indexed.loc["storage_case_return_temperature_c", "value_kind"]
        != "missing_required"
    ):
        raise ValueError(
            "Storage return temperature must remain an open evidence gate."
        )
    if set(
        pathways.loc[
            pathways["pathway_id"].isin(["B", "D", "E"]),
            "phase_d_use",
        ]
    ) != {"sensitivity_only"}:
        raise ValueError("Storage and transport pathways must remain sensitivity-only.")


def _validate_techno_economic_tables(ledger: pd.DataFrame) -> None:
    parameters = pd.read_csv(
        TECHNO_ECONOMIC_PARAMETERS,
        dtype=str,
        keep_default_na=False,
    )
    sources = pd.read_csv(
        TECHNO_ECONOMIC_SOURCES,
        dtype=str,
        keep_default_na=False,
    )
    if parameters["parameter_id"].duplicated().any():
        raise ValueError("Duplicate techno-economic parameter IDs.")
    if sources["source_id"].duplicated().any():
        raise ValueError("Duplicate techno-economic parameter source IDs.")
    valid_source_keys = set(
        ledger.loc[ledger["completion"].eq("complete"), "source_key"]
    )
    if not set(sources["source_key"]) <= valid_source_keys:
        missing = set(sources["source_key"]) - valid_source_keys
        raise ValueError(
            f"Techno-economic source keys missing from data ledger: {missing}"
        )
    valid_sources = set(sources["source_id"])
    for record in parameters.to_dict(orient="records"):
        referenced_sources = {
            source_id for source_id in record["source_ids"].split(";") if source_id
        }
        if not referenced_sources <= valid_sources:
            raise ValueError(
                f"Invalid sources for {record['parameter_id']}: "
                f"{referenced_sources - valid_sources}"
            )
        value_kind = record["value_kind"]
        if value_kind not in {
            "direct_source",
            "derived",
            "scenario",
            "missing_required",
        }:
            raise ValueError(
                f"Invalid techno-economic value kind for "
                f"{record['parameter_id']}: {value_kind}"
            )
        if value_kind == "direct_source" and not referenced_sources:
            raise ValueError(f"Direct parameter lacks source: {record['parameter_id']}")
        if value_kind == "derived" and (
            not referenced_sources or not record["derivation"]
        ):
            raise ValueError(
                f"Derived parameter lacks provenance: {record['parameter_id']}"
            )
        if value_kind == "scenario" and not record["derivation"]:
            raise ValueError(
                f"Scenario parameter lacks definition: {record['parameter_id']}"
            )
        if value_kind == "missing_required" and (
            record["value"] or not record["limitation"]
        ):
            raise ValueError(
                f"Missing parameter is not an explicit gate: {record['parameter_id']}"
            )

    indexed = parameters.set_index("parameter_id")
    required_gates = {
        "case_auxiliary_electricity_fraction",
        "case_source_capture_efficiency",
        "case_full_installed_cost",
        "transport_network_capex",
        "equipment_embodied_co2e",
        "case_hourly_receiving_demand",
        "case_total_residual_rejection",
    }
    if not required_gates <= set(indexed.index):
        raise ValueError(
            f"Missing required Phase D gates: {required_gates - set(indexed.index)}"
        )
    if (
        not indexed.loc[
            sorted(required_gates),
            "value_kind",
        ]
        .eq("missing_required")
        .all()
    ):
        raise ValueError("Required Phase D evidence gates must remain open.")

    energy = pd.read_csv(TECHNO_ECONOMIC_RESULTS / "energy_emissions.csv")
    economics = pd.read_csv(TECHNO_ECONOMIC_RESULTS / "economics.csv")
    sensitivity = pd.read_csv(TECHNO_ECONOMIC_RESULTS / "sensitivity.csv")
    source_potential = pd.read_csv(
        TECHNO_ECONOMIC_RESULTS / "frontier_source_potential.csv"
    )
    if energy["scenario_id"].duplicated().any():
        raise ValueError("Duplicate energy/emissions scenario IDs.")
    if not np.allclose(
        energy["thermal_balance_error_mwh"],
        0.0,
        rtol=0.0,
        atol=1e-12,
    ):
        raise ValueError("Phase D thermal energy balance does not close.")
    if set(energy["pathway_id"]) != {"A", "B", "C", "D", "E"}:
        raise ValueError("Phase D energy/emissions table must cover pathways A-E.")
    if len(sensitivity) < 1000:
        raise ValueError("Phase D sensitivity grid is unexpectedly narrow.")
    if not (
        sensitivity["avoided_operational_co2e_kg_per_mwh"].lt(0).any()
        and sensitivity["avoided_operational_co2e_kg_per_mwh"].gt(0).any()
    ):
        raise ValueError("Sensitivity results must preserve both emissions signs.")
    if not (
        sensitivity["incremental_npc_usd2025"].lt(0).any()
        and sensitivity["incremental_npc_usd2025"].gt(0).any()
    ):
        raise ValueError("Sensitivity results must preserve both economic signs.")
    incomplete_case = economics.loc[
        economics["scenario_id"].eq("C_case_calibrated_incomplete_cost")
    ]
    if (
        len(incomplete_case) != 1
        or incomplete_case["lcoh_usd2025_per_mwh_th"].notna().any()
    ):
        raise ValueError("Case-specific economics must remain withheld.")
    potential = source_potential.set_index("metric")["value"]
    if potential["missing_timestamps"] <= 0:
        raise ValueError("Frontier missing timestamps must remain explicit.")


def _validate_environmental_tables(ledger: pd.DataFrame) -> None:
    parameters = pd.read_csv(
        ENVIRONMENTAL_PARAMETERS,
        dtype=str,
        keep_default_na=False,
    )
    sources = pd.read_csv(
        ENVIRONMENTAL_SOURCES,
        dtype=str,
        keep_default_na=False,
    )
    receiving = pd.read_csv(
        ENVIRONMENTAL_RESULTS / "receiving_class_constraints.csv",
        dtype=str,
        keep_default_na=False,
    )
    pathways = pd.read_csv(
        ENVIRONMENTAL_RESULTS / "frontier_pathway_assessment.csv",
        dtype=str,
        keep_default_na=False,
    )
    storage = pd.read_csv(ENVIRONMENTAL_RESULTS / "storage_capacity_sensitivity.csv")
    if parameters["parameter_id"].duplicated().any():
        raise ValueError("Duplicate environmental parameter IDs.")
    if sources["source_id"].duplicated().any():
        raise ValueError("Duplicate environmental source IDs.")
    valid_source_keys = set(
        ledger.loc[ledger["completion"].eq("complete"), "source_key"]
    )
    if not set(sources["source_key"]) <= valid_source_keys:
        missing = set(sources["source_key"]) - valid_source_keys
        raise ValueError(
            f"Environmental source keys missing from data ledger: {missing}"
        )
    required_source_keys = {
        "epa_thermal_discharges_npdes_2023",
        "epa_tennessee_water_quality_standards_2024",
        "doe_orr_aser_2024",
    }
    if not required_source_keys <= set(sources["source_key"]):
        raise ValueError(
            "Missing authoritative Phase E sources: "
            f"{required_source_keys - set(sources['source_key'])}"
        )
    valid_sources = set(sources["source_id"])
    for record in parameters.to_dict(orient="records"):
        referenced_sources = {
            source_id for source_id in record["source_ids"].split(";") if source_id
        }
        if not referenced_sources <= valid_sources:
            raise ValueError(
                f"Invalid sources for {record['parameter_id']}: "
                f"{referenced_sources - valid_sources}"
            )
        value_kind = record["value_kind"]
        if value_kind not in {"direct_source", "derived", "missing_required"}:
            raise ValueError(
                f"Invalid environmental value kind for "
                f"{record['parameter_id']}: {value_kind}"
            )
        if value_kind == "direct_source" and not referenced_sources:
            raise ValueError(f"Direct parameter lacks source: {record['parameter_id']}")
        if value_kind == "derived" and (
            not referenced_sources or not record["derivation"]
        ):
            raise ValueError(
                f"Derived parameter lacks provenance: {record['parameter_id']}"
            )
        if value_kind == "missing_required" and (
            record["value"] or not record["limitation"]
        ):
            raise ValueError(
                f"Missing parameter is not an explicit gate: {record['parameter_id']}"
            )
    indexed = parameters.set_index("parameter_id")
    required_gates = {
        "case_surface_water_flow_m3_s",
        "case_surface_water_upstream_temperature_c",
        "case_surface_water_mixing_zone",
        "case_aquatic_biological_assessment",
        "case_storage_volume_m3",
        "case_storage_operating_delta_temperature_k",
        "case_route_sensitive_area_clearance",
        "case_cumulative_residual_heat_mwh",
    }
    if not required_gates <= set(indexed.index):
        raise ValueError(
            f"Missing required Phase E gates: {required_gates - set(indexed.index)}"
        )
    if (
        not indexed.loc[sorted(required_gates), "value_kind"]
        .eq("missing_required")
        .all()
    ):
        raise ValueError("Required Phase E evidence gates must remain open.")
    expected_receiving_classes = {
        "populated_land",
        "sparse_land",
        "sensitive_ecosystem",
        "cryosphere",
        "inland_water",
        "coastal_water",
        "open_ocean",
    }
    if set(receiving["receiving_class"]) != expected_receiving_classes:
        raise ValueError("Environmental receiving classes are incomplete.")
    external_classes = receiving.loc[
        receiving["receiving_class"].isin(
            [
                "sparse_land",
                "sensitive_ecosystem",
                "cryosphere",
                "inland_water",
                "coastal_water",
                "open_ocean",
            ]
        ),
        "practical_default",
    ]
    if external_classes.str.startswith("conditional_closed_loop").any():
        raise ValueError("External receiving classes cannot be closed-loop pathways.")
    if set(pathways["pathway_id"]) != {"A", "B", "C", "D", "E", "G", "W"}:
        raise ValueError("Phase E pathway assessment is incomplete.")
    external_pathways = pathways.loc[
        pathways["new_external_thermal_discharge"].eq("yes")
    ]
    if not external_pathways["assessment_status"].eq("excluded").all():
        raise ValueError("Unsupported external thermal discharge must be excluded.")
    if pathways["cumulative_load_value"].ne("").any():
        raise ValueError(
            "Case cumulative environmental load must remain withheld before dispatch."
        )
    if len(storage) != 9 or storage["scenario_id"].duplicated().any():
        raise ValueError("Expected nine unique storage-capacity sensitivity cases.")
    if not storage["capacity_mwh_th"].gt(0).all():
        raise ValueError("Storage-capacity sensitivity must be positive.")
    reference = storage.loc[
        storage["scenario_id"].eq("tank_5000m3_delta_55K"),
        "capacity_mwh_th",
    ]
    if len(reference) != 1 or not np.isclose(reference.iloc[0], 290.0):
        raise ValueError("Storage sensitivity does not reproduce the source reference.")


def main() -> None:
    ledger = pd.read_csv(LEDGER)
    rows: list[dict[str, object]] = []
    for record in ledger.to_dict(orient="records"):
        if str(record["completion"]) != "complete":
            print(
                "Skipped explicitly incomplete acquisition record "
                f"{record['source_key']}."
            )
            continue
        path = ROOT / str(record["local_path"])
        suffix = path.suffix.lower()
        if suffix == ".nc":
            row = _netcdf_inventory(path, str(record["source_key"]))
        elif suffix in {".tif", ".tiff"}:
            row = _raster_inventory(path, str(record["source_key"]))
        elif suffix == ".zip":
            row = _zip_inventory(path, str(record["source_key"]))
        elif suffix == ".json":
            row = _json_inventory(path, str(record["source_key"]))
        elif suffix == ".xml":
            row = _xml_inventory(path, str(record["source_key"]))
        elif suffix == ".pdf":
            row = _pdf_inventory(path, str(record["source_key"]))
        elif suffix == ".xlsx":
            source_key = str(record["source_key"])
            if source_key == "frontier_hpc_facility_data_v4":
                row = _frontier_xlsx_inventory(path, source_key)
            elif source_key in {
                "epa_ghg_emission_factors_hub_2025",
                "epa_egrid_summary_tables_2023_rev2",
            }:
                row = _phase_d_xlsx_inventory(path, source_key)
            else:
                row = _technology_xlsx_inventory(path, source_key)
        elif suffix == ".csv":
            row = _sonderborg_csv_inventory(path, str(record["source_key"]))
        elif suffix in {".html", ".htm"}:
            row = _html_inventory(path, str(record["source_key"]))
        else:
            raise ValueError(f"Unsupported data format: {path}")
        rows.append(row)
        print(f"Validated {record['source_key']}.")
    _validate_technology_tables(ledger)
    print("Validated Phase C technology parameter tables.")
    _validate_techno_economic_tables(ledger)
    print("Validated Phase D techno-economic and emissions tables.")
    _validate_environmental_tables(ledger)
    print("Validated Phase E environmental constraint tables.")
    _write_inventory(rows)


if __name__ == "__main__":
    main()
