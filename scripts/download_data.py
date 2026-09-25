"""Download immutable public-data inputs and record their provenance."""

from __future__ import annotations

import argparse
import csv
import os
from datetime import datetime, timezone
from pathlib import Path

import requests
import yaml

from global_heat_allocation.provenance import sha256_file

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "data_sources.yml"
RAW_BASE = ROOT / "data" / "raw"
LEDGER = ROOT / "data" / "metadata" / "data_snapshots.csv"
USER_AGENT = "global-heat-allocation/0.1 (mailto:bougtoir@gmail.com)"
FIELDNAMES = [
    "source_key",
    "provider",
    "product",
    "version",
    "role",
    "source_url",
    "retrieved_utc",
    "retrieval_conditions",
    "local_path",
    "file_size_bytes",
    "sha256",
    "license_terms",
    "completion",
]


def _request_headers(source: dict[str, object]) -> dict[str, str] | None:
    referer = source.get("referer")
    if referer is None:
        return None
    return {"Referer": str(referer)}


def _retrieval_conditions(source: dict[str, object], default: str) -> str:
    return str(source.get("retrieval_conditions", default))


def _read_sources() -> list[dict[str, object]]:
    with CONFIG.open(encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    return [source for source in config["sources"] if source["acquire"]]


def _read_ledger() -> list[dict[str, str]]:
    if not LEDGER.exists():
        return []
    with LEDGER.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_ledger(rows: list[dict[str, object]]) -> None:
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    temporary = LEDGER.with_name(f".{LEDGER.name}.tmp")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, LEDGER)


def _verify_row(row: dict[str, str]) -> None:
    path = ROOT / row["local_path"]
    if row["completion"] != "complete":
        raise ValueError(f"Incomplete acquisition record: {row['source_key']}")
    if not path.is_file():
        raise FileNotFoundError(path)
    if path.stat().st_size != int(row["file_size_bytes"]):
        raise ValueError(f"File size mismatch: {path}")
    if sha256_file(path) != row["sha256"]:
        raise ValueError(f"SHA-256 mismatch: {path}")


def verify() -> None:
    rows = _read_ledger()
    if not rows:
        raise ValueError(f"No data snapshot records in {LEDGER}")
    required_keys = {str(source["key"]) for source in _read_sources()}
    present_keys = {row["source_key"] for row in rows}
    missing = required_keys - present_keys
    if missing:
        raise ValueError(f"Missing required acquisition records: {sorted(missing)}")
    incomplete_optional: list[str] = []
    for row in rows:
        if row["source_key"] in required_keys or row["completion"] == "complete":
            _verify_row(row)
        else:
            incomplete_optional.append(row["source_key"])
    print(f"Verified {len(rows) - len(incomplete_optional)} public-data files.")
    if incomplete_optional:
        print(
            "Retained explicitly incomplete optional records: "
            + ", ".join(sorted(incomplete_optional))
            + "."
        )


