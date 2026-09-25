from __future__ import annotations

from scripts import validate_jcp_submission


def test_validate_jcp_submission(tmp_path, monkeypatch) -> None:
    report = tmp_path / "JCP_FINAL_QC.md"
    monkeypatch.setattr(validate_jcp_submission, "REPORT", report)

    validate_jcp_submission.main()

    text = report.read_text(encoding="utf-8")
    assert "WEAK GO" in text
    assert "ZIP integrity and exact-membership check: passed." in text
