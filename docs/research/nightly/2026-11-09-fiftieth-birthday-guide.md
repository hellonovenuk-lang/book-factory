# Proposal: a 50th-birthday guide (angle 3, a new line)

Nightly research run, 9 November 2026. Angle 3 of the rotation (the last run, the limericks, was angle 2).

## 1. Decision needed

**Book: *The Newly Fifty Man's Guide to Being Told He Is Fine*, a deadpan official handbook for the man turning 50 and the people who have to buy him a present. Reply `go` or `no` (and why).**

## 2. The pitch

- **Title (working):** *The Newly Fifty Man's Guide to Being Told He Is Fine: An Official Handbook for Him, and for the Person Who Booked the Table*
- **Who buys it:** wife, partner, grown-up kids, friends and colleagues, for a man turning 50 (or 40, 55, 60 with a cover tweak later). A milestone birthday is a *must-buy-something* moment, which a hobby is not.
- **When:** all year, because birthdays are spread across the calendar. No single deadline, so no rush to beat Christmas. Christmas and Father's Day are bonus dates.
- **Why now:** it gives the Dave world a gift for an occasion, not a hobby. It reaches men whose hobby is "none" (the "my knee", "my back", "new reading glasses", "a sudden interest in the garden" man), a group bigger than any single sport.
- **Different from Amazon:** the 50th-birthday books I found are memoir-style essays (Marcus Berkmann), quotes and lists, trivia, or personalised "what happened in your birth year" books. None is a straight-faced manual in which the family is the audience.

## 3. Evidence

How sure am I: **low.** The Amazon refresh found no usable lists again (it returned 0 titles for the one list tried), and Higgsfield was not available, so there are no ranks, prices or credit balance from this run (last known balance: 6). The facts below come from a web search that returned retailer and publisher pages only.

| Fact | Source | Meaning |
|---|---|---|
| Humour books for men turning 50 are a real, repeating shelf: Marcus Berkmann's *A Shed of One's Own* (the author marked turning 50 by "hiding under the duvet for six weeks"), its sequel for 60, *The Dangerous Book for Middle-Aged Men*, *How to Grow Old* (Ebury, Sunday Times bestseller label) | publisher and retailer pages | The buyer and the occasion are proven, and big publishers lead |
| Personalised "Book of Everyone 50th Birthday" (44 pages, changes with name and date) | Wonderbly | People pay for a milestone-specific gift |
| About 570,000-585,000 babies were born in England and Wales in each of 1976 and 1977, so about that many people turn 50 each year (my figure from ONS birth counts; please check before quoting) | ONS | A group of over half a million a year, with a buyer for each |

### Competitors (found by search, ranks not available)

| Title | Publisher | Type |
|---|---|---|
| A Shed of One's Own (Berkmann) | Little, Brown (big) | memoir, essays |
| Still a Bit of Snap in the Celery (Berkmann), £10.99 | Little, Brown (big) | memoir, aimed at 60 |
| The Dangerous Book for Middle-Aged Men | independent (agendabookshop listing) | spoof manual, wide |
| How to Grow Old | Ebury (big) | essays |
| 50 - Older Possibly Wiser, 96 pp | gift imprint | short quotes, either sex |
| The Book for Men Who Have Everything, £6.42 | gift imprint | trivia |
| Things to Do Now That You're 50 | Hamlyn (big) | list book |

No review counts or ranks. **Verdict: weak evidence, worth a cheap test.** Big publishers hold the shelf, so our room is the angle: a straight-faced manual that is also read aloud by the family, same as the live books.

## 4. The book plan

