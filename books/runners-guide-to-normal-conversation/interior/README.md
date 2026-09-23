# Interior v4 layout proposal

A redesigned interior for *The Runner's Guide to Normal Conversation*, made on
the branch `claude/running-book-interior-review-rp6cu9` at the operator's
request (2026-09-23). **It is a proposal, not an approval.** The KDP upload
file is still `../releases/interior-v3-publication-draft.pdf` until the
operator decides otherwise.

- `interior-v4-proposal.pdf`: the 58-page interior (6 × 9 in, no bleed, black
  and white).
- `previews/before-after.png`: three spreads, v3 next to v4.
- `previews/all-pages-v4.png`: every page, laid out as spreads.

## What changed

**Copy.** None rewritten. A script compared every sentence of v3 with v4; the
only differences are layout (headings, numbering, table labels), plus the
removals listed below.

**Page structure.** In v3 every section started a new page, so most pages were
half empty. In v4, sections flow on from one another and the page count drops
from 80 to 58. Apart from the designed pages (front matter, chapter openers)
and the last page of a chapter, no page ends more than about 1.6 in above the
bottom margin. `build_interior.py` measures this on every build.

**Activities.** Every exercise, test and checklist sits in a numbered panel
(No. 01 to No. 36) with a kind label (Assessment, Checklist, Worksheet, Quiz,
Cut-out card and so on). They have real tick boxes, score boxes, write-in
lines and fill-in tables. Diagrams are typeset, not drawn: the severity gauge,
the five-stage capture cycle, the seven-day tracker and the four-step
disclosure method. The two "keep this available" pages (Emergency stop
phrases, Emergency conversation card) are dashed cut-out cards. The
certificate is a bordered full page with signature lines.

**Illustrations.** The same 24 drawings as v3. Nothing was redrawn or
generated. `build_art.py` takes them from the v3 PDF and converts them to true
greyscale, turns the paper tone pure white, deepens the linework, crops each
one to the drawing and softens its edges. They print larger than in v3 and
never below 300 DPI.

**Paper colour.** v3 filled every page with a cream tint (RGB 251, 250, 245).
On a black-and-white interior that prints as a faint grey wash. v4 is plain
white.

**Type.** Source Serif 4 for reading, Archivo and Archivo Black for headings
and activities, Anton for numbers. Archivo Black and Anton match the text-only
cover. All are SIL Open Font Licence (commercial use and embedding allowed);
licences are in `fonts/`.

## Removed (please confirm)

- v3 page 15, a full-page pull quote repeating a paragraph from page 8, and its
  label "Common referral sources".
- The repeated first sentence on the openers of chapters 2 to 7. Each chapter's
  first section still opens with that sentence.
- The second copy of the Alex-and-Pat kitchen illustration. v3 printed it on
  pages 9 and 41; v4 uses it once, in "The office kitchen". Its page-9
  caption, "Pat only asked about the weekend.", went with it.

## Moved within a chapter, to fill pages (please confirm)

- Ch 1: "Case file: Alex" now follows "Reason for referral". "The
  conversational capture cycle" now comes before the severity assessment.
  "Before proceeding" now comes before "Baseline conversation recording".
- Ch 2: "First intervention" follows "Strava confirmation behaviour". "The
  kudos interval" closes the chapter.
- Ch 3: "A controlled disclosure" follows "The two-sentence limit".
  "Acceptable and not yet acceptable" follows "'Fine, thanks'".
- Ch 5: the shoe-pile illustration moves from "Inventory classification" to
  "Domestic kit and marginal gains".
- Ch 7: the café illustration moves from "Final practical assessment" to
  "Early warning signs".

## Added layout labels (not copy, but new words on the page)

Panel kinds and numbers; "Score", "Ticks", "Yes answers", "Tasks completed"
and "Gels found" beside score boxes; "Meal 1–3"; "Day 1–7"; "Yes/No" column
heads; the write-in labels "Outfit identified", "Duration of conversation",
"Their weekend, in their words", "Your follow-up question", "The decision the
new metric will change", "Person authorised to signal", "Maximum duration
stated" and "Time returned"; the fill-in table heads on "Race fees"; "Case
note" and "Patient file" tags; "Notice to the patient"; the "Normal
Conversation Rehabilitation Service" line on the certificate; and a lined
"Notes" page, which keeps the page count even.

## Before this could replace v3

1. **The cover must be rebuilt.** Spine width depends on page count. The
   current cover was sized for 80 pages (0.180 in spine); 58 white pages give
   about 0.131 in. Nothing may be printed on the spine at that width either way.
2. The operator reviews the removals, moves and labels above.
3. Any further change to the drawings themselves is image-generation work
   (ChatGPT). This proposal only improves how the existing ones print.

## Rebuild

From the repository root:

```bash
python books/runners-guide-to-normal-conversation/interior/build_art.py
python books/runners-guide-to-normal-conversation/interior/build_interior.py
```

Add `--all` to the second command to list how full every page is. Needs
WeasyPrint, PyMuPDF, Pillow and NumPy.
