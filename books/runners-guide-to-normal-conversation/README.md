# The Runner’s Guide to Normal Conversation

Book Factory project `runners-guide-to-normal-conversation`.

**This directory is the source of truth for this book.** Not a chat log, not a
Drive folder, not somebody's Downloads.

## Where things live

| Path | What it is |
| ---- | ---------- |
| `book.json` | Project dashboard. Stage, locks, versions, next action. Read this first. |
| `audit.jsonl` | Append-only history of meaningful events. |
| `brief/` | What the book is and who buys it. |
| `manuscript/` | Outline, writing sample, manuscript, locked version snapshots. |
| `style/` | Voice bible, visual bible, design tokens, locked visual references. |
| `pages/manifest.json` | **The page manifest.** The authoritative list of pages. |
| `pages/specs/` | One spec per page. Exact copy and illustration brief. |
| `pages/drafts/` | Candidate page renders. Cheap, plentiful, never deleted. |
| `pages/approved/` | Approved pages. Immutable. Assembly reads only these. |
| `assets/drafts/` | Candidate artwork. |
| `assets/approved/` | Approved artwork. Immutable. |
| `tasks/` | Open and completed production tasks. |
| `qa/` | QA reports. |
| `output/` | Assembled PDFs and review material. Regenerable; not canonical. |

## How to continue this book

```bash
bookfactory status runners-guide-to-normal-conversation
bookfactory next runners-guide-to-normal-conversation
```

`next` tells you exactly what to do. You do not need to remember anything.
