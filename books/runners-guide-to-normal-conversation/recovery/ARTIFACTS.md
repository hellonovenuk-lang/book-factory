# Preserved binary artifacts

The full interior and publication preview were attached by the operator and
retained in their ChatGPT Library. These links require the operator's access:

- [80-page interior v2](https://chatgpt.com/api/library/files/libfile_2889efc353d48191a893e3dd0bca2d25/download)
- [Publication-page preview](https://chatgpt.com/api/library/files/libfile_a25f6826e97c81918a19989f8f1948cc/download)

The local recovery commit includes copies at `../releases/` and
`publication-page-preview.pdf`, with 26 image objects extracted from the
interior. If these binary files are absent in a fresh clone, retrieve the
interior from the preserved link and rerun `pdftotext -layout` and
`pdfimages -all` to regenerate the text and embedded image recovery material.

This pointer does not make the project release ready or establish Book Factory
approval history. See `README.md` for the recovery status.
