# Proposal: a Dave-style guide for the barbecue dad (angle 1, Dave series)

Nightly research run, 28 October 2026. Angle 1 of the rotation (the last run was angle 3, the new grandad).

## 1. Decision needed

**Book: *The Barbecue Dad's Guide to Cooking Indoors*, a straight-faced official programme for the man who treats a barbecue as a profession. Reply `go` or `no` (and why).**

## 2. The pitch

- **Title (working):** *The Barbecue Dad's Guide to Cooking Indoors: An Official Programme for the Man Who Has Been Standing in the Rain Since 4 a.m.*
- **Who buys it:** his wife, partner or grown-up kids, for the man with the smoker, three thermometers and a strong view on charcoal. Same gift buyers and same look as Golf and Padel.
- **When:** Father's Day, Sunday 20 June 2027 (my own calculation, third Sunday in June). Also the start of barbecue season (April to May) and birthdays. Live by early June at the latest, ideally mid-May.
- **Why now:** it is the number 3 "top pick" in `docs/BOOK-IDEAS.md` and has not been proposed yet. A big group (barbecue is the most mainstream "hobby" on the list) with a long season, and it needs no build work.
- **Different from Amazon:** barbecue books are recipe books (Tom Kerridge, Summersdale's *The Dad's BBQ Cookbook*) or joke-and-fact gift books aimed at the man himself. I found none that is a deadpan manual aimed at the household he lives in: the 4 a.m. brisket, the November barbecue under an umbrella, the side salad in the kitchen.

## 3. Evidence

How sure am I: **low.** The Amazon refresh gave no data again (the script hung and returned nothing from this machine, as in earlier runs). Higgsfield is not available in this run, so I could not read the credit balance (last known: 6 credits, before the Retirement book). What I have is publisher and retailer listings from web search, and none of them gives a sales rank.

| Title | Publisher | Price | Notes |
|---|---|---|---|
| The Dad's BBQ Cookbook (Sam Brooks) | Summersdale (Hachette UK), gift publisher | £10.99 | Recipe book "for dads", also in hardback; closest in buyer |
| The BBQ Book (Tom Kerridge) | Bloomsbury | about £25 | Described as a Sunday Times bestseller (publisher claim); a recipe book, a different job |
| How to BBQ Everything | big publisher | about £11 e-book | Billed as an instant Sunday Times bestseller (retailer claim); recipes |
| The Little Book of BBQ | Orange Hippo | not found | Closest to a joke gift book, pitched at Father's Day; the listing I found was Australian, UK availability unchecked |

What this says:
- Barbecue gift and recipe books are a real, repeating Father's Day category.
- Everything found is recipes or generic jokes and facts. No deadpan "life with the barbecue man" manual turned up.
- The category has big names (Kerridge, Hachette). I have **no rank, no review counts and no sales figures**, so I cannot say whether a small publisher can reach the top 20.
- Indirect demand signs: retailers pushed barbecue and smoker products hard in 2025-26 (Klarna data named Ninja Woodfire grills among the most bought), and Ninja launched its first UK gas barbecue and an indoor griddle in 2026. That suggests plenty of new barbecue owners; it is not book sales data.

**Verdict: weak evidence, worth a cheap test.** It is cheap because it is all text and the Dave look exists. If you want proof first, the Golf and Padel sales are the better test.

## 4. The book plan

