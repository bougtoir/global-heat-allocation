from pathlib import Path

import pytest

from scripts import download_data


class _Response:
    def __init__(self, payload: bytes) -> None:
        self.payload = payload

    def __enter__(self) -> "_Response":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def raise_for_status(self) -> None:
        return None

    def iter_content(self, chunk_size: int) -> list[bytes]:
        return [self.payload]


class _Session:
    def __init__(self, payload: bytes) -> None:
        self.payload = payload

    def get(self, *args: object, **kwargs: object) -> _Response:
        return _Response(self.payload)


def test_unrecorded_snapshot_is_registered_after_identical_redownload(
    tmp_path: Path,
    monkeypatch,
) -> None:
    payload = b"immutable snapshot"
    raw_base = tmp_path / "data" / "raw"
    path = raw_base / "provider" / "snapshot.bin"
    path.parent.mkdir(parents=True)
    path.write_bytes(payload)
    monkeypatch.setattr(download_data, "ROOT", tmp_path)
    monkeypatch.setattr(download_data, "RAW_BASE", raw_base)
    source = {
        "key": "snapshot",
        "provider": "Provider",
        "product": "Product",
        "version": "Version",
        "role": "input",
        "url": "https://example.test/snapshot.bin",
        "local_filename": "provider/snapshot.bin",
        "license_terms": "Public domain",
    }

    row = download_data._recover_unrecorded(source, _Session(payload))

    assert row["sha256"] == download_data.sha256_file(path)
    assert row["local_path"] == "data/raw/provider/snapshot.bin"
    assert "checksum-identical" in str(row["retrieval_conditions"])
    assert not path.with_name(f".{path.name}.recovery-verification").exists()


def test_unrecorded_snapshot_mismatch_preserves_both_files(
    tmp_path: Path,
    monkeypatch,
) -> None:
    raw_base = tmp_path / "data" / "raw"
    path = raw_base / "provider" / "snapshot.bin"
    path.parent.mkdir(parents=True)
    path.write_bytes(b"existing snapshot")
    monkeypatch.setattr(download_data, "ROOT", tmp_path)
    monkeypatch.setattr(download_data, "RAW_BASE", raw_base)
    source = {
        "key": "snapshot",
        "provider": "Provider",
        "product": "Product",
        "version": "Version",
        "role": "input",
        "url": "https://example.test/snapshot.bin",
        "local_filename": "provider/snapshot.bin",
        "license_terms": "Public domain",
    }

    with pytest.raises(ValueError, match="differs"):
        download_data._recover_unrecorded(source, _Session(b"upstream changed"))

    assert path.read_bytes() == b"existing snapshot"
    assert path.with_name(f".{path.name}.recovery-verification").read_bytes() == (
        b"upstream changed"
    )
