# Proposal: a book of cut-out vouchers from the hobby addict (angle 2, new format)

Nightly research run, 30 October 2026. Angle 2 of the rotation (the last run was angle 1, the barbecue dad).

## 1. Decision needed

**Book: *The Hobby Addict's Book of Vouchers*, 40 cut-out promises, each with the fine print he would write himself. Reply `go` or `no` (and why).**

## 2. The pitch

- **Title (working):** *The Hobby Addict's Book of Vouchers: 40 Promises From a Man Who Fully Intends to Keep Them*
- **Who buys it:** the hobby addict himself (to hand over when he has run out of gift ideas), or his wife, kids or friends as a joke present that he then has to honour. Same households as Golf and Padel, so it works for every hobby, not one sport.
- **When:** Valentine's Day, Sunday 14 February 2027, and UK Mother's Day, Sunday 7 March 2027 (my own calculation from Easter on 28 March 2027). Live by about 5 January.
- **Why now:** it is a different shape of gift (a thing you give, not a thing you read), it uses the Dave voice we already have, and it needs no pictures inside.
- **Different from Amazon:** coupon books for him or her exist (for example *Coupons for Him*, a small-publisher title) and are sweet or rude. I found none that is deadpan, with terms and conditions ("valid once the season has ended", "subject to the weather, the fixture list and his mood").

## 3. Evidence

How sure am I: **very low.** The Amazon refresh returned nothing again (the script timed out after two minutes from this machine). Higgsfield is not available in this run, so no credit balance (last known: 6 credits). Web search found no sales ranks for any coupon book.

| Fact | Source | Meaning |
|---|---|---|
| KDP lists "coupon books" as an example of a low-content book | KDP help page | A bare coupon book is treated as low-content (no ISBN needed, can't be put in a series). Ours is full of copy, so it should count as normal content, but check at upload |
| Coupon books for him, for couples and blank DIY ones are listed at US retailers at about $9.50-$17.95 | Walmart listings | The format sells as a gift at a normal book price |
| *Coupons for Him* (ISBN 9781999670061, Thomas Media) | Powell's, Porchlight | A small publisher has one in the gift lane, so the lane is open to small publishers |

I found no UK rank, review count or page count for any of them. **Verdict: weak evidence, worth a cheap test only.** I would not pick this over the Golf and Padel sales data once it exists.

## 4. The book plan

- **Format:** 6 x 9 in, black and white, about 56 pages (40 vouchers, two per page, plus front matter and a "terms" page). £7.99 UK / $8.99 US. At that price KDP pays 50%, so about £2.2 a copy (royalty table in `docs/research/2026-09-30-new-book-types.md`; check KDP's calculator at upload). At £9.99 it is about £3.3.
- **Pen name:** the Dave brand (Kieran Smith), same big-lettering cover as the live books.
- **Contents:**
  1. How to redeem a voucher (rules, expiry, "not transferable to a Tuesday")
  2. 10 Household vouchers (a Saturday with no fixture list, one full dinner with phone away)
  3. 10 Family vouchers (one school event attended start to finish, one bedtime story with no comment on the pace)
  4. 10 Couple vouchers (one holiday not planned around his hobby, one afternoon of listening)
  5. 10 Emergency vouchers (one lift to the airport with no detour, one "you were right")
  6. A cut-out Certificate of Redemption and a blank voucher for her to fill in
- **Pictures:** none inside (typeset only). One cover picture, about 2 credits.
- **Cover direction:** big title; Dave holding out a fan of vouchers with a hopeful face, his hobby kit visibly packed by the door behind him; plain band across the top.

## 5. Samples (original)

**Back cover:** "Dave has run out of ideas. He has, however, a pen, a lot of goodwill and no sense of what a promise costs. Inside: forty vouchers, each redeemable once, each with terms. Cut one out. Hand it to him. Watch his face."

**Three sample vouchers:**
1. *This voucher entitles you to: one full Saturday with no mention of the fixture list.* Terms: valid until 11.30 a.m., or kick-off, whichever is first. Not valid in a car.
2. *This voucher entitles you to: one holiday I did not plan around my hobby.* Terms: destination to be agreed. Must have a normal beach. I may ask what the "local scene" is. I may not find out.
3. *This voucher entitles you to: one "you were right".* Terms: may be redeemed in front of other people. Not valid on the subject of the new equipment. That was different.

## 6. What Book Factory needs

- **Today:** the `activity` page type already builds a "cut-out card" from blocks (`docs/RENDERING.md`), all real type, no picture budget used. Forty vouchers on 20 pages is plausible with it, so the book may be buildable without new code. Not tested at 2 per page; a fit check in `/write-book` will say.
- **If a new voucher page is wanted** (dashed border, scissor mark, two per page): one build phase.
- **Tear-out is not possible.** KDP paperbacks cannot be perforated, so the vouchers are cut with scissors, and the cover and blurb must say "cut-out", not "tear-out". Put the voucher text away from the inner margin so cutting is easy.

## 7. Timeline

1. Kieran says `go` (any day).
2. `/write-book`: about 3 sittings (brief, voice, manuscript, look-check, cover). If the voucher page needs building first, add one phase.
3. Kieran approves the cover and uploads to KDP; ~72 hours for review.
4. Live around 5 January 2027 if started by mid-November; if later, aim only at Mother's Day (7 March; live by about 25 January).

## 8. Risks and runners-up

- **Risks:** very thin evidence; a lower price means a lower royalty; low-content classification could limit series and some features; overlaps in buyer and date with the *Hobby Widow's Guide* proposal (awaiting); buyers may expect pre-perforated pages.
- **Runner-up 1:** *The Hobby Addict's Excuse Book* (a fill-in log of reasons for being late, every one used before); same format risk.
- **Runner-up 2:** a Dave "year of holidays" family planner; needs a calendar page type, and planners are crowded.

## 9. Sources

- [KDP: low-content books](https://kdp.amazon.com/help/topic/GGE5T76TWKA85DJM)
- [Powell's: Coupons for Him](https://www.powells.com/book/coupons-for-him-9781999670061)
- [Porchlight: Coupons for Him](https://porchlightbooks.com/product/coupons-for-him--thomas-media/isbn/9781999670061)
- [Walmart: DIY love coupon books for him](https://www.walmart.com/c/kp/diy-love-coupons-him)
- `docs/research/nightly/2026-10-07-hobby-widow-guide.md` and `docs/research/2026-09-30-new-book-types.md` (royalties)
