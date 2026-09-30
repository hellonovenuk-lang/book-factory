"""Snapshot Amazon UK and US book bestseller lists into one CSV.

Research helper for choosing the next book (see
.claude/skills/nightly-book-research). Read-only: it fetches public
bestseller pages and product pages, and writes a CSV. For each list it
records rank, title, price, reviews and, for the top N, publisher, page
count and publication date, and whether the publisher looks like a small
or self-publisher rather than a traditional house.

    python3 scripts/research/amazon_bestsellers.py --out <file.csv> [--top 20]
        [--list uk:4455:"Word search" ...] [--cache <dir>]

Amazon's search pages block scripts; the bestseller pages and product
pages do not (checked 2026-09-30). Prices on the UK store show in US
dollars when fetched from a US server.
"""
import argparse
import concurrent.futures
import csv
import hashlib
import html
import os
import re
import subprocess
import tempfile
import time

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126 Safari/537.36")
HOSTS = {"uk": "www.amazon.co.uk", "us": "www.amazon.com"}

# market, browse node, name. Find more nodes with --children <market>:<node>.
DEFAULT_LISTS = [
    ("uk", "266870", "Colouring for grown-ups"), ("uk", "10525967031", "Mandalas & patterns"),
    ("uk", "15511942031", "Kids colouring"), ("uk", "492672", "Kids activity books"),
    ("uk", "15511945031", "Kids dot to dot"), ("uk", "15511947031", "Kids mazes"),
    ("uk", "270496", "Puzzles & quizzes"), ("uk", "270498", "Crosswords"),
    ("uk", "270497", "Brain teasers"), ("uk", "270506", "Quiz questions"),
    ("uk", "270507", "Trivia"), ("uk", "274131", "Jokes & riddles"),
    ("uk", "274134", "Humour: love, sex & marriage"), ("uk", "274143", "Humour: sports"),
    ("uk", "274135", "Humour: parodies"), ("uk", "274128", "Humour: general"),
    ("uk", "274122", "Children's humour"), ("uk", "530094", "Kids Christmas"),
    ("uk", "15512201031", "Kids chapter books & readers"), ("uk", "3372661", "Kids early learning"),
    ("uk", "291757", "Kids short story collections"),
    ("us", "11357541011", "Coloring for grown-ups"), ("us", "4455", "Word search"),
    ("us", "15756641", "Sudoku"), ("us", "4416", "Crosswords"),
    ("us", "4436", "Logic & brain teasers"), ("us", "4439", "Puzzles"),
    ("us", "4452", "Trivia"), ("us", "119235586011", "Party games"),
    ("us", "4469", "Jokes & riddles"), ("us", "4472", "Humor: love, sex & marriage"),
    ("us", "4481", "Humor: sports"), ("us", "4473", "Humor: parodies"),
    ("us", "761128", "Humor: parenting & families"), ("us", "3373", "Kids activity books"),
    ("us", "3374", "Kids coloring"), ("us", "3003", "Kids humor"),
    ("us", "3072", "Kids Christmas"), ("us", "3564979011", "Kids chapter books & readers"),
    ("us", "3019", "Kids short story collections"), ("us", "7009080011", "Kids early learning"),
]

# Traditional publishers and their imprints seen on these lists. Anything
# else with a known publisher counts as small / self-published.
BIG = """penguin puffin harper macmillan collins bantam griffin little,-brown walker egmont
ebury sphere simon-&-schuster studio-press hachette farshore summersdale publications-interna
cottage-door times-books cassell chronicle dutton adams-media buster national-geographic
miles-kelly phoenix expanse cider-mill authors-equity usborne scholastic igloo dorling
bloomsbury hodder andrews-mcmeel workman sourcebooks ulysses rockridge callisto zeitgeist
sparkpool random-house quarto o'mara arcturus carlton welbeck octopus ladybird nosy-crow
little-tiger make-believe priddy autumn bonnier templar candlewick golden dover thunder-bay
parragon highlights school-zone kumon wiley rodale hay-house orion headline transworld
hutchinson lomic richardson hamlyn kingfisher oxford letts cgp bbc hardie-grant running-press
rp-minis union-square heinemann faber quercus pavilion hinkler skittledog hrp-house viz
kodansha yen seven-seas harlequin avon sterling peter-pauper carson-dellosa evan-moor
spectrum houghton hmh century souvenir gallery-books clarion cartwheel warne andersen
dc-thomson ivy-press guinness dey-street crown da-capo fourth-estate john-murray magpie
akashic harvest merriam puzzlewright walter-foster kaplan dummies david-&-charles arcade
campbell alison-green imagine-that phidal zonderkidz arcadia applesauce dino-books eight15
raleigh william-morrow""".split()
BIG = [b.replace("-", " ") for b in BIG]


def is_small(publisher):
    p = (publisher or "").lower()
    return bool(p) and not any(b in p for b in BIG)


