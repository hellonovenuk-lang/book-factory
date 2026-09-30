# What to publish next: research on new book types

Research run for Kieran, 30 September 2026. Question: beyond the
"Oh F*ck, That's Dave" hobby-addict gift books (three live), which kinds of
book should Book Factory make next, aiming for **simple to produce** and
**high sales volume**? Covered: colouring books, puzzle books, quiz and
trivia, joke books, kids' books, short stories.

Raw data: [`2026-09-30-amazon-bestsellers.csv`](2026-09-30-amazon-bestsellers.csv)
(1,260 rows: the top 30 of 42 Amazon UK and US bestseller lists, with
publisher, price, reviews and page count for the top 20 of each).

---

## The answer in one paragraph

Make **puzzle and quiz books**, starting with ones that carry the Dave
humour to the same buyers. They are the one kind of book where small
self-publishers regularly hold #1 on Amazon, they are growing (Circana:
puzzle, logic and activity books up in Q1 2026), they sell all year and
spike at Christmas, and Book Factory can make them almost entirely by
typesetting: no Higgsfield credits, no picture approvals, no
"near enough" artwork. The hottest corner right now is the **murder-mystery
puzzle book** (small publishers at #1 and #2 in US Word Search with as
few as 49 reviews). Leave colouring books, picture books and short
stories for later: the numbers and the costs are against them for us today.

## Ranked shortlist

