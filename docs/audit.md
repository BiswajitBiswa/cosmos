# Audit findings as memory

`cosmos audit` turns QA / security audit findings into first-class memory. A finding is durable engineering
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
Findings never go stale by age — they are closed explicitly — but a finding whose evidence files disappear becomes a `stale-candidate` like any other fact.
A finding that was `fixed`/`wontfix` and is imported again as open is flagged **regressed**.

## Input format
The JSON a Claude audit session already produces:

```json
[{"id": "11", "severity": "critical", "title": "…", "area": "Verdicts",
  "locations": "`services/pipeline_stage.py:352` · `stage_service.py:1076`",
  "sections": [["What", "…"], ["Impact", "…"], ["Fix", "…"]]}]
```

## Commands
```bash
cosmos audit import docs/qa-findings.json --prefix QA --source qa-audit.md
cosmos audit list [--status open|fixed|withdrawn|wontfix|regressed] [--severity critical] [--json]
cosmos audit show QA-11
cosmos audit fix QA-12 "org_id__eq → org_id, PR #<n>"      # records HEAD as fixed_commit
cosmos audit withdraw QA-8 "companies is shared reference data by design"
cosmos audit wontfix QA-6 | cosmos audit reopen QA-6
cosmos audit claim QA-1 | cosmos audit pr-open QA-1 | cosmos audit needs-human QA-17 "intent unclear"
cosmos audit set QA-1 pr_open "PR #<n>"
cosmos audit export -o docs/qa-findings.json                  # same schema back out
cosmos audit report --format md -o docs/qa-audit.md           # regenerated from the ledger
cosmos audit report --format slack                            # parent + threaded replies as JSON
```

## Publishing to Slack
```bash
cosmos audit slack                      # dry run: preview cards for open findings not yet posted
cosmos audit slack --validate           # blocks.validate every card (no token needed)
export SLACK_BOT_TOKEN=xoxb-…             # scopes: chat:write, reactions:write — env only, never stored
cosmos audit slack --send --channel C0123456
cosmos audit slack --status             # posted vs pending
cosmos audit slack --seed-state docs/.slack-posted.json --prefix QA   # migrate from the legacy poster
```

```bash
cosmos audit slack --convert --dry --channel C0123456                 # rewrite already-posted plain-text messages as cards
cosmos audit slack --convert --only QA-12 --ts <permalink> --channel C0123456   # one message, needs only chat:write
```

Each open finding becomes one top-level Block Kit card: header **containing the title** (`🔴 CRITICAL · QA-11 — …`),
a fields row (Severity · Ref · Area · Status · Location), a divider, one section per labelled paragraph, the ack legend, and a
**trailing divider** — Slack groups consecutive same-app messages, and without it cards bleed into each other. Cards are
pre-seeded with 👀 / ✅ / 🚫 reactions, so acking is one click and each bug can be
discussed in its own thread. Already-posted ids are tracked in `.cosmos/state/slack-posted.json` (gitignored);
re-running never duplicates a post. `--all` forces a repost.

## Lint: filter keys that are not columns
```bash
cosmos audit lint --repo-base core.crud.base:BaseRepository \
  --crud-glob 'core/crud/*.py' --module-prefix core.crud. \
  --roots webserver/app core processor/app --sys-path .
```
Or set the same keys under `audit.lint` in `.cosmos/config.json`. Walks every `repo.list/get/update/update_many/delete/count/upsert({...})`
call, resolves the repository singleton to its model, and flags literal filter keys that are not columns (silently dropped by
`apply_filters`-style helpers) and operator suffixes passed to methods that take plain column names (`update_many`). This class of bug
produced two real findings. Limits: literal dict keys at the call site only; the target project's dependencies must be importable.

## In the loop with Claude Code
- Typing `finding: …` in a session captures an explicit finding observation; `cosmos dream` turns it into a note.
- `UserPromptSubmit` retrieval ranks findings by the files they anchor to, so a prompt like *"refactor pipeline_stage.py"* surfaces `QA-11` before the edit happens.
- Open findings appear in the CLAUDE.md / AGENTS.md managed block like any other high-importance fact.
