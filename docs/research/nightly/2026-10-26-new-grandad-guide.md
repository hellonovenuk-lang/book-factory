# Proposal: a Dave-style guide for the new grandad (angle 3, a new line)

Nightly research run, 26 October 2026. Angle 3 of the rotation (the last run was angle 2, the Christmas quiz).

## 1. Decision needed

**Book: *The New Grandad's Guide to Being Handed the Baby*, a straight-faced official manual for the man who has just become a grandad. Reply `go` or `no` (and why).**

## 2. The pitch

- **Title (working):** *The New Grandad's Guide to Being Handed the Baby: An Official Programme for the Man Who Has Been Told "You Can't Do It Like That Any More"*
- **Who buys it:** the new parents (his grown-up children) or his wife, for a man who has just become a grandad (a very big group every year) or is about to. They are the same gift buyers as the Dave books, one generation up.
- **When:** Father's Day, Sunday 20 June 2027 (my own calculation, third Sunday in June; I did not find it in a source). It also works year-round for birthdays and "it's a boy / girl" announcements, so it is not a one-date book. Live by early June at the latest.
- **Why now:** it is a quiet slot. Nothing is urgent, so it does not compete for sittings with the Christmas proposals still awaiting you.
- **Different from Amazon:** the grandad books I found are warm and sentimental (quotes, picture books). None is a deadpan manual about the *household* a grandad lives in: the car seat he cannot fit, the new rules about honey and sleeping positions, the golf he has "given up for the baby" (he has not).

## 3. Evidence

How sure am I: **low.** My Amazon refresh gave no data again (the script hung and returned nothing from this machine, as in earlier runs). What I have is publisher and bookseller listings from web search.

| Title | Publisher | Price | Notes |
|---|---|---|---|
| Grandad's Wit and Wisdom (Richard Benson) | Summersdale (gift publisher) | £9.99 | Hardback, quips about grandad life; closest competitor |
| Grandad - You're the Best! (Adrian Besley) | Carlton | not found | 300+ quotes, anthology |
| Grandads Are the Greatest (Faulks / Tudor, 2023) | not confirmed | not found | Rhyming picture book, warm not funny |
| I Love My Grandad (Giles Andreae) | Hachette | £7.99 | Picture book, for the child to give |
| What Not to Say to Your Husband (Quercus, 2020) | Quercus | £12.99 | Shows that husband-gift humour sells at £12.99 |

What this says:
- Grandad gift books are a real, repeating category in the Father's Day and Christmas gift lists.
- Everything I found is quotes, anthologies or picture books. I found no deadpan manual and no small-publisher bestseller.
- I have **no rank, no review counts and no sales figures**, so I cannot say whether a small publisher can reach the top 20 here.

**Verdict: weak evidence, worth a cheap test.** It is cheap because it is all text and the Dave look already exists. If you want proof first, the Golf and Padel sales are the better test.

## 4. The book plan

