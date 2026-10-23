# Proposal: a Dave-style Christmas Day quiz for the whole family (angle 2, a new format for the same buyers)

Nightly research run, 23 October 2026. Angle 2 of the rotation (the last run was angle 1, the fishing book).

## 1. Decision needed

**Book: *The Hobby Addict's Family Christmas Quiz*, 12 quiz rounds about Christmas Day in a house where one person's hobby has taken over the day. Reply `go` or `no` (and why).**

## 2. The pitch

- **Title (working):** *The Hobby Addict's Family Christmas Quiz: 12 Rounds for the Table Where Somebody Keeps Checking the Football Scores*
- **Who buys it:** the same people who buy the Dave books (the wife, partner or grown-up kids), for Christmas Day itself: the quiz comes out after the main meal. It is a game for the whole table, so it is bought as a shared present, a host gift or a stocking filler.
- **When:** this Christmas only needs to be live about **13-20 November** (a quiz is bought later than a gift book, since it is for the day). It then comes back every December; the rest of the year it is a dead book, so it must earn its keep in six weeks.
- **Why now:** Christmas quiz books are a standing UK category. Big publishers fill it (Very British Problems Christmas Quiz Book, £10.99, October 2025; So This is Christmas Quiz Book, £10.99; 1% Club Book 2, £14.99). All are general trivia. None is funny about the family at the table.
- **Different from Amazon:** the questions are about *your own household*: "Who said 'I'll just be five minutes' before the Boxing Day ride?" It is a quiz about people, not facts, so any family can play it with no knowledge needed.

## 3. Evidence

How sure am I: **low.** My Amazon refresh returned 0 titles for every list again (the script is blocked from this machine, as in earlier runs), so I have no ranks, prices or review counts of my own. What I have is publisher listings from web search.

| Title | Publisher | Price | Notes |
|---|---|---|---|
| The Very British Problems Christmas Quiz Book | Little, Brown (big) | £10.99 | Paperback, 23 Oct 2025; pitched as a stocking filler |
| So This is Christmas Quiz Book | Bonnier (big) | £10.99 | 1,500+ questions, 34 quizzes, Oct 2022 |
| The 1% Club Book 2 | Bantam (big) | £14.99 | Family quiz with Christmas quizzes |
| The Holly Jolly Christmas Quiz Book | gift publisher | £9.99 | Party games and a team quiz; out of stock at the V&A shop |
| The Christmas Quiz (L. J. Sanderson) | not confirmed | not found | 700+ questions, anagrams |

What this says:
- Christmas quiz books are a real, repeating category, and the leaders are big publishers with general trivia. That is a hard place for a small publisher on rank alone.
- Our edge is the angle, not the facts: a funny quiz about the household. The 30 September report found quiz and trivia lists are where small publishers do get into the top 20, but I could not re-check that for Christmas quizzes.
- I found no small-publisher Christmas quiz bestseller, and no sales figures. That may be a gap or a sign the seasonal quiz does not pay for a small publisher.

**Verdict: weak evidence, worth a cheap test.** It is cheap because everything is text and the Dave look already exists.

## 4. The book plan

