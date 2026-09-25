import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "docs" / "APPLIED_ENERGY_FIT_NOVELTY_AUDIT.md"


def test_applied_energy_audit_rebuilds_deterministically() -> None:
    subprocess.run(
        [sys.executable, "scripts/write_applied_energy_audit.py"],
        cwd=ROOT,
        check=True,
    )
    before = AUDIT.read_bytes()
    subprocess.run(
        [sys.executable, "scripts/write_applied_energy_audit.py"],
        cwd=ROOT,
        check=True,
    )
    assert AUDIT.read_bytes() == before


def test_applied_energy_audit_preserves_claim_boundaries() -> None:
    text = AUDIT.read_text(encoding="utf-8")

    assert "**NO-GO for submission to Applied Energy" in text
    assert "two-scale constraint-attrition" in text
    assert "0 practical mode is supported" in text
    assert "must not be collapsed into a single" in text
    assert "first global heat-redistribution model" in text
    assert "Cloudflare challenge" in text
