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
