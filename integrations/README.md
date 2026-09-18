# Integrations

Book Factory does not depend on any AI vendor. The core is a Python library and
a CLI; the files in here are **operator instructions for a particular assistant**,
nothing more.

| File | Use it when |
| --- | --- |
| `chatgpt/BOOK_FACTORY.md` | Using ChatGPT, mainly for artwork and art direction. |
| `claude/BOOK_FACTORY.md` | Using Claude Code or Claude in a repository. |

**No business logic lives in these files.** Every rule they describe is enforced
by the system itself - if an adapter disappeared tomorrow, nothing about how the
system behaves would change. That is deliberate: rules an agent can forget are
not rules.

The shared, vendor-neutral rules are in `../AGENTS.md`. These files add only
what is specific to how that assistant is used in practice.

## How the pieces fit

```
Claude Code          builds and maintains Book Factory
Book Factory         holds canonical state, enforces the rules
ChatGPT              reads state, takes visual tasks, generates artwork,
                     submits drafts, hands control back
You                  approve or reject
Book Factory         locks approved work, continues production
```

Any of those agents can be swapped out. None of them holds state.
