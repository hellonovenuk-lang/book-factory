# Preserved binary artifacts

The full interior and publication preview were attached by the operator and
retained in their ChatGPT Library. These links require the operator's access:

- [80-page interior v2](https://chatgpt.com/api/library/files/libfile_2889efc353d48191a893e3dd0bca2d25/download)
- [Publication-page preview](https://chatgpt.com/api/library/files/libfile_a25f6826e97c81918a19989f8f1948cc/download)
- [Publication-details draft, 80 pages](https://chatgpt.com/api/library/files/libfile_c80dd91cca688191bc23043465efdfa4/download)
- [Updated one-page publication proof](https://chatgpt.com/api/library/files/libfile_9d19268ac06881918360f5e41984b39d/download)

The publication-details draft was built from the unchanged v2 interior:
PDF page 2 adds the author, and PDF page 4 replaces the treatment-conditions
page with the supplied preview after removing its bracketed placeholders.
No free ISBN number is printed before KDP assigns one. Raster comparison at
90 dpi found that pages 1, 3, and 5–80 are visually identical to v2.
`build_publication_revision.py` reproduces this PDF-level draft from the two
preserved inputs. It is **not** an approved Book Factory release.

The local recovery commit includes copies at `../releases/` and
`publication-page-preview.pdf`, with 26 image objects extracted from the
interior. If these binary files are absent in a fresh clone, retrieve the
interior from the preserved link and rerun `pdftotext -layout` and
`pdfimages -all` to regenerate the text and embedded image recovery material.

This pointer does not make the project release ready or establish Book Factory
approval history. See `README.md` for the recovery status.