- **Format:** 6 x 9 in, black and white, about 80 pages. £9.99 UK / $9.99 US, earning about £4.06 / $3.69 a copy (royalty table in `docs/research/2026-09-30-new-book-types.md`; check KDP's calculator at upload).
- **Pen name:** the Dave brand (Kieran Smith), same big-lettering cover as Golf and Padel.
- **Contents (numbered activities, as in the live books):**
  1. Welcome to the Programme (what a barbecue is: "a kitchen, but worse")
  2. Stage 1: Equipment (three thermometers, one smoker, one opinion about charcoal)
  3. Stage 2: The Early Start (the 4 a.m. brisket for a 1 p.m. lunch)
  4. Stage 3: Weather (the November barbecue in a coat, under an umbrella; a decision tree)
  5. Stage 4: The Guests (what he says when someone asks for it well done)
  6. Stage 5: The Kitchen (the oven is not broken; a gentle reintroduction)
  7. Stage 6: The Sides (who made the salad, and who is allowed to say so)
  8. Stage 7: The Clean-Up (the grill brush, the fat, the shared bin)
  9. Diagnostic: "Are you a Barbecue Dad or a Man With a Fire Problem?"; a cut-out "Certificate of Indoor Competence"
- **Pictures:** none inside (typeset activity pages only). One cover picture, about 2 credits.
- **Cover direction:** big title, one family scene: Dave in a coat and wellies at the smoker in the rain, umbrella taped to the lid, the family at the kitchen window with a plate of salad. A plain empty band across the top for the title.

## 5. Samples (original)

**Back cover:** "Dave got up at 4 a.m. to start a brisket for a lunch at 1. It is now November. It is raining. He is wearing a coat indoors-out and calling it 'the bark'. This is the official programme for getting him from the smoker to the oven, one tray of chips at a time."

**Three sample activities:**
1. *No. 02: Equipment Check.* Tick the items you own. [ ] a smoker [ ] a second smoker [ ] three thermometers [ ] a thermometer for the thermometers. Score: 4 ticks, you may call it "a setup". Not a hobby.
2. *No. 07: The Weather Decision.* Is it raining? If yes, go to 2. If no, go to 3. 2: "It adds moisture." Go to 4. 3: It is January. Go to 4. 4: Light the barbecue.
3. *No. 12: Indoor Cooking, Trial Run.* Time allowed: 30 minutes. Cook one chicken in the oven. Number of times you open the door to check it: 0 allowed, 9 recorded. Number of times you say "it'll be better outside": ______.

**Certificate:** "Official Indoor Cook. Qualified to use the hob, the oven and a plate. Not qualified to say 'low and slow' at a Tuesday dinner."

## 6. What Book Factory needs

- **Can it make this today?** Probably yes, with no build work: the live books are made the same way (`activity` pages with ticks, scores, a decision-style layout and a certificate, `docs/RENDERING.md`). I have not run a trial; treat it as likely, not certain.
- Copy to write: the manuscript, the cover copy and the diagnostic. `/write-book` does this. The one picture is the cover.

## 7. Timeline

1. `go`, then `/write-book "The Barbecue Dad's Guide to Cooking Indoors"` (about 2-3 sittings, after the books already queued: Retirement and any Christmas pick).
2. Cover picture, cover build, Kieran approves the cover.
3. Upload to KDP and order a printed proof (allow 2-3 weeks including shipping).
4. KDP review (up to 72 hours, longer for a new account's first print books).

Realistic live date if started in January: **February-March 2027.** The hard deadline is early June 2027 for Father's Day. Nothing here competes with this Christmas.

## 8. Risks and runners-up

Risks:
- Thin evidence: no ranks, no sales; Summersdale and Hachette already hold the barbecue-dad shelf.
- Seasonal: barbecue is spring and summer, so Christmas sales will be weaker than the golf and padel books (though a barbecue dad is a fine stocking-filler).
- Brand names: avoid naming real products (Weber, Ninja, Traeger) on the cover or in the title.

Runners-up:
- *The Fantasy Football Manager's Guide to Real Life* (huge group, but football trademarks and many existing football books).
- *The Wild Swimmer's Guide to Warm Water* (a growing hobby, but a smaller gift-buying group).

## 9. Sources

- [The Dad's BBQ Cookbook, Hachette UK](https://www.hachette.co.uk/titles/sam-brooks/the-dads-bbq-cookbook/9781837994991/)
- [The BBQ Book (Tom Kerridge), Foyles](https://www.foyles.co.uk/book/the-bbq-book/tom-kerridge/9781526684899)
- [How to BBQ Everything, Pocketbook](https://pocketbook.uk/how-to-bbq-everything-9781529975765)
- [The Little Book of BBQ, Collins Books](https://collinsbooks.com.au/p/the-little-book-of-bbq-get-fired-up-it-s-grilling-time)
- [Klarna BBQ trends ahead of National BBQ Week, Retail Times](https://retailtimes.co.uk/klarna-reveals-sizzling-trends-ahead-of-national-bbq-week/)
- Royalty table: `docs/research/2026-09-30-new-book-types.md`
