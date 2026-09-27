# KDP - files to upload to Amazon

One folder per book. Each holds exactly what KDP asks for:

- `cover.pdf` - the full-wrap cover (back, spine and front in one file)
- `interior.pdf` - the inside pages
- `UPLOAD.md` - what to type into each box of KDP's form

| Book | Folder | Status |
| --- | --- | --- |
| The Golf Addict's Guide to Family Reintegration | [`golf-addicts-guide/`](golf-addicts-guide/UPLOAD.md) | Ready to upload (cover v4, 71 pages) |
| The Padel Addict's Guide to Talking About Anything Else | [`padel-addicts-guide/`](padel-addicts-guide/UPLOAD.md) | Ready to upload (cover v2, 80 pages) |
| The Runner's Guide to Normal Conversation | [`runners-guide/`](runners-guide/UPLOAD.md) | Ready to upload (cover v3, 58 pages; made outside Book Factory's pipeline) |

The PDFs here are copies of each book's approved files, checked by SHA-256
(a fingerprint of the file) in its `UPLOAD.md`. The originals stay in
`books/<book>/`. If a book's cover or pages change, refresh its folder here.