def _download(
    source: dict[str, object],
    session: requests.Session,
) -> dict[str, object]:
    path = RAW_BASE / str(source["local_filename"])
    if path.exists():
        raise FileExistsError(f"Refusing to overwrite raw snapshot: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_name(f".{path.name}.part")
    if partial.exists():
        raise FileExistsError(f"Incomplete download already exists: {partial}")

    try:
        with session.get(
            str(source["url"]),
            headers=_request_headers(source),
            stream=True,
            timeout=(30, 300),
        ) as response:
            response.raise_for_status()
            with partial.open("xb") as handle:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        handle.write(chunk)
                handle.flush()
                os.fsync(handle.fileno())
        os.replace(partial, path)
    except Exception:
        partial.unlink(missing_ok=True)
        raise

    retrieved = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    return {
        "source_key": source["key"],
        "provider": source["provider"],
        "product": source["product"],
        "version": source["version"],
        "role": source["role"],
        "source_url": source["url"],
        "retrieved_utc": retrieved,
        "retrieval_conditions": _retrieval_conditions(
            source,
            "Anonymous HTTPS full-file streaming download; no subsetting",
        ),
        "local_path": str(path.relative_to(ROOT)),
        "file_size_bytes": path.stat().st_size,
        "sha256": sha256_file(path),
        "license_terms": source["license_terms"],
        "completion": "complete",
    }


def _recover_unrecorded(
    source: dict[str, object],
    session: requests.Session,
) -> dict[str, object]:
    path = RAW_BASE / str(source["local_filename"])
    verification = path.with_name(f".{path.name}.recovery-verification")
    if verification.exists():
        raise FileExistsError(
            f"Recovery verification file already exists: {verification}"
        )
    with session.get(
        str(source["url"]),
        headers=_request_headers(source),
        stream=True,
        timeout=(30, 300),
    ) as response:
        response.raise_for_status()
        with verification.open("xb") as handle:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    handle.write(chunk)
            handle.flush()
            os.fsync(handle.fileno())
    if path.stat().st_size != verification.stat().st_size:
        raise ValueError(f"Unrecorded snapshot differs in size from source: {path}")
    local_hash = sha256_file(path)
    if local_hash != sha256_file(verification):
        raise ValueError(f"Unrecorded snapshot differs in SHA-256 from source: {path}")
    verification.unlink()

    retrieved = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)
    return {
        "source_key": source["key"],
        "provider": source["provider"],
        "product": source["product"],
        "version": source["version"],
        "role": source["role"],
        "source_url": source["url"],
        "retrieved_utc": retrieved.replace(microsecond=0).isoformat(),
        "retrieval_conditions": _retrieval_conditions(
            source,
            "Recovered after interrupted ledger update; existing snapshot "
            "verified by checksum-identical full redownload",
        ),
        "local_path": str(path.relative_to(ROOT)),
        "file_size_bytes": path.stat().st_size,
        "sha256": local_hash,
        "license_terms": source["license_terms"],
        "completion": "complete",
    }


def _restore(
    source: dict[str, object],
    expected: dict[str, str],
    session: requests.Session,
) -> None:
    path = RAW_BASE / str(source["local_filename"])
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_name(f".{path.name}.part")
    if partial.exists():
        raise FileExistsError(f"Incomplete download already exists: {partial}")
    try:
        with session.get(
            str(source["url"]),
            headers=_request_headers(source),
            stream=True,
            timeout=(30, 300),
        ) as response:
            response.raise_for_status()
            with partial.open("xb") as handle:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        handle.write(chunk)
                handle.flush()
                os.fsync(handle.fileno())
        expected_size = int(expected["file_size_bytes"])
        if partial.stat().st_size != expected_size:
            raise ValueError(f"Restored file size mismatch: {partial}")
        if sha256_file(partial) != expected["sha256"]:
            raise ValueError(f"Restored SHA-256 mismatch: {partial}")
        os.replace(partial, path)
    except Exception:
        raise


def acquire() -> None:
    sources = _read_sources()
    existing_rows = _read_ledger()
    existing_by_key = {row["source_key"]: row for row in existing_rows}
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    rows: list[dict[str, object]] = list(existing_rows)
    for source in sources:
        key = str(source["key"])
        if key in existing_by_key:
            expected = existing_by_key[key]
            path = ROOT / expected["local_path"]
            if path.exists():
                _verify_row(expected)
                print(f"Verified existing {key}.")
            else:
                _restore(source, expected, session)
                _verify_row(expected)
                print(f"Restored checksum-identical {key}.")
            continue
        path = RAW_BASE / str(source["local_filename"])
        if path.exists():
            row = _recover_unrecorded(source, session)
            action = "Recovered ledger entry"
        else:
            row = _download(source, session)
            action = "Acquired"
        rows.append(row)
        _write_ledger(rows)
        print(f"{action} {key}: {row['file_size_bytes']} bytes.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify all acquired files against the provenance ledger.",
    )
    args = parser.parse_args()
    if args.verify:
        verify()
    else:
        acquire()


if __name__ == "__main__":
    main()
