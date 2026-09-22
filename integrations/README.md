# Integrations

Book Factory does not depend on any AI vendor. The core is a Python library and
a CLI; the files in here are **operator instructions for a particular assistant**,
nothing more.

| File | Use it when |
| --- | --- |
| `chatgpt/BOOK_FACTORY.md` | Using ChatGPT - the normal production operator - for any task, visual or written. |
| `chatgpt/AUTONOMOUS_PRODUCTION.md` | ChatGPT running a whole book end to end: intake, production policy, when to keep going. |
| `claude/BOOK_FACTORY.md` | Using Claude Code, which builds and maintains Book Factory itself. |

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
ChatGPT              reads state, drives the book task by task: writes,
                     generates artwork, submits drafts, and keeps going
                     wherever the recorded production policy allows
You                  choose the production policy (at intake, or
                     `create --policy`; change it with `policy set`);
                     approve or reject wherever the policy keeps a
                     checkpoint (every approval if checkpointed)
Book Factory         locks approved work, continues production
```

Any of those agents can be swapped out. None of them holds state.
