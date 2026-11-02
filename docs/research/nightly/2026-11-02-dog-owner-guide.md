# Proposal: a Dave-style guide for the dog person in the house (angle 3, a new line)

Nightly research run, 2 November 2026. Angle 3 of the rotation (the last run was angle 2, the voucher book).

## 1. Decision needed

**Book: *The Dog Owner's Guide to Remembering It Is a Dog*, a straight-faced official programme for the person whose dog now has its own birthday party, its own sofa and a say in the holiday. Reply `go` or `no` (and why).**

## 2. The pitch

- **Title (working):** *The Dog Owner's Guide to Remembering It Is a Dog: An Official Programme for the Person Who Has Referred to Himself as "Dad" at the Vet*
- **Who buys it:** a partner, a sibling or a friend, for the dog owner. Roughly 41% of UK households now have a dog (about 15.5 million dogs, UK Pet Food survey, March 2026), a far wider group than any single hobby.
- **When:** not tied to one date. Birthdays and stocking fillers work; Mother's Day (7 March 2027) and Father's Day (Sunday 20 June 2027, my own count) suit "dog mum / dog dad" jokes. It cannot be live for most of Christmas 2026 (section 7), so aim at Valentine's to Father's Day.
- **Why now:** dog ownership is at a record high and the buyer pool is far bigger than golf or padel.
- **Different from Amazon:** the dog humour I found is photo books, cartoons and "the dog's inner thoughts" (the dog narrates). I found no deadpan official manual about the owner's behaviour, aimed at the owner's household, in the Dave style.

## 3. Evidence

How sure am I: **low.** The Amazon refresh returned nothing again (the script hung and produced no file, as in earlier runs). What I have is publisher and bookseller listings from web search.

| Title | Publisher | Price | Notes |
|---|---|---|---|
| The Dog Owner's Survival Guide (Tatiana Davidova) | Hachette (big) | £7.99 | Illustrated tongue-in-cheek advice; closest competitor |
| I Bark, Therefore I Am | Simon & Schuster (big) | not found | Photo book, listed for 20 Oct 2026 |
| You're Not a Real Dog Owner Until... | Simon & Schuster (big) | not found | Cartoon observations |
| Off the Leash (Rupert Fawcett) | not confirmed | not found | Cartoon book with a sequel, so the first sold |
| Funny Dogs (Charlie Ellis) | not confirmed | £7.99 | Photo and caption book |
| Absolutely Barking (Michele Hanson) | not confirmed | not found | Essays on British dog owners |

What this says:
- Dog humour is a real, repeating gift category. A Waterstones gift buyer says puzzle, quiz and joke books never go out of fashion.
- Everything I found is from a large publisher, is picture or cartoon led, or has the dog as narrator.
- I have **no rank, review counts or sales**, so I cannot say a small publisher can reach the top 20. The shelf is crowded and cheap (£3.99-£7.99).

**Verdict: weak evidence, worth a cheap test at best.** The wide buyer pool is the argument for; big publishers already on the shelf are the argument against.

## 4. The book plan

