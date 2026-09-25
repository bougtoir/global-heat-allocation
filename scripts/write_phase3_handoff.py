"""Generate the Phase 3 handoff from canonical validation outputs."""

from __future__ import annotations

import csv
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROCESSED_VALIDATION = ROOT / "data" / "metadata" / "processed_validation.csv"
SYNTHETIC_VALIDATION = ROOT / "results" / "diagnostics" / "synthetic_validation.csv"
ARTIFACTS = ROOT / "provenance" / "processed_artifacts.csv"
OUTPUT = ROOT / "docs" / "PHASE_3_HANDOFF.md"


def _read_indexed(path: Path, key: str) -> dict[str, dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return {row[key]: row for row in csv.DictReader(handle)}


def main() -> None:
    processed = _read_indexed(PROCESSED_VALIDATION, "check")
    synthetic = _read_indexed(SYNTHETIC_VALIDATION, "check")
    with ARTIFACTS.open(encoding="utf-8", newline="") as handle:
        artifact = next(csv.DictReader(handle))
    failed_processed = [
        name for name, row in processed.items() if row["status"] != "pass"
    ]
    failed_synthetic = [
        name for name, row in synthetic.items() if row["status"] != "pass"
    ]
    if failed_processed or failed_synthetic:
        raise ValueError("Cannot write Phase 3 handoff with failed validation checks.")

    population = float(processed["population_conservation"]["value"])
    maximum_delta = float(processed["maximum_one_gj_temperature_change"]["value"])
    size_mib = int(artifact["file_size_bytes"]) / 1024**2
    text = f"""# Phase 3 handoff: formal model and canonical cube

## Canonical artifact

- Artifact: `{artifact["artifact"]}`
- Size: {size_mib:.1f} MiB
- SHA-256: `{artifact["sha256"]}`
- Dimensions: {processed["time_steps"]["value"]} time steps × \
{processed["latitude_cells"]["value"]} latitudes × \
{processed["longitude_cells"]["value"]} longitudes
- Aggregated population diagnostic: {population:,.0f}
- Maximum one-GJ cell temperature perturbation: {maximum_delta:.8f} K

The derived cube is intentionally not committed because it is reproducibly
generated from the immutable raw snapshots with `make preprocess`. Its
checksum and validation record are tracked.

## Validation status

All {len(processed)} processed-data invariants passed. These cover dimensions,
population conservation, global surface area, humidity bounds, the configured
local perturbation limit, source and sink mask logic, and burden
non-negativity.

All {len(synthetic)} deterministic synthetic-Earth checks passed. The spatial,
temporal, and joint solvers recovered planted source and sink optima, and the
one-GJ transfer conserved energy.

The Stull wet-bulb proxy is missing outside its stated validation domain rather
than extrapolated. Humidex remains the primary burden metric.

## Next phase

Run global one-unit spatial, temporal, and joint analyses; retain negative and
pathological optima; then add transport, storage, capacity, and environmental
constraints progressively.
"""
    temporary = OUTPUT.with_name(f".{OUTPUT.name}.tmp")
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        handle.write(text)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, OUTPUT)
    print(f"Wrote {OUTPUT.relative_to(ROOT)}.")


if __name__ == "__main__":
    main()
