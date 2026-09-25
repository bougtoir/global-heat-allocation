# JCP final clean-build and reproducibility report

## Verdict

**Passed for the frozen JCP submission pipeline.**

The analytical baseline had already been reproduced from an independent clean
checkout before the final-finishing freeze. In accordance with the freeze, this
pass did not rerun the 2.5 GB primary-data analysis merely to obtain new
narrative results. It reverified the retained raw snapshots and frozen
source-artifact checksums, then rebuilt the complete JCP package twice.

## Environment and commands

The final-finishing verification used the repository virtual environment and
the published Make targets:

```bash
make lint
make test
make verify-references
make jcp-qc
make jcp-qc
unzip -t submission/jcp/jcp_submission_package.zip
```

## Results

- Ruff check: passed.
- Ruff format check: 78 files passed.
- Pytest: 86 passed.
- Reference verification: 109 files in 4 snapshots verified.
- JCP build and validation: passed twice.
- Main-text word count: 6,005.
- Main references: 48.
- ZIP integrity: passed.
- ZIP exact membership: passed with 33 members.
- Figure/table numbering and PNG/SVG pair audit: passed.
- Accidental Japanese/full-width-character audit: zero findings.
- Raw snapshot ledger integrity: 78 of 78 paths, sizes, and checksums verified.
- Manuscript value integrity: 76 of 76 source-artifact checksums verified.

## Deterministic rebuild

The following files were hashed after one successful `make jcp-qc`, rebuilt
again, and hashed again. The before/after checksums were identical:

| Artifact | SHA-256 |
|---|---|
| JCP submission ZIP | `4a5e4711d068adf3a47796ec4fadbc6bca0ed6fee6af9cb02acfc44d80507cb1` |
| Clean manuscript DOCX | `d78a63f9877272d9704ba6203aca46a332c201d566dae5ae6460fceb896c1d1e` |
| Inline manuscript DOCX | `fb6c335b3d131268eae3787d28216b0a3b0df2b058eebc9d190b37a68a4dada9` |
| Supplementary material DOCX | `a67af310932f2fe04d039d152b8066c086ec3fbf699460a4f6f6f226a4c68e8e` |

## Render inspection

LibreOffice rendered the final deliverables successfully. The Java launcher
warning did not prevent conversion.

- Clean manuscript: 40 pages.
- Inline manuscript: 26 pages.
- Supplement: 7 pages.
- Title page: 2 pages.
- Cover letter: 1 page.

The inline manuscript remains within the requested approximate 25-35-page
target. Final inspection found no clipping or overlap in the reviewed main-text,
figure, and table pages. Table 5 displays the corrected non-recommendation
wording and continues legibly onto the following page.

## Scope of reproducibility

The deterministic comparison covers the JCP package and key DOCX outputs from
the frozen analysis artifacts. It does not claim that unresolved practical
inputs exist or that a project-level thermal pathway has been validated.
