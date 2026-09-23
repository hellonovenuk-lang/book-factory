# KDP upload pack - The Runner's Guide to Normal Conversation

Updated 2026-09-23. This pack is for uploading the redesigned 58-page
interior and its matching cover directly to KDP. It does **not** make the
Book Factory project `release_ready`: that project has no page manifest yet.
Both files were approved by the operator in chat and are recorded in
`audit.jsonl` (`interior_decision` and `cover_decision`, 2026-09-23). The
operator presses Publish.

## 1. Files to upload

| KDP field | File | SHA-256 |
| --- | --- | --- |
| **Manuscript (interior)** | `interior/interior-v4-proposal.pdf` (58 pages) | `195e5e1e9bce3a3218b6484d9f19d3e5bcde8f9f3e33ee90e9d37cb4a65a22a6` |
| **Cover** | `cover/proposals/cover-v3-weekend.pdf` ("How was your weekend?") | `3fc886310ac18b97792fb026bb6b31c6842eeb53e3e3c1babff2248015006fa1` |
| Superseded interior (80 pages) | `releases/interior-v3-publication-draft.pdf` | `675ff470d239e292e0f7f6433f7ae24a9d94cab234bec5399c695e33ca942d63` |
| Superseded covers (sized for 80 pages, do not use) | `cover/proposals/cover-v2-text-only.pdf`, `cover/drafts/cover-v1.pdf` | |

The interior and cover belong together: the cover's spine is sized for exactly
58 pages. If the interior ever changes page count, the cover must be rebuilt
with `python books/runners-guide-to-normal-conversation/cover/build_cover_v3.py`.
The committed PDFs are the approved files; rebuilding produces new checksums.

Choose "Upload a cover you already have (print-ready PDF only)". Do not use
Cover Creator.

## 2. Pre-upload checks already run

Interior (checked 2026-09-23):

- 58 pages, an even count; every page is 6 × 9 in with no bleed, on white.
- All fonts are embedded (Source Serif 4, Archivo, Archivo Black, Anton and
  DejaVu Sans subsets; all free to embed).
- Every image is at least 300 DPI at its printed size.
- Content sits at least 0.875 in from the gutter and 0.625 in from the outside
  edge. KDP needs 0.375 in and 0.25 in.
- The file is 11.9 MB.

Cover (checked 2026-09-23):

- A single full-wrap PDF, 12.381 × 9.250 in (6 × 9 trim, 0.131 in spine for
  58 white pages, 0.125 in bleed).
- Passes Book Factory's own cover check (`bookfactory.core.cover.check_pdf`)
  at those dimensions: title, author and back copy are selectable embedded
  type, nothing under 7 pt, all type clear of the edges and spine folds, and
  the barcode area is empty.
- The spine is blank; KDP allows spine text only from 79 pages.
- No white box is drawn for the barcode: KDP adds its own 2 × 1.2 in barcode
  panel at the bottom right of the back.

## 3. KDP form - Paperback details

| Field | Value |
| --- | --- |
| Language | English |
| Book title | The Runner's Guide to Normal Conversation |
| Subtitle | A Rehabilitation Manual for Runners Who Can No Longer Answer a Simple Question. It must match the subtitle printed on the cover |
| Series | Leave blank for now. Add it once a second title in the series exists |
| Edition number | Leave blank |
| Author | Kieran Smith |
| Contributors | None |
| Publishing rights | I own the copyright and I hold the necessary publishing rights |
| Primary audience | Not sexually explicit. Reading age: leave blank (adult) |
| Primary marketplace | Amazon.co.uk (or Amazon.com if the US is the main target) |

**Description** (paste into the description box):

> They only asked how your weekend was.
>
> You explained the porridge, the weather, the headwind and why the final average was misleading.
>
> The Normal Conversation Rehabilitation Service has prepared this manual for runners whose training now occupies meals, holidays and the first twelve minutes of any conversation. Inside, patients will find:
>
> - a referral and diagnostic test to measure the severity of their condition
> - conversation exercises for anyone who cannot answer "How was your weekend?" in under twenty minutes
> - guidance on equipment, economics, relapse prevention and life outside the training plan
> - a certificate of conditional discharge
>
> An illustrated gift book for the runner who already knows who they are, from the partner, friend or colleague who has heard about the 10k PB more than once.

**Keywords** (seven boxes, one phrase each; no brand names or trademarks):

1. funny gift for runners
2. running humour book
3. gifts for marathon runners
4. running jokes gift for him
5. runner stocking stuffer
6. running club secret santa
7. funny book for runner husband

**Categories** (KDP lets you choose three; search these in the picker):

1. Humor > Sports
2. Sports & Outdoors > Running & Jogging
3. Humor > Parodies

## 4. KDP form - Paperback content

| Field | Value |
| --- | --- |
| ISBN | Get a free KDP ISBN. Do not print or invent an ISBN; KDP adds the barcode to the reserved area on the back |
| Imprint | Leave as "Independently published" (no separate imprint) |
| Publication date | Leave blank |
| Print options | Black & white interior, white paper. Trim 6 × 9 in. Bleed: No bleed. Cover finish: Matte |
| Manuscript | Upload the interior PDF above |
| Cover | Upload `cover/proposals/cover-v3-weekend.pdf` |
| AI-generated content | Answer honestly for how this book was made. If ChatGPT drafted the text, answer **Yes** for text. The illustrations were generated, so answer **Yes** for images. The cover has no generated images (it is typeset and drawn by code), but the interior does. Amazon does not show buyers this answer |

Then open the **Print Previewer** and check every page, the spine and the barcode area.

## 5. Pricing

For 24-108 black-and-white pages on Amazon.com, printing costs a flat $2.30.
The royalty is 60% of list price at $9.99 or more, and 50% below that
(KDP rates checked July 2026). KDP shows the exact cost for each marketplace
on the pricing page.

| List price | Royalty per copy (Amazon.com) |
| --- | --- |
| $9.99 | about $3.69 |
| **$12.99 (suggested)** | about $5.49 |

Suggested prices: **$12.99 in the US and £9.99 in the UK**, with the other
marketplaces left to KDP's automatic conversion. Expanded Distribution: off.
It pays much less per copy and is not needed for Amazon gift sales.

## 6. Order of work (aim: on sale by mid-October)

1. ~~Pick the cover.~~ Done: cover v3, "How was your weekend?" (2026-09-23).
2. Create the paperback in KDP, fill in sections 3-5, and run the Print Previewer.
3. **Order a printed proof** from the Paperback content page before you publish.
   It arrives in about a week. Check the cover colour, the illustration
   reproduction and the gutter.
4. Publish. Review usually takes 3-5 business days and is slower in Q4.
5. After it goes live: claim the book in Author Central and turn on "Look
   Inside". Start a small automatic Amazon Ads campaign (for example £5-10 a
   day) from early November.

## 7. Open decisions for the operator

- ~~**Which cover.**~~ Decided 2026-09-23: cover v3, replacing the text-only choice of 2026-09-22.
- ~~**Interior layout and illustrations.**~~ Decided 2026-09-23: interior v4, with the existing drawings cleaned up for print.
- **AI disclosure answers** for text and images (section 4).