- **Format:** 6 x 9 in, black and white, about 80 pages. £9.99 UK / $9.99 US, earning about £4.06 / $3.69 a copy (royalty table in `docs/research/2026-09-30-new-book-types.md`; check KDP's calculator at upload).
- **Pen name:** the Dave brand, same big-lettering cover. Dave gets a spaniel (name to be agreed at intake).
- **Contents (numbered activities, as in the live books):**
  1. Welcome to the Programme (a dog is not a child; please read this twice)
  2. Stage 1: Terminology ("dad", "mum", "his brother", "she's had a big day")
  3. Stage 2: The Walk (20 minutes allowed, 2 hours 10 taken)
  4. Stage 3: Furniture and Sleeping (whose bed it is; the sofa treaty)
  5. Stage 4: Spending (the orthopaedic bed; the birthday cake with a candle)
  6. Stage 5: Holidays (dog-friendly, therefore not child-friendly)
  7. Stage 6: Photographs (400 photos, 3 of the family)
  8. Stage 7: The Vet (a risk assessment with a tick-box for "has he cried")
  9. Diagnostic: "Are you a Dog Owner or a Dog's Assistant?"; cut-out "Certificate of Good Boy"
- **Picture budget:** none inside (typeset activity pages). One cover picture, about 2 credits. I could not read the Higgsfield balance (connector not available); last known 6 credits.
- **Cover direction:** big title, one family scene: Dave on the floor at the edge of the sofa, the spaniel in his chair, his wife holding the lead. A plain empty band across the top for the title.

## 5. Samples (original)

**Back cover:** "Dave has owned a dog for 14 months and has referred to himself as its father 31 times. He has a framed photo of it at work. He has never framed one of the children. This is the official programme for getting him from the dog park to a normal Saturday without anyone saying 'he's family'."

**Three sample activities:**
1. *No. 03: The Walk.* Time allowed: 20 minutes. Time taken: 2 hours 10. People spoken to: 6. Names of the people known: 0. Names of their dogs known: 6.
2. *No. 09: Terminology.* Tick the words you have used this week. [ ] "He's had a big day." [ ] "She doesn't like that." [ ] "Her brother." Score: 3 ticks, you have a brother-in-law who is a spaniel.
3. *No. 14: The Sofa Treaty.* Cushions the dog has: 4. Cushions you have: 0. Who signed the treaty: you.

**Certificate:** "Official Dog Owner. Qualified to hold a lead. Not qualified to carry a birthday cake."

## 6. What Book Factory needs

- **Can it make this today?** Probably yes, with no build work: `activity` pages with ticks, scores and a certificate (`docs/RENDERING.md`) are how the live books are made. I have not run a trial; likely, not certain.
- Copy to write: manuscript, cover copy, diagnostic. `/write-book` does this. The one picture is the cover.

## 7. Timeline

1. `go`, then `/write-book "The Dog Owner's Guide to Remembering It Is a Dog"` (2-3 sittings, after any book already started).
2. Cover picture, cover build, Kieran approves the cover.
3. KDP upload and a printed proof (allow 2-3 weeks including shipping), then KDP review (up to 72 hours).

Realistic live date if started this week: **early to mid-January 2027.** That misses Christmas, so target Valentine's, Mother's Day and Father's Day. If you want something for Christmas, the Christmas quiz proposal is the better fit.

## 8. Risks and runners-up

Risks:
- Thin evidence, and big publishers (Hachette, Simon & Schuster) already sit in dog humour.
- Cheap photo and cartoon books look nicer on a shelf.
- Misses Christmas 2026.

Runners-up:
- *The Cat Owner's Guide to Being Tolerated* (same format, smaller buyer pool, less crowded).
- *The Allotment Addict's Guide to Weekends Indoors* (from `docs/BOOK-IDEAS.md`, a Dave-series pick not yet proposed).

## 9. Sources

- [UK Pet Food: 15.5 million dogs in UK homes (March 2026)](https://www.ukpetfood.org/resource/britain-s-dog-ownership-boom-as-15-5-million-dogs-now-live-in-uk-homes.html)
- [PDSA Animal Wellbeing mini report 2025](https://www.pdsa.org.uk/media/15783/pdsa-paw-mini-report-2025.pdf)
- [The Dog Owner's Survival Guide, Hachette](https://www.hachette.co.uk/titles/tatiana-davidova/the-dog-owners-survival-guide/9781800078574/)
- [The Dog Owner's Survival Guide, Waterstones](https://www.waterstones.com/book/9781800074002)
- [You're Not a Real Dog Owner Until..., Simon & Schuster](https://www.simonandschuster.co.uk/books/Youre-Not-a-Real-Dog-Owner-Until/Jason-Chatfield/Youre-Not-a-Real/9781524892357)
- [I Bark, Therefore I Am, Simon & Schuster](https://www.simonandschuster.co.uk/books/I-Bark-Therefore-I-Am/Charlotte-Jean/Inner-Monologues-of-the-Domesticated/9781685553135)
- [Topping Books humour and gift books](https://www.toppingbooks.co.uk/collections/humour-puzzle-gift-books/)
- Royalty table: `docs/research/2026-09-30-new-book-types.md`