| # | Book type | Why | Effort for Book Factory | Verdict |
|---|---|---|---|---|
| 1 | **Dave puzzle & quiz books** for each hobby ("The Golf Addict's Puzzle Book": word searches, quizzes, "spot the excuse", criss-cross puzzles with joke clues) | Same buyer as the live books (the family, at Christmas / Father's Day), same look, the books sell each other. Humour-trivia books for men sit high in UK Trivia (Curious Press "The Book For Men Who Have Everything" #2) and US Sports Humour (Red Panda Press "The Golfer's Excuse Handbook" #6). Themed golf word searches exist but are plain and humourless. | One build phase: a word-search / grid block with an answer key, typeset by the renderer. Everything else (quizzes, tick-box panels, tables) already exists as `activity` blocks. 0 picture credits beyond the cover. | **Do first** |
| 2 | **Murder-mystery puzzle book** (a story told through word searches and logic puzzles; could be "Who Nicked Dave's Putter?") | The trend of the moment: Murdle (4m copies), Murdoku, and small publishers' "Kill Grid" (#1 US Word Search, #8 Logic) and "The Killer Never Checked In" (#12 / #16). Sells all year, not only as a gift. | Same puzzle block as #1, plus careful writing: every clue must be checkable, so Claude writes it and a small checker proves each puzzle has one answer. | **Do second** |
| 3 | **Kids' joke and "would you rather" books by age** ("Jokes for 8 Year Olds") | Text only. Small publishers own these lists: Lion and Mane Press at #3, #4 and #6 in UK Jokes & Riddles; "Would You Rather" for 6-12s at #6 UK Trivia (6,600 reviews); several in the US top 20. Birthday + Christmas gift. | Easy: text pages only. **Needs a separate pen name**: a clean kids' brand must never sit next to "Oh F*ck, That's Dave". | **Good third line** |
| 4 | **Large-print puzzles for older adults** (word search, sudoku) | Big steady volume and repeat buyers; small publishers at #5 and #7 in US Crosswords, #7 and #9 in US Word Search. But crowded, and it's a price fight on generic books. | Easy once the puzzle block exists; sudoku is a small generator. Crosswords with proper clues are hard - skip them. | Later, as a volume line |
| 5 | **Funny / sweary adult colouring book** in the Dave world | Real demand: Summersdale's sweary books at #17 and #24 UK, "Cutest Serial Killers" parody at #9 US. But the UK adult list is 19/20 big publishers (Coco Wyo via Penguin, Disney). | Hard for us now: 40-50 drawn pages, i.e. roughly 100+ Higgsfield credits with redraws (balance today: 6 credits), and AI line art is the #1 complaint in colouring reviews (broken lines, extra fingers). | Park until there is a credit budget |
| 6 | Kids' mazes / dot-to-dot | Small publishers own these (UK Mazes 12/20, UK Dot to Dot 17/20, #1 in both). | Mazes can be drawn by code; dot-to-dot needs drawn pictures. Another pen name. | Possible later |
| 7 | Kids' picture books, short stories, chapter books | **No** small or self-published title in the top 20 of UK or US kids' colouring, activity, Christmas, humour, chapter-book or short-story lists. The typical self-published picture book sells 200-500 copies in its life. Colour printing eats the royalty. | Hardest: 24-32 consistent colour pictures per book. | **Avoid for now** |
| 8 | Journals, planners, log books | Amazon counts these as "low-content": no free ISBN, no series, no expanded distribution. Saturated. | Easy, but weak. | Avoid |

## What the Amazon lists showed

Snapshot of 30 September 2026, top 20 of each list. "Small" means an
independent or self-published publisher (the "Independently published"
label, or a one-person imprint such as Red Panda Press or Lion and Mane
Press), not a traditional publisher.

| List | Small publishers in top 20 | Best small-publisher rank |
|---|---|---|
| UK Mandalas & patterns colouring | 18 | #1 |
| UK Kids dot to dot | 17 | #1 |
| US Party games (score pads, would-you-rather) | 17 | #1 |
| US Colouring for grown-ups | 13 | #1 |
| UK Kids mazes | 12 | #1 |
| US Word search | 12 | #1 |
| US Trivia | 11 | #6 |
| UK Trivia | 9 | #2 |
| UK Puzzles & quizzes | 8 | #6 |
| US Jokes & riddles | 8 | #3 |
| UK Brain teasers | 7 | #5 |
| US Crosswords | 7 | #5 |
| US Sudoku | 6 | #7 |
| UK Jokes & riddles (of 10 with a known publisher) | 5 | #3 |
| US Sports humour (of 11 known) | 3 | #3 |
| UK Crosswords | 2 | #3 |
| **UK Colouring for grown-ups** | **1** | #20 |
| **UK & US kids' colouring, activity, Christmas, humour, early learning, chapter books, short stories** | **0** | - |

Other things the lists say:

- **Murder-mystery puzzles are everywhere**: Murdoku, Murdle, "The Killer
  Isn't Alice", "Kill Grid", "CrimeSearch", "Murder Among the Stacks" all
  sit in the US word search and logic lists. Several are under a year old.
- **Humour activity books for adults sell big**: "Things To Do While You Poo
  On The Loo" (about 12,000 reviews) is in UK Jokes & Riddles.
- **Colouring = "cosy, bold and easy"**: Coco Wyo holds 10 of the UK top 12,
  after starting self-published and signing with Penguin (UK sales £1.3m in
  2025, The Bookseller). Bold-and-easy styles are about 40% of the top sellers.
- **Kids' lists are licensed characters** (Minecraft, Pokémon, Disney, Bluey)
  and big publishers. Hard to break into without a brand.
- **UK humour lists** (general, sports, parodies) are mostly memoirs, novels
  and celebrity books. The Dave books are best placed in the gift / trivia /
  "books for men" corner, not general humour.

## Money per copy

KDP paperback royalty = list price × 60% (50% under £7.99 / $9.99, since
June 2025) minus printing. Black-and-white printing is a flat £1.93 / $2.30
up to 110 pages (KDP's official rates).

| Book | UK price → you earn | US price → you earn |
|---|---|---|
| Dave gift book, 80 pp | £9.99 → **£4.06** | $9.99 → **$3.69** |
| Puzzle / quiz book, 110 pp | £7.99 → **£2.86** | $9.99 → **$3.69** |
| Same at £6.99 / $8.99 | £1.57 | $2.20 |
| Large-print word search, 200 pp | £8.99 → £2.54 | $9.99 → $2.59 |
| Colouring book, 100 pp, one side | £7.99 → £2.86 | $9.99 → $3.69 |
| Kids' picture book, 32 pp colour | £8.99 → £2.80 | $11.99 → $3.59 |

Lesson: keep puzzle books to **110 pages or fewer** and price at **£7.99 /
$9.99 or more**. Just under those prices you drop to 50% and lose about
£1.30 a copy.

## Rules and timing that matter

- **Only 2 new paperbacks a week.** Since 21 September 2026 KDP limits each
  account to 2 new titles per format per week (it was 10). Existing books and
  edits are not affected. This favours a few good books over many quick ones.
- **AI disclosure.** KDP must be told about AI-generated text or images
  (a private checkbox, not shown to buyers). Tightened April 2026; undisclosed
  books are being pulled. Claude-written copy and Higgsfield pictures both
  count, so tick it every time.
- **Puzzle and colouring books are not "low-content"** in KDP's rules, so they
  keep the free ISBN, series and Look Inside. Journals and planners don't.
- **Christmas.** Q4 can be 2-3× a normal month for gift books. KDP review
  runs 3-10 days in Q4, and a book needs time to get found. To catch this
  Christmas, a new book should be live by about **7 November**. One puzzle
  book is realistic; three are not.

## How sure we are

- One day's snapshot of the top 20. Rank shows what sells *now*, not how many
  copies; a Christmas list will look different.
- "Small publisher" was judged from the publisher name; a few imprints may be
  misfiled either way. The humour and kids' lists often had no publisher on
  the page (audiobook or Kindle listings), so those counts are smaller.
- UK prices in the CSV show in US dollars because the download ran from a
  US server.
- Web sources are industry figures (Circana, The Bookseller, Publishers
  Weekly, KDP help pages) plus self-publishing blogs; the blog numbers are
  claims, used only as background.

## Suggested next step

Plan one Book Factory phase to add a **puzzle page** (word search grid +
answer key, set as real type), then make **The Golf Addict's Puzzle Book**
as the pilot, aiming to be live before Christmas. If it sells, repeat for
Padel and Running, then try the murder-mystery book.

## Sources

- Amazon.co.uk and Amazon.com bestseller lists, 42 lists, fetched 2026-09-30 (see CSV)
- [KDP: Paperback printing cost](https://kdp.amazon.com/en_US/help/topic/G201834340)
- [KDP: Low-content books](https://kdp.amazon.com/en_US/help/topic/GGE5T76TWKA85DJM)
- [KDP: Content guidelines](https://kdp.amazon.com/en_US/help/topic/G200672390)
- [Publishers Lunch: KDP limits authors to two new titles a week](https://lunch.publishersmarketplace.com/2026/09/kdp-limits-authors-to-two-new-titles-a-week/)
- [Jane Friedman: KDP cuts royalty for print books under $9.99](https://janefriedman.com/amazon-kdp-decreases-royalty-rates-for-print-books-priced-under-9-99/)
- [Circana: 2026 book market trends](https://www.circana.com/post/turning-the-page-on-2026-book-trends)
- [Publishers Weekly: print sales, first half 2025](https://www.publishersweekly.com/pw/by-topic/industry-news/financial-reporting/article/98147-print-book-sales-slipped-in-first-half-of-2025.html)
- [The Bookseller: Coco Wyo bucks the trend](https://www.thebookseller.com/bestsellers/going-loco-for-coco-coco-wyo-bucks-the-trend-in-handicrafts)
- [Book Riot: bold and cosy colouring](https://bookriot.com/bold-and-cozy-coloring-coco-wyo-controversies/)
- [bookillustrationai.com: why bold and easy dominates](https://bookillustrationai.com/blog/bold-and-easy-coloring-books-amazon-kdp)
- [The Cool Down: AI colouring book complaints](https://www.thecooldown.com/green-home/reddit-coloring-books-ai-art-print/)
- [KDP Builder: AI disclosure rules 2026](https://kdpbuilder.com/blog/kdp-ai-disclosure-rules)
- [Neolemon: what children's books earn on KDP](https://www.neolemon.com/blog/how-much-can-you-make-selling-childrens-books-on-amazon-kdp/)
- [Murdle series (Amazon)](https://www.amazon.com/Murdle/dp/B0CJCHFGTH)
- [Book Bolt: seasonality in KDP books](https://bookbolt.io/seasonality-in-no-content-and-low-content-kdp-books/)
- [BookBaby: holiday publishing timeline](https://blog.bookbaby.com/how-to-self-publish/self-publishing/publishing-timeline-for-holiday-book-sales)