- **Format:** 5.5 x 8.5 in, black and white, about 72-80 pages, same look as Golf and Padel. £9.99 UK / $11.99 US; about £3.50 a copy at 60% after printing (check KDP's calculator at upload).
- **Pen name:** the Dave brand (Kieran Smith). Dave turns 50 in this one.
- **Contents (sections of an official handbook):**
  1. Foreword: "Congratulations. You have been issued a body."
  2. **Part 1 The Birthday itself**: the party he did not want, the card with a tractor on it, the speech he is "not going to do"
  3. **Part 2 The Body**: new noises, the knee, a sudden need to explain his back to strangers, reading glasses held at arm's length
  4. **Part 3 The Spend**: the midlife-crisis purchase, ranked by cost (bike, guitar, a van, a "project")
  5. **Part 4 The Music**: the playlist argument, "they don't make them like that", the gig where he sat down
  6. **Part 5 The Health Check**: a deadpan self-assessment, ticks and score boxes (the activity page)
  7. **Part 6 The Family's Guide to Him**: how to talk to a man who has just discovered his own mortality and the garden
  8. **Appendix**: a certificate, a cut-out "Excuse Card" for leaving early, and a "Things I Am Now Allowed To Say" list
- **Pictures:** 2-3 at most, about 6 credits (balance unknown tonight, last known 6): the Part 1 opener and the cover. The rest typeset (checklists, score boxes, certificate), which cost nothing.
- **Cover direction:** big "50" and title; Dave at the head of a table holding a cake with too many candles, family sitting politely; plain band across the top. Same style as the live covers.

## 5. Samples (original, first drafts)

**Back cover:** "He is fifty. He is fine. He has said so four times, and twice more with a hand on the knee. This is the official handbook for the man, and for the person who booked the table. Read the sections aloud. He will say he is not listening."

**Three sample pages**

*Section 2.1: The Noise.* Between the ages of 49 and 50 the body begins to make a sound when its owner stands up. The sound is not a complaint. It is a notification. The man will respond to it with a short comment ("Right.") and a hand placed on the nearest surface. Family members should not remark on the noise. They should look at the ceiling, as at a plane going over.

*Section 3.4: The Purchase.* Every man turning fifty buys one thing he describes as "an investment". Tick the box that applies: [ ] A bike that costs more than the car [ ] A guitar he last played in 1994 [ ] A shed with a heater [ ] A van. Score one point per box. Two or more points means a conversation. Four means he has already told the neighbours.

*Section 5.2: The Health Check.* Stand up. Count the seconds before you can say nothing about it. Under three: normal. Three to eight: normal for fifty. Over eight: do not mention it, and book a table nearer the door.

(These show the voice only; the manuscript pass checks them against `style/voice-bible.md`, the banned phrases and content QA.)

## 6. What Book Factory needs

- **Today:** everything. Text pages, checklist, score box, certificate and cut-out card are all existing activity blocks (`docs/RENDERING.md`); chapter openers use the picture budget (chapter openers only is the default).
- No build work expected. `/write-book "The Newly Fifty Man's Guide to Being Told He Is Fine"` would start it, with the intake asking the big decisions (exact title, Dave's fixed details, black and white, cover style).

## 7. Timeline

1. Kieran says `go`.
2. `/write-book`: about 3-4 sittings (brief, voice, manuscript, pages, cover).
3. Kieran approves the look, the cover; upload to KDP (about 72 hours review).
4. Live about 3-4 weeks after `go`. No gift deadline; best to be live by mid-January so it catches the birthdays of the whole year and Father's Day (20 June 2027).

## 8. Risks and runners-up

- **Risks:** big publishers hold this shelf; evidence is thin; "50" dates the title (a later 40th, 60th variant could use the same engine); overlap with the retirement book's older buyer.
- **Runner-up 1:** *The Newly Engaged Man's Guide to His Own Wedding* (hobby-neutral, a very large occasion; needs a check that wedding humour is not saturated).
- **Runner-up 2:** *The Man in the Waiting Room: the NHS Appointment Handbook*, a short deadpan companion for the 50th-birthday health check (small, cheap, niche).

## 9. Sources

- [Marcus Berkmann, A Shed of One's Own (Bookends)](https://www.welcometobookends.co.uk/titles/marcus-berkmann/a-shed-of-ones-own/9780349146294/)
- [Still a Bit of Snap in the Celery (Hachette UK)](https://www.hachette.co.uk/titles/marcus-berkmann/still-a-bit-of-snap-in-the-celery/9780349145495/)
- [How to Grow Old (Penguin)](https://www.penguin.co.uk/books/440355/how-to-grow-old/)
- [The Dangerous Book for Middle-Aged Men (Agenda Bookshop)](https://agendabookshop.com/products/dangerous-book-for-middle-aged-men)
- [50 - Older Possibly Wiser (Narborough Hall)](https://www.narboroughhall.co.uk/collections/humour-gifts/products/50-older-possibly-wiser)
- [The Book of Everyone 50th Birthday (Wonderbly)](https://wonderbly.com/personalized-products/tboe-milestone-50th-birthday-edition-book)
- [Things to Do Now That You're 50](https://pastforward.org/products/things-to-do-now-that-youre-50-9780600638735)