class Fetcher:
    def __init__(self, cache):
        self.cache = cache
        os.makedirs(cache, exist_ok=True)

    def get(self, url):
        fn = os.path.join(self.cache, hashlib.md5(url.encode()).hexdigest())
        for attempt in range(3):
            if os.path.exists(fn) and os.path.getsize(fn) > 5000:
                break
            subprocess.run(["curl", "--compressed", "-sS", "-m", "25", "-A", UA,
                            "-H", "Accept-Language: en-GB,en;q=0.9", "-o", fn, url],
                           capture_output=True)
            time.sleep(1.2 + attempt * 3)
        if not os.path.exists(fn):
            return ""
        with open(fn, encoding="utf-8", errors="ignore") as f:
            return f.read()


def children(fetch, market, node):
    s = fetch.get(f"https://{HOSTS[market]}/gp/bestsellers/books/{node}")
    return [(n, html.unescape(t)) for n, t in
            re.findall(r'zgbs/books/(\d+)/ref=zg_bs_nav_books_\d+[^"]*">([^<]+)<', s)]


def list_items(fetch, market, node):
    s = fetch.get(f"https://{HOSTS[market]}/gp/bestsellers/books/{node}?pg=1")
    out = []
    for b in re.split(r'id="gridItemRoot"', s)[1:]:
        rank = re.search(r'zg-bdg-text">#(\d+)<', b)
        asin = re.search(r"/dp/([A-Z0-9]{10})", b)
        clamp = [html.unescape(x) for x in re.findall(r'line-clamp-\d_[A-Za-z0-9]+">([^<]*)<', b)]
        fmt = re.search(r'a-text-normal">([A-Za-z ]+)</span>', b)
        price = re.search(r'p13n-sc-price_[A-Za-z0-9]+">([^<]+)<', b)
        rev = re.search(r'([\d.]+) out of 5 stars[^<]*</span>.*?a-size-small">([\d,]+)<', b, re.S)
        out.append(dict(rank=int(rank.group(1)) if rank else None, asin=asin and asin.group(1),
                        title=clamp[0] if clamp else "", author=clamp[1] if len(clamp) > 1 else "",
                        fmt=fmt and fmt.group(1), price=price and price.group(1),
                        stars=rev and rev.group(1),
                        reviews=rev and int(rev.group(2).replace(",", ""))))
    return out


def product(fetch, market, asin):
    s = fetch.get(f"https://{HOSTS[market]}/dp/{asin}")
    t = re.sub(r"<script.*?</script>|<style.*?</style>", "", s, flags=re.S)
    t = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", t)))
    pub = re.search(r"Publisher\s*‏?\s*:\s*‎?\s*([^:]{2,60}?)\s+(?:Publication date|Language|\()", t)
    pages = re.search(r"Print length\s*‏?\s*:?\s*‎?\s*(\d+) pages", t)
    date = re.search(r"Publication date\s*‏?\s*:\s*‎?\s*([0-9A-Za-z .,]+?\d{4})", t)
    return dict(publisher=pub and pub.group(1).strip(), pages=pages and pages.group(1),
                date=date and date.group(1))


def crawl_list(fetch, market, node, name, top):
    items = list_items(fetch, market, node)
    for it in items[:top]:
        if it["asin"]:
            it.update(product(fetch, market, it["asin"]))
    return market, name, items


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", help="CSV file to write")
    ap.add_argument("--top", type=int, default=20, help="product-page lookups per list")
    ap.add_argument("--list", action="append", default=[],
                    help='extra list as market:node:name, e.g. us:4455:"Word search"')
    ap.add_argument("--only", action="store_true", help="use only the --list lists")
    ap.add_argument("--children", help="print sub-lists of market:node (node may be empty)")
    ap.add_argument("--cache", default=os.path.join(tempfile.gettempdir(), "amazon-bestsellers-cache"))
    ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args()
    fetch = Fetcher(a.cache)
    if a.children is not None:
        market, _, node = a.children.partition(":")
        for n, t in children(fetch, market, node):
            print(n, t)
        return
    lists = [] if a.only else list(DEFAULT_LISTS)
    for spec in a.list:
        market, node, name = spec.split(":", 2)
        lists.append((market, node, name))
    if not a.out:
        ap.error("--out is required")
    rows = []
    with concurrent.futures.ThreadPoolExecutor(a.workers) as ex:
        futs = [ex.submit(crawl_list, fetch, m, n, name, a.top) for m, n, name in lists]
        for f in concurrent.futures.as_completed(futs):
            market, name, items = f.result()
            print(f"{market} {name}: {len(items)} titles", flush=True)
            for i in items:
                p = i.get("publisher")
                rows.append([market.upper(), name, i["rank"], i["title"], i["author"], i["fmt"],
                             p or "", "" if not p else ("yes" if is_small(p) else "no"),
                             i["price"], i["stars"], i["reviews"], i.get("pages") or "",
                             i.get("date") or "", i["asin"]])
    rows.sort(key=lambda r: (r[0], r[1], r[2] or 999))
    with open(a.out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["market", "list", "rank", "title", "author", "format", "publisher",
                    "small_or_self_published", "price_shown", "stars", "reviews", "pages",
                    "publication_date", "asin"])
        w.writerows(rows)
    print(f"wrote {len(rows)} rows to {a.out}")


if __name__ == "__main__":
    main()
