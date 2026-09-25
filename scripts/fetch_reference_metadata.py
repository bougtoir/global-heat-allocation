"""Acquire immutable DOI metadata snapshots or verify published ones."""

from __future__ import annotations

import argparse
import csv
import json
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import requests
import yaml

from global_heat_allocation.provenance import sha256_file

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "references.yml"
RAW_BASE = ROOT / "data" / "raw" / "references"
LEDGER = ROOT / "data" / "metadata" / "reference_snapshots.csv"
VERIFICATION = ROOT / "provenance" / "reference_verification.csv"
USER_AGENT = "global-heat-allocation/0.1 (mailto:bougtoir@gmail.com)"
CROSSREF_ENDPOINT = "https://api.crossref.org/works/"
DATACITE_ENDPOINT = "https://api.datacite.org/dois/"


def _endpoint(registry: str) -> str:
    if registry == "crossref":
        return CROSSREF_ENDPOINT
    if registry == "datacite":
        return DATACITE_ENDPOINT
    raise ValueError(f"Unsupported reference registry: {registry}")


def _record(payload: dict, registry: str) -> dict:
    if registry == "crossref":
        return payload["message"]
    return payload["data"]["attributes"]


def _title(record: dict, registry: str) -> str:
    if registry == "crossref":
        return (record.get("title") or [""])[0]
    titles = record.get("titles") or [{}]
    return titles[0].get("title", "")


def _date_parts(record: dict, registry: str = "crossref") -> str:
    if registry != "crossref":
        return str(record.get("publicationYear", ""))
    date = record.get("published-print") or record.get("published-online") or {}
    parts = date.get("date-parts", [[]])[0]
    return "-".join(str(value) for value in parts)


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_csv_atomic(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise ValueError(f"Cannot write an empty ledger: {path}")
    temporary = path.with_name(f".{path.name}.tmp")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=rows[0].keys(),
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _snapshot_id(retrieved_at: datetime) -> str:
    return f"crossref_{retrieved_at.strftime('%Y%m%dT%H%M%SZ')}"


def acquire() -> None:
    with CONFIG.open(encoding="utf-8") as handle:
        references = yaml.safe_load(handle)["references"]

    retrieved_at = datetime.now(timezone.utc).replace(microsecond=0)
    retrieved = retrieved_at.isoformat()
    snapshot_id = _snapshot_id(retrieved_at)
    staging = RAW_BASE / f".{snapshot_id}.incomplete"
    final = RAW_BASE / snapshot_id
    if staging.exists() or final.exists():
        raise FileExistsError(f"Snapshot already exists: {snapshot_id}")
    staging.mkdir(parents=True)

    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    ledger_rows: list[dict[str, object]] = []
    verification_rows: list[dict[str, object]] = []

    try:
        for reference in references:
            doi = reference["doi"]
            registry = reference.get("registry", "crossref")
            response = session.get(
                f"{_endpoint(registry)}{quote(doi, safe='')}",
                timeout=60,
            )
            response.raise_for_status()
            path = staging / f"{reference['key']}.json"
            path.write_bytes(response.content)
            record = _record(response.json(), registry)
            title = _title(record, registry)
            final_path = final / path.name
            ledger_rows.append(
                {
                    "snapshot_id": snapshot_id,
                    "citation_key": reference["key"],
                    "doi": doi,
                    "retrieved_utc": retrieved,
                    "source_url": response.url,
                    "local_path": str(final_path.relative_to(ROOT)),
                    "file_size_bytes": path.stat().st_size,
                    "sha256": sha256_file(path),
                    "completion": "complete",
                }
            )
            verification_rows.append(
                {
                    "snapshot_id": snapshot_id,
                    "citation_key": reference["key"],
                    "title": title,
                    "doi_or_url": f"https://doi.org/{doi}",
                    "verified_utc": retrieved,
                    "claim_supported": reference["supports"],
                    "verification_notes": (
                        f"{registry.capitalize()} metadata verified; publication date "
                        f"{_date_parts(record, registry)}. "
                        "Claim scope limited to the cited work's documented topic."
                    ),
                }
            )

        manifest = staging / "manifest.json"
        manifest.write_text(
            json.dumps(
                {
                    "snapshot_id": snapshot_id,
                    "retrieved_utc": retrieved,
                    "source": "Crossref REST API and DataCite REST API",
                    "records": len(ledger_rows),
                    "complete": True,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        staging.rename(final)
    except Exception:
        failure_manifest = staging / "manifest.json"
        failure_manifest.write_text(
            json.dumps(
                {
                    "snapshot_id": snapshot_id,
                    "retrieved_utc": retrieved,
                    "source": "Crossref REST API and DataCite REST API",
                    "records_retrieved": len(ledger_rows),
                    "complete": False,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        raise

    existing_ledger = _read_csv(LEDGER)
    existing_verification = _read_csv(VERIFICATION)
    _write_csv_atomic(LEDGER, [*existing_ledger, *ledger_rows])
    _write_csv_atomic(
        VERIFICATION,
        [*existing_verification, *verification_rows],
    )


def verify() -> None:
    rows = _read_csv(LEDGER)
    if not rows:
        raise ValueError(f"No reference snapshot records in {LEDGER}")

    snapshots: Counter[str] = Counter()
    for row in rows:
        if row["completion"] != "complete":
            raise ValueError(f"Incomplete record: {row['citation_key']}")
        path = ROOT / row["local_path"]
        if not path.is_file():
            raise FileNotFoundError(path)
        if path.stat().st_size != int(row["file_size_bytes"]):
            raise ValueError(f"File size mismatch: {path}")
        if sha256_file(path) != row["sha256"]:
            raise ValueError(f"SHA-256 mismatch: {path}")
        snapshots[row["snapshot_id"]] += 1

    for snapshot_id, expected_records in snapshots.items():
        manifest_path = RAW_BASE / snapshot_id / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if not manifest["complete"]:
            raise ValueError(f"Incomplete manifest: {manifest_path}")
        if manifest["records"] != expected_records:
            raise ValueError(f"Record-count mismatch: {manifest_path}")

    print(f"Verified {len(rows)} reference files in {len(snapshots)} snapshot(s).")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify the committed snapshot ledger without network access.",
    )
    args = parser.parse_args()
    if args.verify:
        verify()
    else:
        acquire()


if __name__ == "__main__":
    main()
