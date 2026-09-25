# JCP DOCX rendering review

Date: 2026-09-25 UTC

## Method

The generated DOCX files were converted with headless LibreOffice and inspected
as full-document contact sheets plus full-resolution previews of the title page,
cover letter, graphical abstract, and supplementary tables.

## Results

- `manuscript_jcp.docx`: 54 rendered pages; no embedded main figures, clipped
  text, unresolved placeholders, or visibly broken tables.
- `manuscript_jcp_inline.docx`: 55 rendered pages; all six main figures appeared
  in sequence and remained legible.
- `title_page.docx`: 2 rendered pages; author-controlled metadata remains
  visibly marked.
- `cover_letter.docx`: 1 rendered page; no clipping or overflow.
- `supplementary_material.docx`: 5 landscape pages; compact tables are legible
  and no row is expanded across dozens of pages.
- `graphical_abstract.png`: all five stages and the zero-evidence-supported-mode
  endpoint are legible without overlap.

The temporary PDF and contact-sheet renderings are QC artifacts under `build/`
and are not included in the submission ZIP.
