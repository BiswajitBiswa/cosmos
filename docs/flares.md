# Flares: audit findings as memory

`cosmos flares` turns QA / security audit findings into first-class memory. A finding is durable engineering
knowledge with a lifecycle — it should follow the code, show up when someone touches the affected files, and
never be re-filed once the team has decided it is by design.

## Model
One finding = one note in `.cosmos/ledger/finding/`, category `finding`, with:

| field | meaning |
|---|---|
| `meta_audit_id` | stable id, e.g. `QA-11` (prefix + the auditor's id) |
| `meta_severity` | critical · high · medium · low · info |
| `meta_finding_status` | open → claimed → pr_open → fixed \| needs_human \| withdrawn \| wontfix, plus **regressed** |
| `meta_area`, `meta_locations` | grouping and the `file:line` anchors (also parsed into `files` for retrieval) |
| `meta_found_commit`, `meta_fixed_commit` | HEAD when imported / when marked fixed |
| Details block | the auditor's labelled sections (What · Impact · Repro · Fix …) |

Status precedence on import: an exported non-open status (written by a human or by the session-driven fix loop) is taken
verbatim — never coerced; an incoming `open` never downgrades a local `claimed` / `pr_open` / `needs_human` / `withdrawn`;
`fixed`/`wontfix` + incoming `open` = **regressed**. `needs_human` is where could-not-reproduce and ambiguous-intent
findings go instead of a PR. "Open-like" (open, claimed, pr_open, needs_human, regressed) is what reports, retrieval and
Slack publishing consider still-active.

Rules: **withdrawn is a state, never a deletion** (the note stays so nobody re-files it, but it leaves retrieval and CLAUDE.md).
Flares never go stale by age — they are closed explicitly — but a finding whose evidence files disappear becomes a `stale-candidate` like any other fact.
A finding that was `fixed`/`wontfix` and is imported again as open is flagged **regressed**.

## Input format
The JSON a Claude audit session already produces:

```json
[{"id": "11", "severity": "critical", "title": "…", "area": "Verdicts",
  "locations": "`services/pipeline_stage.py:352` · `stage_service.py:1076`",
  "sections": [["What", "…"], ["Impact", "…"], ["Fix", "…"]]}]
```

## Bugs found by hand

A bug you or a teammate found by hand, with no audit session behind it, is recorded the same way. There are three entry points, and every one gives each bug the current prefix:

- **Console:** **＋ Record bugs** on the Flares page. Type or paste one bug per line, or choose a file.
- **Command line:** `cosmos flares add "high: Login fails on Safari @ web/login.js:42" --fix "…"`.
- **A list:** `cosmos flares add --from bugs.txt` (also `.csv`, `.tsv`, `.xlsx`, `.json`, or `-` for stdin).

| input | how it is read |
|---|---|
| a line | An optional leading severity (`critical` `high` `medium` `low` `note`, or `blocker` `major` `minor` `P0`–`P3`), the title, then an optional ` @ path:line`. Lines under 8 characters and `#` comments are skipped. |
| rows pasted from a sheet | Tab-separated. With a header row, the columns are found by name; without one, they are taken as title, severity, location, what, impact, fix, area. |
| `.csv` / `.tsv` / `.xlsx` | The header row is read by name: title (or bug, summary, issue), severity (or priority), location (or where, file), what (or description, steps), impact, fix, area (or lane, module), status, id. An `.xlsx` is read with the standard library, first sheet only. |

**Updates instead of duplicates:**

- The same title recorded again updates that flare.
- A row whose `id` matches a flare updates it, so `cosmos flares export -o flares.xlsx` can be edited and read back.
- A status in the sheet moves the flare. Common words are understood: `done` and `resolved` mean fixed, `in progress` means claimed, `won't fix` means wontfix, `not a bug` means withdrawn.
- An old export that still says `open` reopens nothing. Write `reopen` to reopen a closed flare.
- A list that names no severity keeps the one the flare already has.

## Ids and the prefix

A flare's id is `<PREFIX>-<raw id>`, and the prefix is where the project is in its life when the flare is filed, read
from git. Nothing to run and nothing to choose: every flare filed now (from a session with `cosmos_flare` or
`flare: …`, by an import, or named by a dream) takes the current stage, and keeps it after the project moves on.

| stage | when |
|---|---|
| `QA` | branch `qa/*`, `qa-*`, `test/*`, `testing` |
| `UAT` | branch `uat/*`, `uat`, `staging`, `stage` |
| `RC` | branch `release/*`, `release-*`, `rc/*`, or HEAD has an `-rc` / `-beta` / `-alpha` tag |
| `HOTFIX` | branch `hotfix/*`, `hotfix-*` |
| `PROD` | `main` / `master` / `trunk` once a version tag (`v1.2.0`, `1.2`) is reachable from HEAD |
| `DEV` | any other branch, or nothing released yet |

`cosmos flares stage` prints the prefix a new flare gets here and why. In `.cosmos/config.json`:

- `flares.stages` — your own branch patterns, checked first: `{"develop": "DEV", "preprod/*": "UAT"}`
- `flares.stage` — pin the stage for every branch (a project that is "in QA" whatever the branch)
- `flares.project` — a project tag before the stage: `RET-QA-11`
- `flares.prefix` — one prefix for every flare, lifecycle off (explicit outranks inferred; older versions of cosmos
  wrote it on `import --prefix`, remove it to follow the lifecycle)

`cosmos flares import --prefix PENTEST` names that one import. A finding that is already in the ledger keeps its id when
it is imported or filed again under a later stage (same source and raw id), so a re-import is an update, and a fixed
finding reported again is a regression, never a duplicate. A finding the model writes while reading a session gets an id
with the current prefix and is a note (no lifecycle) unless it states a severity.
`cosmos flares import` on a file that does not exist asks before creating an empty one to fill in (`--yes` skips the
question).

## Commands
```bash
cosmos flares import docs/qa-findings.json --source qa-flares.md
cosmos flares add "high: Login fails on Safari @ web/login.js:42" --what "…" --fix "…"   # one bug found by hand
cosmos flares add --from bugs.csv                                    # a list: .txt .md .csv .tsv .xlsx .json, or - for stdin
cosmos flares list [--status open|fixed|withdrawn|wontfix|regressed] [--severity critical] [--json]
cosmos flares show QA-11
cosmos flares fix QA-12 "org_id__eq → org_id, PR #<n>"      # records HEAD as fixed_commit
cosmos flares withdraw QA-8 "companies is shared reference data by design"
cosmos flares wontfix QA-6 | cosmos flares reopen QA-6
cosmos flares claim QA-1 | cosmos flares pr-open QA-1 | cosmos flares needs-human QA-17 "intent unclear"
cosmos flares set QA-1 pr_open "PR #<n>"
cosmos flares claimed QA-1 | cosmos flares fixed QA-1 …                # each status's own name works too (except open: use reopen)
cosmos flares fix QA-12 "PR #<n>" --commit 862f73c --branch qa/fixes   # the fix lives in another worktree
cosmos flares edit QA-12 --title "…" --severity high --locations "api/x.py:42"   # correct a flare; its id stays
cosmos flares stage                                            # the prefix a new flare gets here, and why
cosmos flares export -o docs/qa-findings.json                  # same schema back out
cosmos flares export -o flares.xlsx                            # an Excel sheet: id, severity, status, title, locations, what / impact / fix, commits, dates
cosmos export -o team.xlsx                                     # flares, facts, rules, lanes, endpoints, playbooks — one sheet each
cosmos flares report --format md -o docs/qa-flares.md           # regenerated from the ledger
cosmos flares report --format slack                            # parent + threaded replies as JSON
```

## Publishing to Slack
```bash
cosmos flares slack                      # dry run: preview cards for open findings not yet posted
cosmos flares slack --validate           # blocks.validate every card (no token needed)
export SLACK_BOT_TOKEN=xoxb-…             # scopes: chat:write, reactions:write — env only, never stored
cosmos flares slack --send --channel C0123456
cosmos flares slack --status             # posted vs pending
cosmos flares slack --seed-state docs/.slack-posted.json --prefix QA   # migrate from the legacy poster
```

```bash
cosmos flares slack --convert --dry --channel C0123456                 # rewrite already-posted plain-text messages as cards
cosmos flares slack --convert --only QA-12 --ts <permalink> --channel C0123456   # one message, needs only chat:write
```

Each open finding becomes one top-level Block Kit card: header **containing the title** (`🔴 CRITICAL · QA-11 — …`),
a fields row (Severity · Ref · Area · Status · Location), a divider, one section per labelled paragraph, the ack legend, and a
**trailing divider** — Slack groups consecutive same-app messages, and without it cards bleed into each other. Cards are
pre-seeded with 👀 / ✅ / 🚫 reactions, so acking is one click and each bug can be
discussed in its own thread. Already-posted ids are tracked in `.cosmos/state/slack-posted.json` (gitignored);
re-running never duplicates a post. `--all` forces a repost.

## Lint: filter keys that are not columns
```bash
cosmos flares lint --repo-base core.crud.base:BaseRepository \
  --crud-glob 'core/crud/*.py' --module-prefix core.crud. \
  --roots webserver/app core processor/app --sys-path .
```
Or set the same keys under `audit.lint` in `.cosmos/config.json`. Walks every `repo.list/get/update/update_many/delete/count/upsert({...})`
call, resolves the repository singleton to its model, and flags literal filter keys that are not columns (silently dropped by
`apply_filters`-style helpers) and operator suffixes passed to methods that take plain column names (`update_many`). This class of bug
produced two real findings. Limits: literal dict keys at the call site only; the target project's dependencies must be importable.

## In the loop with Claude Code
- Typing `flare: …` in a session captures an explicit finding observation; `cosmos dream` turns it into a note.
- `UserPromptSubmit` retrieval ranks findings by the files they anchor to, so a prompt like *"refactor pipeline_stage.py"* surfaces `QA-11` before the edit happens.
- Open findings appear in the CLAUDE.md / AGENTS.md managed block like any other high-importance fact.

## QA playbooks

A team's own QA protocol (for example `docs/qa/MASTER_QA_PROTOCOL.md`) is found by itself: a markdown file named
*protocol* / *playbook* / *runbook* / *master prompt*, written for an agent. It becomes a command for every agent
(`/master-qa-protocol`), and `/qa` reads it first and follows it. Another project that wants the same protocol runs
`cosmos playbooks add <path to it>`, which copies it into `.cosmos/playbooks/` (committed) to adapt; a project with none
runs `cosmos playbooks add qa` for a generic one (safety rules, discovery, the loop with flares and a resumable state
file, stop rules, severity, areas). `cosmos playbooks` lists what was found; `playbooks.ignore` and `playbooks.paths` in
`.cosmos/config.json` correct the detection.
