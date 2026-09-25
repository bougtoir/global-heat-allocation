from __future__ import annotations

import re
import zipfile

from scripts import build_jcp_submission as jcp


def test_jcp_source_resolves_values_citations_and_markers() -> None:
    blocks, references, word_count = jcp._resolve_source()
    resolved = "\n".join(text for _, text in blocks)

    assert 6000 <= word_count <= 8000
    assert len(references) == 48
    assert "{{" not in resolved
    assert "[[" not in resolved
    assert "AUTHOR ACTION" in resolved
    assert "zero practical endpoints are supported" in resolved


def test_jcp_source_has_complete_main_figure_and_table_markers() -> None:
    source = jcp.MANUSCRIPT_SOURCE.read_text(encoding="utf-8")

    assert sorted(map(int, re.findall(r"\[\[FIGURE:(\d+)\]\]", source))) == list(
        range(1, 7)
    )
    assert sorted(map(int, re.findall(r"\[\[TABLE:(\d+)\]\]", source))) == list(
        range(1, 6)
    )


def test_jcp_reference_registry_respects_limit_and_first_appearance() -> None:
    keys = jcp._reference_keys()
    blocks, _, _ = jcp._resolve_source()
    resolved = "\n".join(text for _, text in blocks)

    assert len(keys) <= 50
    assert keys[0] == "glavic2007sustainability"
    assert keys[-1] == "ornl2024wasteheatreport"
    assert "Oak Ridge National Laboratory" in resolved


def test_jcp_archive_contains_required_assets() -> None:
    archive_path = jcp.SUBMISSION / "jcp_submission_package.zip"
    with zipfile.ZipFile(archive_path) as archive:
        names = set(archive.namelist())
        assert archive.testzip() is None

    assert {
        "manuscript_jcp.docx",
        "manuscript_jcp_inline.docx",
        "title_page.docx",
        "highlights.txt",
        "cover_letter.docx",
        "graphical_abstract.png",
        "graphical_abstract_editable.pptx",
        "supplementary_material.docx",
        "submission_checklist.md",
    }.issubset(names)
