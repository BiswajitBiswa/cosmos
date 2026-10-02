---
type: "Finding"
title: "A repository whose committed hook command is older than the user-level one runs every hook twice (two Gates, two briefin"
description: "A repository whose committed hook command is older than the user-level one runs every hook twice (two Gates, two briefings)"
status: "stable"
generated: {"by": "human:Biswajit Tripathy", "at": "2026-10-01T00:00:00Z"}
sources: [{"resource": ".claude/settings.js", "title": "settings.js"}, {"resource": "cosmos/upgrade.py", "title": "upgrade.py"}]
stale_after: "2027-03-30T00:00:00Z"
links: ["/lanes/cosmos.md", "/constraint/mem_15da1401-for-clients-that-dont-report-their-folders-every.md", "/constraint/mem_cf1dd94b-tests-already-set-cosmosnobackground-so-they-can.md", "/decision/mem_4efbf3d7-releases-and-their-repairs-reach-every-project-b.md", "/dependency/mem_06dacbf0-self-upgrade-at-most-once-a-day-per-machine-a-se.md", "/dependency/mem_0c3037f2-cosmos-upgrade-py-210-maybebackground-the-daily.md"]
id: "mem_6fa48630"
aliases: ["mem_6fa48630"]
category: "finding"
lane: "cosmos"
cosmos_status: "active"
confidence: 0.9
importance: 0.65
source: "explicit"
created: "2026-10-01"
updated: "2026-10-01"
last_verified: "2026-10-01"
evidence_count: 1
files: [".claude/settings.js", "cosmos/upgrade.py"]
tags: ["finding", "medium"]
authors: ["Biswajit Tripathy"]
valid_from: "2026-10-01"
meta_audit_id: "PROD-0180e8"
meta_finding_status: "open"
meta_found_commit: "a0ee41c"
meta_locations: ".claude/settings.json \u00b7 cosmos/upgrade.py"
meta_raw_id: "0180e8"
meta_severity: "medium"
meta_source_doc: "manual"
---

# A repository whose committed hook command is older than the user-level one runs every hook twice (two Gates, two briefings)

**Category:** finding · **Status:** active · **Confidence:** 90%

## Details
**What** — Claude Code runs both when the repo-level and user-level commands differ; seen in this repo: two GATE messages for one turn

**Fix** — repair's _step_repo_hooks rewrites the repository's command to the current one, so both levels carry the same command

## Why we believe this
- Observed 1× (first 2026-10-01, last 2026-10-01); source: explicit
- Evidence file: `.claude/settings.js`
- Evidence file: `cosmos/upgrade.py`
- Imported from manual on 2026-10-01

## Related
- [[mem_15da1401]]
- [[mem_cf1dd94b]]
- [[mem_4efbf3d7]]
- [[mem_06dacbf0]]
- [[mem_0c3037f2]]

## Links
- lane: [cosmos](/lanes/cosmos.md)
- related: [mem_15da1401](/constraint/mem_15da1401-for-clients-that-dont-report-their-folders-every.md)
- related: [mem_cf1dd94b](/constraint/mem_cf1dd94b-tests-already-set-cosmosnobackground-so-they-can.md)
- related: [mem_4efbf3d7](/decision/mem_4efbf3d7-releases-and-their-repairs-reach-every-project-b.md)
- related: [mem_06dacbf0](/dependency/mem_06dacbf0-self-upgrade-at-most-once-a-day-per-machine-a-se.md)
- related: [mem_0c3037f2](/dependency/mem_0c3037f2-cosmos-upgrade-py-210-maybebackground-the-daily.md)

#finding #medium
