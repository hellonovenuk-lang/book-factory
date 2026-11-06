# Proposal: a book of hobby-household limericks (angle 2, new format)

Nightly research run, 6 November 2026. Angle 2 of the rotation (the last run was angle 1, the Grand Prix guide).

## 1. Decision needed

**Book: *The Hobby Addict's Book of Limericks*, 100 five-line verses about living with a man and his hobby. Reply `go` or `no` (and why).**

## 2. The pitch

- **Title (working):** *The Hobby Addict's Book of Limericks: 100 Verses About a Man Who Said He'd Be Back by Four*
- **Who buys it:** the same households as Golf and Padel: a wife, daughter or friend buying a stocking filler or birthday gift for a man with a hobby, or the man himself. A limerick (a five-line rhyming joke verse) is quick to read aloud, so it works as a bathroom-shelf or Christmas-table book.
- **When:** Father's Day, Sunday 20 June 2027 (live by about mid-May), with Valentine's and Mother's Day as bonus dates. Too late for this Christmas (a book needs about 5-6 weeks).
- **Why now:** it is a new shape for the Dave world (verse, not a manual), costs no pictures inside, and a limerick page is short enough to read in a shop or in a "look inside" preview.
- **Different from Amazon:** limerick gift books I found are general (Michael Palin's *A Sackful of Limericks*), dad-joke or nonsense collections, or sweary. I found none that is about the household of one hobby, so none carries the Dave voice.

## 3. Evidence

How sure am I: **very low.** The Amazon refresh timed out again from this machine, so there are no ranks. Higgsfield was not available in this run (last known credit balance: 6). Web search gave listings only, no sales figures.

| Fact | Source | Meaning |
|---|---|---|
| Limerick and dad-joke gift books are on sale in UK and US shops, including a Hachette dad-joke title (*Dad Joke Loading*, Oct 2025) and small-press limerick books (*The Little Book of Teenage Dad Jokes: 101 Nonsense Limericks*) | publisher and retailer pages | The format exists at gift-shop level, and small publishers are in it |
| Palin's *A Sackful of Limericks* (2016) | Winstone's Books | A known name proved the format; no newer big title found |
| KDP asks for AI disclosure and may flag undifferentiated public-domain text | KDP content guidelines (via third-party summary; check the official page) | We write original verse, so no public-domain problem. Disclose AI use as for the other books |

No ranks, review counts or page counts for any competitor. **Verdict: weak evidence, worth a cheap test only.** I would not pick it over the Golf and Padel sales data once it exists. The first research run (`docs/research/2026-09-30-new-book-types.md`) rated journals and planners as saturated; verse is not low-content, but the same caution about unproven demand applies.

## 4. The book plan

- **Format:** 5.5 x 8.5 in, black and white, about 72 pages (one or two limericks per page with space round them). £8.99 UK / $9.99 US, so about £3.2 a copy at 60% (printing about £1.93 at this length; check KDP's calculator at upload).
- **Pen name:** the Dave brand (Kieran Smith).
- **Contents:**
  1. A short foreword from Dave, who has "never been late, only early for a different event"
  2. 10 limericks on **Leaving** (kit by the door, the "quick one")
  3. 10 on **The Return** (muddy floors, the sheepish hello)
  4. 10 on **Money** (the new equipment, the receipt hidden in the recycling)
  5. 10 on **The Fixture List** (weddings, christenings, the clash)
  6. 10 on **Other People's Opinions** (the club bore, the group chat)
  7. 10 on **The Family** (the kids' view, the dog's view)
  8. 10 on **Holidays**, 10 on **Christmas**, 10 on **Retirement**
  9. 10 on **Reconciliation** (flowers, the promised voucher)
  10. "Write your own": two blank lined pages for the reader
- **Pictures:** none inside. Optional: 10 small spot drawings, about 20 credits, not recommended. One cover picture, about 2 credits.
- **Hobby-neutral:** verses say "the club", "the kit", "the fixture list", so one book fits golf, padel, running, fishing and more, unlike the single-sport books.
- **Cover direction:** big title; Dave at a lectern or on a chair, reading a verse aloud to a patient family at the table; plain band across the top. Same style as the live covers.

## 5. Samples (original)

**Back cover:** "Dave said he'd be back by four. This is a book of what happened next. A hundred limericks about the man, the kit, the clubhouse and the people waiting at home. Read one aloud at dinner. Watch who laughs first."

**Five sample limericks:**

1. There once was a man, name of Dave,
   Whose kit bag was all that he'd save.
   "Back by four," he said, bright.
   It was gone before light,
   And returned with a tan and a wave.

2. He bought a new thing for his hobby.
   The price was, he said, "not a lobby
   Of cash, just a few quid."
   The receipt, though, was hid
   In the recycling. Somebody's snobby.

3. The wedding was set for the Saturday.
   "Will there be a game?" Dave said, "May I?"
   The bride, with a stare,
   Said, "There's no game there."
   He wore the same face as the day he'd sell his own ma-ma.

4. His wife keeps a list on the fridge:
   "Dave, remember: home. Not the ridge."
   He reads it with care,
   Then he's gone, and she's there
   With the dog, and a cup, and a smidge.

5. At Christmas he sat at the table
   And carved with the grace he was able.
   The talk turned to sport.
   Mum said, "Cut it short."
   He did. Then went off to the stable.

(These are first drafts to show voice and idea. Rhymes and metre in 3-5 are loose, and the final book must fix them: the manuscript pass would check every verse for scansion, sense and the voice bible's banned phrases. A hundred good limericks is hard; expect to cut a third.)

## 6. What Book Factory needs

- **Today:** a plain text page type already exists, and a poem or verse is just short text. One or two limericks per page is plausible with the existing text page; spacing and a centred, indented layout may need a small style tweak (a verse page type, one short build phase) if the default looks cramped. A fit check in `/write-book` will say.
- **Risk in the process, not the code:** writing 100 verses that scan is the real work. It goes through `/write-book`'s manuscript step and the content QA (banned phrases, "it's not X, it's Y" shapes).

## 7. Timeline

1. Kieran says `go` (any day).
2. Optional: one build phase for a verse page, if the look-check shows text pages are not good enough.
3. `/write-book`: about 3-4 sittings (the manuscript will take the longest).
4. Kieran approves the cover and uploads to KDP; ~72 hours for review.
5. Live by about mid-May 2027 for Father's Day (20 June); live by about 5 January for Valentine's if he wants it sooner.

## 8. Risks and runners-up

- **Risks:** very thin evidence; verse quality is hard and a weak limerick shows; humour poetry may be a small shelf; overlap with the vouchers, quiz and widow proposals (all awaiting) for the same Valentine's/Christmas buyers.
- **Runner-up 1:** *The Hobby Addict's Excuse Book*, a fill-in log of excuses, every one used before; low-content risk.
- **Runner-up 2:** a Dave "spot the difference" book; needs many matched pictures, so expensive in credits.

## 9. Sources

- [Winstone's Books: A Sackful of Limericks](https://winstonebooks.co.uk/collections/gifts/products/9781847947994)
- [Hachette UK: Dad Joke Loading](https://www.hachette.co.uk/titles/harry-hilton/dad-joke-loading/9781837996988/)
- [The Little Book of Teenage Dad Jokes: 101 Nonsense Limericks](https://pastforward.org/products/the-little-book-of-teenage-dad-jokes-101-nonsense-limericks-poetry-verse-9781739536701)
- [KDP content guidelines](https://kdp.amazon.com/en_US/help/topic/G200672390)
- [Vappingo: KDP content guidelines summary](https://www.vappingo.com/word-blog/kdp-content-guidelines/)
- `docs/research/2026-09-30-new-book-types.md` (royalties, journals judged saturated)
