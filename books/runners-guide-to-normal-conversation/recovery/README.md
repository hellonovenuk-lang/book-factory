# Recovery record

The original editable Book Factory project and its approval history were not
present on remote `main` when recovery began on 2026-09-19. This directory
preserves material recovered from the user's attached files. The new
`book.json` is a fresh project skeleton and does **not** represent the lost
project's locks, approvals, QA, or release readiness.

See `ARTIFACTS.md` for the durable download links. GitHub shell push lacked
credentials in the recovery session; until binary files are confirmed on
remote `main`, the Library copy of the interior is the durable source.

## Exact files

- `../releases/interior-v2-refined.pdf` is the attached 80-page, 6 × 9-inch
  interior, copied without alteration. Its SHA-256 is
  `4392b77d7792aee4a7ac03b5e36d507cad9942724eaa7c27201087c1afa7469e`.
  It is the preserved previous canonical interior while a publication-details
  revision is prepared.
- `publication-page-preview.pdf` is the attached one-page preview, copied
  without alteration. Its copyright, publisher, and ISBN lines contain
  placeholders; it is not an approved publication page.

## Extracted material

- `page-text/pdf-001.txt` through `pdf-080.txt` and `interior-layout.txt`
  contain text extracted from the preserved PDF. They can lose semantic
  structure and exact reading order, so compare them to the PDF before use.
- `illustrations/` contains image objects extracted from the PDF, indexed by
  PDF page in `illustrations-index.tsv`. These are the images as embedded in
  the PDF, not proven copies of the original native artwork.

The previous editable page specs, manuscript source, visual bible, intake,
asset registry, approval events, and earlier interior PDF have not been
recovered. Do not infer approval or rerender the interior from the fresh
skeleton. A future reconstruction must keep the preserved PDF available and
identify any changes against it.

The operator supplied the publication details in a later session: author and
copyright holder Kieran Smith, copyright year 2026, KDP free paperback ISBN,
and no separate publishing company or custom imprint. Do not invent an ISBN.
