# Proposal: a Dave-world book for her, *The Hobby Widow's Guide to Having a Life* (angle 3, a new line)

Nightly research run, 7 October 2026. The rotation moved on from angle 2 (the advent book of 5 October) to angle 3, a new line.

## 1. Decision needed

**Book: *The Hobby Widow's Guide to Having a Life*, a funny gift book written for the woman who lives with a hobby addict, live on Amazon by about 15 January 2027 (in time for Valentine's Day and UK Mother's Day). Reply `go` or `no` (and why).**

## 2. The pitch

- **Title and subtitle (working):** *The Hobby Widow's Guide to Having a Life: Rulings, Quizzes and Permission Slips for Anyone Who Lives With Someone Else's Hobby*
- **Who buys it:** the partner herself (a treat), her friends and sisters, and the grown-up kids ("Mum, this is you"). The Dave books are bought *about* him; this one is bought *for her*. The same household, a second gift.
- **When:** Valentine's Day (14 Feb 2027) and UK Mother's Day (7 Mar 2027). Live by about 15 January, so there is time to get found. It also works at Christmas 2027 and for every Dave sport, because the hobby is never named in the title.
- **Why now:** it is a new buyer for the Dave brand at no extra cost, it can be buyable on the same Amazon search ("gift for wife of golfer"), and it fills the quiet gap between Christmas and Father's Day. UK retailers report parody and humour books taking a big slice of the Mother's Day gift market (Bookseller, link below).
- **What is different:** the funny books about hobby obsession (e.g. *The Golfer's Excuse Handbook*) talk to the man or to the sport. I found none aimed at the person left at home. The Dave books already sell the joke from the family's side; this makes it the star.

## 3. Evidence

How sure am I: **low to medium.** Amazon's list pages loaded tonight but the script found no titles (their page layout has probably changed; `scripts/research/amazon_bestsellers.py` needs a fix), so the numbers below are from the 30 September snapshot. The Higgsfield balance tool was not available; the last known balance is 6 credits. I found no sales figures for a "for her" hobby book, so this is a **cheap test, not a sure thing**.

| What the data shows | Number | What it means |
|---|---|---|
| Hobby-obsession humour sells for a small publisher | *The Golfer's Excuse Handbook* (Red Panda Press): US Humor Sports #6, $8.50, 104 pp, 1,522 reviews, published Nov 2022, still ranking in 2026 | A funny book on one hobby lasts for years |
| Small publishers sit in sports humour | US Humor Sports: 3 of 11 known publishers small; *157 Ways to Kick Bass* (fishing, $14.99, 118 pp, 127 reviews) | A $14.99 niche gift book can sell |
| UK love/marriage and parody humour lists | Top 5 are all big publishers (Penguin, Fourth Estate and the like), mostly novels | Our book should not aim at these lists; it belongs in "gift for wife / husband" searches |
| Mother's Day parody books | "Parody books lead Mother's Day sales" (Bookseller, linked) | Real seasonal demand in the UK |

| Nearby book | Rank | Price | Pages | Reviews | Publisher |
|---|---|---|---|---|---|
| The Golfer's Excuse Handbook | US Humor Sports 6 | $8.50 | 104 | 1,522 | Red Panda Press (small) |
| 157 Ways to Kick Bass | US Humor Sports 7 | $14.99 | 118 | 127 | Independent (small) |
| Disappointing Affirmations | US Humor Parodies 12 | $12.61 | 96 | 1,102 | Chronicle (big) |
| The Mum Book / The Dad Book | UK gift lists, not ranked in our snapshot | £9.99 | about 100 | not checked | Hachette (big) |

Honest verdict: demand for the *form* is clear, demand for *this exact book* is a guess. It costs nothing in credits besides one cover picture and no build work, so the risk is small.

## 4. The book plan

- **Format:** 6 x 9 inch paperback, black and white inside, about **72 pages**, same as Golf and Padel.
- **Price and earnings:** UK £9.99 earns about **£4.06** a copy, US $9.99 about **$3.69** (60% royalty minus £1.93 / $2.30 printing, from the first report).
- **Pen name:** the Dave brand (Kieran Smith), so it shelves beside the other books.
- **Contents:** all `activity` pages (typeset, no pictures), in 6 parts:
  1. **The Rulings** (14): official decisions on household disputes ("Is the third round of the day a round?").
  2. **The Quizzes** (10): "Which of these did he say this week?", "Guess the cost of the new thing".
  3. **The Permission Slips** (8): cut-out slips she may hand out to herself ("Valid for one Saturday with no mention of it").
  4. **The Gauges** (6): fill-in dials (hours of conversation about his hobby, 0 to "I have learned his handicap").
  5. **The Diagnostics** (6): "How far gone is he?" and "How far gone are you?" tick lists.
  6. **The Certificates** (4) and a closing **Declaration of Independence** she signs.
- **Pictures:** none inside. The cover is one picture (about 2 credits), a woman on the sofa with a cup of tea and a glass of wine while a man in the background demonstrates a swing with a lampshade.
- **Cover direction:** big lettering, same Dave typeface, warm pink-and-cream palette (the one change from the live books), one family scene.

## 5. Samples

**Back-cover blurb (draft):**
> You didn't marry the hobby. The hobby arrived afterwards, moved in and now has its own wardrobe. This is the book for the person who has learned the offside rule, the stroke index and the price of a carbon frame, and would like to learn something else for a change. Rulings, quizzes and permission slips for taking your life back, one Saturday at a time.

**Sample page, Ruling No. 03: "The Quick One"**
> *Question:* He says he is going out for "a quick one". Is it a quick one?
> *Ruling:* A quick one is any activity that finishes before the soup goes cold. If the soup has gone cold, it was a normal one. If he has changed shoes, it was a long one. If he has asked "do we have any plasters", it was a session.
> *Penalty:* He cooks the next meal. Soup included.

**Sample page, Permission Slip No. 02**
> THIS SLIP ENTITLES THE HOLDER to one full Saturday in which nobody says the word "round", "set", "mile" or "gears". Valid at home, in the car and at his mother's. Not valid during a final. Signed: ____ (cut along the dotted line)

**Sample page, Gauge No. 01: "How Much Have You Learned Against Your Will?"**
> A dial from *Nothing* to *I could referee it*. Shade to the level you have reached. Anything above half is a cry for help.

## 6. What Book Factory needs

Everything exists today: `activity` pages (ticks, gauges, tables, cut-out cards, certificates) are built (Phase 16) and the picture budget is one cover picture. No build phase. Steps: `/write-book` with the title, policy `visual_checkpoint` (Kieran's choice; it is the recommended one), the locked Dave voice copied by `--series-from` the Golf book, and the cover picture drawn with Kieran's approval.

## 7. Timeline

| Step | When |
|---|---|
| `go` from Kieran, `/write-book` starts (2 or 3 sittings; the retirement book is still in Visual Development, so one at a time) | after the retirement book's pictures, about 20 October |
| Copy, page plan and renders | by about 12 November |
| Cover, Kieran's approval, KDP files | by about 1 December |
| Printed proof (about 1 week) and upload; KDP review 3 to 10 days | by 20 December |
| **Live on Amazon** | **about 5 January 2027, before Valentine's Day** |

Note KDP limits each account to 2 new titles a week; this is not a problem.

## 8. Risks and runners-up

Risks:
- Demand for a "for her" hobby book is unproven (low evidence). A cheap test, but it may sell like a quiet extra.
- Mocking him is the joke; it must stay affectionate, or it tips into the cruel tone the voice bible bans.
- The tick-list pages may feel like the Dave books reworded; the "permission slips" and gauges must be distinct.

Runners-up:
1. *The Golf Addict's Puzzle Book* (the earlier research's number one): strong data (US Word Search small publishers at #1), but needs a puzzle page built first (about 2 phases).
2. A murder-mystery puzzle book ("Who Nicked Dave's Putter?"): the hottest trend (*Murdle Heist* is out 8 October 2026), and it also needs the puzzle page plus careful clue writing.
3. Dave football or new-dad (options B and C from 2 October): same buyer, nothing to build, no new idea.

## 9. Sources

- [Bookseller: trade prepares for Mother's Day](https://thebookseller.com/news/trade-prepares-mothers-day-steel-and-spa-days-745191)
- [For Reading Addicts: parody books leading Mother's Day sales](https://forreadingaddicts.co.uk/8-books-mum-mothers-day/)
- [Hachette: The Mum Book](https://www.hachette.co.uk/titles/forest-xiao-2/the-mum-book/9781408374085/)
- [Murdle series, Profile Books (Murdle Heist, 8 Oct 2026)](https://mitpressbookstore.mit.edu/book/9781250892317)
- Amazon.co.uk and Amazon.com bestseller lists, snapshot of 30 September 2026: `docs/research/2026-09-30-amazon-bestsellers.csv`
- [KDP paperback printing cost](https://kdp.amazon.com/en_US/help/topic/G201834340)
