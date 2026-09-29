# Memory model

## Observation → Memory
An **observation** is one sentence-level candidate extracted from a session, with `category`, `score`, `files`, `source` (observed | explicit), author, hashed session id and commit. Observations are sanitized before they are written and are append-only JSONL under `.cosmos/observations/`.

A **memory** is a consolidated fact in `.cosmos/ledger/<category>/<id>-<slug>.md`. The id is `mem_` + sha1(text)[:8].

## Statuses
| status | meaning | who changes it |
|---|---|---|
| active | believed true | dream (new / merged / revived), `verify` |
| contradicted | conflicts with another active fact; needs a human | dream |
| stale-candidate | evidence files missing or not re-observed within the category limit | dream |
| superseded | replaced by a newer fact; kept as history with `superseded_by` | dream (evidence-based), `verify --resolve` |
| forgotten | retired by a developer | `forget` |

Retrieval and CLAUDE.md never surface `superseded` or `forgotten`.

## Hierarchy
explicit developer rule (`remember:` / `cosmos remember`) > consolidated memory > observed > inferred by LLM.
An explicit rule supersedes a conflicting inferred fact automatically; the reverse never happens.

## Time
All dates are absolute ISO dates. `created`, `updated`, `last_verified`. Staleness limits (days) per category live in `config.json → dream.staleness_days`.

## Confidence
Starts at 0.45 + 0.4·score for observed facts (0.9 explicit); +0.05 per re-observation, +0.1 on `verify`; capped at 0.98/0.99.

## Freshness

A dream doubts a fact (status `stale-candidate`, shown on Verdicts, never handed to an agent) when none of its evidence
files exist any more, or when an identifier it names is gone from its evidence files and from the rest of the code
(the ledger itself is not searched: a fact cannot confirm itself). A file that was renamed or moved is followed through
git's rename history and the fact points at the new path. When the evidence returns, the doubt is lifted by itself; a
search that fails never counts as absence. Doubts the evidence cannot settle go to the model, then to a person.

## Where the ledger lives

`.cosmos/` is ordinary committed files in the branch where `cosmos init` ran, so every branch made from it carries the
team memory and merging a branch shares what was learned on it. cosmos commits `.cosmos/` to the checked-out branch every
10 minutes while you work and after each dream, with a commit that holds only `.cosmos/` (whatever you have staged stays
staged). While that commit is the branch tip and not pushed yet it is amended, so a working session leaves one cosmos
commit, not dozens. It never commits during a merge, rebase, cherry-pick or on a detached HEAD, and it never pushes: the
memory goes out when you push the branch. `.cosmos/state/` (read positions, live view, logs) stays on the machine.
`.cosmos/.gitattributes` merges the append-only files (journal, log, observations) by union, so two branches that both
recorded work do not conflict there; a fact two branches changed differently conflicts like code and the next dream
reconciles whatever you keep. `sync.commit: false` in `.cosmos/config.json` turns the automatic commits off.

**Opt-in: a separate branch.** `cosmos init --branch` keeps the ledger on its own `cosmos` branch instead (a worktree at
`.cosmos/`, pushed by itself, ignored by code branches). `cosmos sync --inline` moves it back into the checked-out branch.

## Several writers at once

Dreams, the watcher, the console, MCP servers and CLI commands in several sessions all write the same ledger. Each note
remembers what it was when a process read it, and a save is three-way: a note this process did not change is never
written over a newer file, and a note both changed keeps this process's fields (key by key inside `meta`) and the
file's for everything else. A dream that ran for minutes therefore cannot put a flare that another session moved to
`pr_open` back to `open`. Files merge by union in git for the append-only parts; a note edited on two branches is
reconciled by the next dream.

## Evidence that moved

A dream follows git's renames for a fact whose files are gone. `cosmos review --repoint` does it for every stale fact
at once, including ones flagged before the rename was followed: it prints what it would change, and with `--yes` brings
a fact back only when its files exist again and every identifier it names is still in the code. Doubts about age are
never cleared this way.
