# KDP upload pack - The Runner's Guide to Normal Conversation

Prepared 2026-09-22. This pack is for uploading the existing 80-page interior
directly to KDP. It does **not** make the Book Factory project
`release_ready`: that project has no page manifest yet, and nothing here is an
approval. The operator chooses the cover and presses Publish.

## 1. Files to upload

| KDP field | File | SHA-256 |
| --- | --- | --- |
| Manuscript (interior) | `releases/interior-v3-publication-draft.pdf` | `675ff470d239e292e0f7f6433f7ae24a9d94cab234bec5399c695e33ca942d63` |
| Cover, option A: illustrated (operator review-approved 2026-09-20) | `cover/drafts/cover-v1.pdf` | `93b1415a5720517fb0ca1f5b9c70247552b29759adc720ce26f102758e6b86fd` |
| Cover, option B: text only (proposal, not approved) | `cover/proposals/cover-v2-text-only.pdf` | `87a43c4a5413f61a17df2b847ec7dc8c7084f88cb26ec57254d3251a0b1a1f80` |

Upload **one** cover. Choose "Upload a cover you already have (print-ready
PDF only)". Do not use Cover Creator.

Option B is rebuilt with `python books/runners-guide-to-normal-conversation/cover/build_cover_text_v2.py`
from the repository root. Its fonts (Anton and Archivo Black, SIL Open Font
Licence, so commercial use and embedding are allowed) are in `cover/fonts/`.

## 2. Pre-upload checks already run

Interior (checked 2026-09-22 against `bookfactory/kdp/profiles/kdp-default.json`):

- 80 pages, an even count; every page is 6 × 9 in with no bleed.
- All fonts are embedded (DejaVu Serif and DejaVu Sans subsets).
- The lowest image resolution is 341 DPI at its printed size (page 9). KDP's minimum is 300.
- Content sits at least 0.875 in from the gutter and 0.625 in from the outside
  edge. KDP needs 0.375 in and 0.25 in at 80 pages.
- The file is 4.9 MB.

Covers: both are single full-wrap PDFs, 12.430 × 9.250 in (6 × 9 trim,
0.180 in spine for 80 white pages, 0.125 in bleed). They have selectable
embedded type, nothing on the spine, and a clear barcode area on the back.
Option B passes Book Factory's cover check except for "contains no artwork
image". That failure is expected, because it is text only by design.

## 3. KDP form - Paperback details

| Field | Value |
| --- | --- |
| Language | English |
| Book title | The Runner's Guide to Normal Conversation |
| Subtitle | **Option B:** A Rehabilitation Manual for Runners Who Can No Longer Answer a Simple Question. **Option A:** leave blank (KDP wants any subtitle printed on the cover to match this field) |
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
| Cover | Upload the chosen cover PDF above |
| AI-generated content | Answer honestly for how this book was made. If ChatGPT drafted the text, answer **Yes** for text. The illustrations were generated, so answer **Yes** for images. For option B the cover has no generated images, but the interior still does. Amazon does not show buyers this answer |

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

1. Pick the cover, A or B.
2. Create the paperback in KDP, fill in sections 3-5, and run the Print Previewer.
3. **Order a printed proof** from the Paperback content page before you publish.
   It arrives in about a week. Check the cover colour, the illustration
   reproduction and the gutter.
4. Publish. Review usually takes 3-5 business days and is slower in Q4.
5. After it goes live: claim the book in Author Central and turn on "Look
   Inside". Start a small automatic Amazon Ads campaign (for example £5-10 a
   day) from early November.

## 7. Open decisions for the operator

- **Which cover.** Option A was review-approved on 2026-09-20. Option B is a proposal.
- **Interior illustrations.** The 25 interior images use the same illustration
  style as cover option A. If you dislike that style, decide whether that
  matters inside the book, where the jokes carry it, before you publish.
  Replacing them is a larger job.
- **AI disclosure answers** for text and images (section 4).
