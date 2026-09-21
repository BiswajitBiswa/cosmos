# Lanes and Intake

## Lanes — memory organised the way the team thinks
Every fact, finding and diagram carries a **lane**: the feature or module it belongs to, inferred from the files it anchors to. Configure explicit lanes in `.cosmos/config.json`:

```json
{ "lanes": { "payments": ["src/payments/**"], "billing": ["webserver/app/api/v1/endpoints/billing.py", "core/services/billing*"] } }
```

Without configuration the lane is deliberately **coarse**: the top-level app or package a file lives in (skipping `src`, `app`, `lib`, …). `docs/`, `references/` → `docs`; `.claude/`, `.github/`, `scripts/`, `infra/` → `tooling`; files in a sibling repository → `../<that-repo>`; files outside the repository tree are never evidence. Partial locations in an audit (`crud/base.py`) are resolved against the tree so they land in the right package. Findings with no resolvable file fall back to their audit `area`.

Lanes are not LLM-derived by default. `cosmos lanes --propose` prints a suggested mapping — from paths, or, when `llm.provider` is configured, from the model grouping the files into product-shaped lanes (every glob is validated against real paths). `--write` saves it to `config.json → lanes` and re-files every memory. The `/atlas` deep pass also proposes lanes.

`cosmos lanes` (and the Lanes page) shows, per lane: facts, open findings, and the people who produced observations there in the last 30 days. Two or more people in one lane is flagged as **overlap** — visible before it becomes a merge conflict. The ledger index and CLAUDE.md are grouped by lane.

## Intake — a feature enters with a map
```bash
cosmos intake "bulk invite with partial success" -f webserver/app/api/v1/endpoints/team_members.py
```

Before any code is written, cosmos answers from the ledger and observations already in the repo:

- **Lanes touched**, with an overlap warning where two people are already active
- **Collides with** — recorded decisions, constraints and conventions that this feature must respect or consciously change
- **Open findings in the way** on those lanes and files
- **Who has been here** in the last 30 days, and a suggested owner
- **Related facts**

The result is saved as `.cosmos/ledger/intake/<date>-<slug>.md` — reviewable in the PR that implements the feature — and listed on the Intake page, where a request can also be typed directly.
