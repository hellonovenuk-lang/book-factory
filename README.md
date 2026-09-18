# Book Factory

Book Factory is a production system for illustrated humour and gift books.

You give it a book idea. It walks the book through concept, writing, visual
identity, page planning, illustration, layout, approval, quality checks,
assembly and Amazon KDP preflight - and it remembers everything, so you never
have to.

It is built for one particular job: making 60 to 120 page illustrated humour
books, with recurring characters and visual jokes, over and over, and making
book number ten far easier than book number one.

## The one idea that matters

**The repository is the source of truth. The conversation never is.**

Every decision, every approved page, every locked style rule lives in files on
disk. That means you can close a chat, open a completely new one - with Claude,
with ChatGPT, with anybody - and say:

> Continue Book Factory project golf-addict.

The agent runs two commands, reads the answers, and knows exactly where the
book stands and what to do next. You never have to explain the previous fifty
conversations again.

```
bookfactory status golf-addict
bookfactory next golf-addict
```

## What it stops going wrong

Book Factory exists because a complete illustrated golf book was produced by
hand through chat, and the result showed the work was good but the process was
not. These are the failures it prevents, structurally rather than by asking an
agent to be careful:

| What went wrong | What stops it now |
| --- | --- |
| The character's face changed halfway through the book | Nothing is drawn until a reference set is approved and locked. Every later illustration task points at those exact files. |
| Chapter headings and layouts drifted | Headings, page numbers and layout are set by a deterministic renderer from a design token file, not drawn and not retyped. |
| Approved artwork got regenerated to fix a typo | Approved files are read-only, checksummed, and cannot be replaced without an explicit revision. |
| Generated type contained spelling mistakes | Image generation never renders words. Ever. All text is typeset. |
| Page numbers went wrong | Page numbers come from the page manifest. |
| Nobody could say which file was page 58 | The page manifest says, with a checksum. |
| "Did you approve this?" "I think so?" | Approval is an explicit command that writes a record. Silence approves nothing. |
| The chat became the project | The repository is the project. |

## Getting started

```bash
pip install -e .          # or: pip install -r requirements.txt
bookfactory doctor        # check this machine can render and assemble
```

Then start a book:

```bash
bookfactory create "Golf Addict" --pages 90
bookfactory next golf-addict
```

`next` will always tell you the one thing to do. Do it, run `next` again.
That is the whole operating loop.

There is a complete worked example in `books/demo-book/` - a small synthetic
book, taken all the way from idea to assembled interior PDF. It is deliberately
left with one open illustration task, so you can hand the repository to a fresh
ChatGPT session and watch a real piece of artwork come back through the proper
route. The book stays assembled and valid while that task is open.

Rebuild it from nothing at any time with:

```bash
python scripts/build_demo_book.py
```

## The commands you will actually use

| Command | What it does |
| --- | --- |
| `bookfactory status <book>` | Where the book stands. |
| `bookfactory next <book>` | The single next action. |
| `bookfactory approve <book> <id>` | Approve a page or a piece of artwork. |
| `bookfactory reject <book> <id> --reason "..."` | Reject it. The file is kept. |
| `bookfactory revise <book> <id>` | Change something already approved, properly. |
| `bookfactory review <book>` | Contact sheet and review PDFs of the whole book. |
| `bookfactory qa <book>` | Run the quality checks. |
| `bookfactory assemble <book>` | Build the interior PDF. |
| `bookfactory preflight <book>` | Check it against the KDP rules. |

Every command takes `--json` for agents. `bookfactory --help` lists the rest.

## The rules the system enforces for you

1. **No mass page production before the visual style is locked.** This is the
   expensive mistake. The system refuses.
2. **Approved means immutable.** Changing approved work requires
   `bookfactory revise`, which keeps the old version and demands a fresh
   approval.
3. **Image generation draws pictures. It never sets type.** Headings, captions,
   page numbers, tables, quiz copy and contents pages are typeset from the page
   spec.
4. **Assembly is mechanical.** It reads approved files, verifies checksums, and
   concatenates them. It cannot generate, rewrite or reinterpret anything, and
   it fails loudly rather than using the nearest available file.
5. **Nothing is approved by silence.**

## Where to read next

| File | Who it is for |
| --- | --- |
| `docs/OPERATOR.md` | You. A full walkthrough of making a book, start to finish. |
| `SYSTEM.md` | How the system is built, for a developer. |
| `AGENTS.md` | The rules every AI agent must follow. Vendor-neutral. |
| `integrations/chatgpt/BOOK_FACTORY.md` | Paste into ChatGPT when using it for artwork. |
| `integrations/claude/BOOK_FACTORY.md` | For Claude sessions. |
| `docs/RENDERING.md` | How pages are rendered, and how to debug a layout. |

## Requirements

Python 3.10 or newer, and one HTML-to-PDF backend. WeasyPrint is installed with
the package and is the default. Chromium is used automatically if present.
`bookfactory doctor` tells you what it found.