- **Format:** 6 x 9 in, black and white, about 90 pages. List price £8.99 UK / $9.99 US, which earns about **£3.46 a copy in the UK and $3.69 in the US** (printing £1.93 / $2.30 up to 110 pages; royalty table in `docs/research/2026-09-30-new-book-types.md`; check KDP's calculator at upload).
- **Pen name:** the Dave brand, same big-lettering cover as Golf and Padel.
- **Contents:**
  1. How to play (teams, a scorer who is not allowed to be the loudest person, "the referee's decision is final, and the referee is whoever cooked")
  2. Round 1: Who Said It? (the quotes of Christmas morning)
  3. Round 2: The Great Christmas Dinner (timings, gravy, the sprout nobody ate)
  4. Round 3: Present or Purchase? (what the hobby person bought themselves "for the house")
  5. Round 4: Hobby Corner (golf, padel, running, cycling: a mixed round, answers are household facts)
  6. Round 5: Boxing Day Plans (the ride, the round, the fixture list)
  7. Round 6: Guess the Price (the list of things "it was about £800")
  8. Round 7: Film Night (the one everyone has seen eleven times)
  9. Round 8: Grandparents' Round (an easier round so everyone scores)
  10. Rounds 9-12: Picture-free "Name That" rounds (anagrams, odd-one-out, Christmas song titles with a word wrong), plus a tie-break
  11. Scorecard pages and a cut-out "Champion of Christmas" certificate
  12. Answer key
- **Pictures:** none inside, so no page-picture credits. One cover picture (about 2 credits). I could not read the Higgsfield balance (connector not available in this run); last known balance 6 credits, and the Retirement cover may have used some.
- **Cover direction:** the family round the table after dinner, paper hats on, the hobby person half out of his chair holding a phone, a plain empty band across the top for the title.

## 5. Samples (original)

**Back cover:** "It is 4pm on Christmas Day. The turkey is a memory. Someone has the football on mute. Somebody else has said 'right, quiz?' in a brave voice. This book is that quiz: twelve rounds about the people at your own table. No general knowledge needed. Dave is not allowed to be quizmaster."

**Five sample questions:**
1. *(Who Said It?)* "I'm only going to be an hour." Which day of the Christmas holidays does this get said, and how long is the actual hour? (A: Boxing Day; five.)
2. *(Dinner)* In what order does the family sit down? Put in order of appearance: the cook, the hobby person, the person who was told twice, the dog. (A: dog, cook, person who was told twice, hobby person, after the second call.)
3. *(Present or Purchase)* The new gadget was "for the house". Who uses it? (A: him; once; in the garage.)
4. *(Guess the Price)* The kit under the tree was "about £80". What did it cost: £80, £180 or £380? (A: depends on whether the receipt is found. It is not found.)
5. *(Hobby Corner)* Odd one out: a birdie, an eagle, a bogey, a Boxing Day. (A: the Boxing Day; it is the only one he has played badly on purpose to get out of the washing-up.)

**Sample certificate:** "Champion of Christmas. Awarded to the person who got the most right and was told not to go on about it."

(The finished book's anagrams and answers get checked by script before it is written, because a wrong answer key is the main way a quiz book gets bad reviews.)

## 6. What Book Factory needs

- **Can it make this today?** Probably yes, with no build work. The `activity` page type can set numbered questions with answer lines, a scorecard and a cut-out certificate as real type (`docs/RENDERING.md`). I have not run a trial; treat it as likely, not certain. The answer key goes at the back as ordinary text pages.
- **Check anagrams and answers by script** before writing the final copy (a small throwaway script in the scratchpad, not a Book Factory change).
- Copy to write: about 150-180 questions, the rules, scorecards, certificate and cover copy. `/write-book` does this.

## 7. Timeline

Today is 23 October. The Retirement book is already in visual development, so this competes for sittings with it.

1. Day 0: `go`, then `/write-book "The Hobby Addict's Family Christmas Quiz"` (about two or three sittings).
2. Cover picture, cover build, Kieran approves the cover.
3. Upload to KDP. A printed proof (5-7 days) probably does not fit this Christmas: either skip it and accept the risk, or order it and go live late.
4. KDP review (usually under 72 hours).

Realistic live date if started this week: **about 15-22 November.** If it slips past early December, the book is dead until next year and I would then say no.

## 8. Risks and runners-up

Risks:
- Evidence is thin: no rank data of my own and a category led by big publishers.
- Seasonal: sells in about six weeks of the year.
- A quiz lives or dies on correct answers; every answer needs checking.
- Overlaps in buyer and date with the awaiting Advent Calendar proposal (2026-10-05); I would pick only one of the two for this Christmas.

Runners-up:
- *The Hobby Addict's Quiz: How Well Do You Know the Man You Live With?*, the evergreen version of this idea (no Christmas deadline, more crowded with Summersdale titles).
- A *Boxing Day Survival Log* (a funny planner and record for the days between Christmas and New Year); weaker, because Amazon treats log books as low-content.

## 9. Sources

- [The Very British Problems Christmas Quiz Book, Foyles listing](https://www.foyles.co.uk/book/9781408730676)
- [So This is Christmas Quiz Book, Bonnier](https://bookshelf.bonnierbooks.co.uk/books/9781800783393)
- [The 1% Club Book 2, Penguin](https://www.penguin.co.uk/books/468638/the-1-club-book-2-by-none/9780857507334)
- [The Holly Jolly Christmas Quiz Book, V&A Shop](https://www.vam.ac.uk/shop/books/all-books/the-holly-jolly-christmas-quiz-book-164352.html)
- Royalty table and KDP rules: `docs/research/2026-09-30-new-book-types.md`