- **Format:** 6 x 9 in, black and white, about 80 pages. £9.99 UK / $9.99 US, earning about £4.06 / $3.69 a copy (royalty table in `docs/research/2026-09-30-new-book-types.md`; check KDP's calculator at upload).
- **Pen name:** the Dave brand (Kieran Smith), same big-lettering cover as Golf and Padel.
- **Contents (numbered activities, as in the live books):**
  1. Welcome to the Programme (what a grandad is for: "arrive, admire, hand back")
  2. Stage 1: Pre-Arrival (the hospital bag he packed for himself; the 14 texts "any news?")
  3. Stage 2: Holding the Baby (the correct way; the wrong way; the way he did it in 1994)
  4. Stage 3: The New Rules (no honey, no "back to sleep", no sweets, no nonsense)
  5. Stage 4: Kit and Equipment (the pram he can fold, the car seat he cannot)
  6. Stage 5: Babysitting (a risk assessment, with a tick-box for "has he put the telly on")
  7. Stage 6: The Hobby Handover (the baby's first club, golf set, bike or rod, before it can walk)
  8. Stage 7: Photos (150 photos, 3 of the baby)
  9. Diagnostic: "Are you a Grandad or an Uncle with Opinions?"; a cut-out "Certificate of Grandfatherhood"
- **Pictures:** none inside (typeset activity pages only). One cover picture, about 2 credits. I could not read the Higgsfield balance (connector not available); last known 6 credits, and the Retirement book may have used some.
- **Cover direction:** big title, one family scene: Dave in the armchair holding a baby as if it were a live grenade, mother and grandma watching. A plain empty band across the top for the title.

## 5. Samples (original)

**Back cover:** "Dave has been a father for 31 years and a grandad for 4 days. He has read the leaflet. He has opinions about the leaflet. This is the official programme for getting him from the hospital car park to a successful babysit without anyone saying 'in my day'."

**Three sample activities:**
1. *No. 03: Holding the Baby.* Tick the statements that apply. [ ] I know where the head goes. [ ] I will not say "we never had one of those". [ ] I have not offered it a sip of anything. Score: 3 ticks, you may sit down.
2. *No. 11: Car Seat Fitting.* Time allowed: 20 minutes. Time taken: 2 hours 15. Number of people told "I've got it": 4. Number of times the manual was opened: 0, then 1, then thrown.
3. *No. 14: The Hobby Handover.* List the age at which the baby will be given its first golf club. Acceptable answers: "when she is old enough". Actual answer: Tuesday.

**Certificate:** "Official Grandad. Qualified to hold, admire and return. Not qualified to feed."

## 6. What Book Factory needs

- **Can it make this today?** Probably yes, with no build work: the live books are made the same way (`activity` pages with ticks, scores and a certificate, `docs/RENDERING.md`). I have not run a trial; treat it as likely, not certain.
- Copy to write: the manuscript, the cover copy and the diagnostic. `/write-book` does this. The one picture is the cover.

## 7. Timeline

1. `go`, then `/write-book "The New Grandad's Guide to Being Handed the Baby"` (about 2-3 sittings, after the Retirement book).
2. Cover picture, cover build, Kieran approves the cover.
3. Upload to KDP and order a printed proof (allow 2-3 weeks including shipping).
4. KDP review (up to 72 hours, longer for a first print book from a new account).

Realistic live date if started in January: **February-March 2027.** The hard deadline is early June 2027 for Father's Day. There is no rush this Christmas.

## 8. Risks and runners-up

Risks:
- Thin evidence: no ranks, no sales, and Summersdale already sits in the category.
- Narrower net than a hobby: a grandad is only new once. The buyer pool is wide but each sale depends on a birth in the family.
- "Grandad" competes with sentiment: buyers may want warm, not deadpan.

Runners-up:
- *The Dad Joke Disaster Log*, a funny record book (weaker: crowded with big publishers like Hachette's Dad Joke Loading, and log books are low-content).
- *The Stepdad's Guide to Not Being Called Dad*, a rarer angle, but a sensitive one.

## 9. Sources

- [Grandad's Wit and Wisdom, Winstone Books listing](https://winstonebooks.co.uk/products/9781786850621)
- [Grandad - You're the Best!, Waterstones listing](https://www.waterstones.com/book/9781408338179)
- [Grandads Are the Greatest, Book-ish listing](https://www.book-ish.co.uk/product/grandads-are-the-greatest/)
- [I Love My Grandad, Hachette](https://www.hachette.co.uk/titles/giles-andreae/i-love-my-grandad/9781408346563/)
- [What Not to Say to Your Husband, Hachette](https://www.hachette.co.uk/titles/jason-hazeley/what-not-to-say-to-your-husband/9781529411492/)
- [Dad Joke Loading, Hachette](https://www.hachette.co.uk/titles/harry-hilton/dad-joke-loading/9781837996971/)
- [KDP publishing timeline guide, Vappingo](https://www.vappingo.com/word-blog/kdp-publishing-timeline/)
- Royalty table: `docs/research/2026-09-30-new-book-types.md`
