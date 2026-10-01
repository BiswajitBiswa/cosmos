---
type: "Finding"
title: "A repository whose committed hook command is older than the user-level one runs every hook twice (two Gates, two briefin"
description: "A repository whose committed hook command is older than the user-level one runs every hook twice (two Gates, two briefings)"
status: "stable"
generated: {"by": "human:Biswajit Tripathy", "at": "2026-10-01T00:00:00Z"}
sources: [{"resource": ".claude/settings.js", "title": "settings.js"}, {"resource": "cosmos/upgrade.py", "title": "upgrade.py"}]
stale_after: "2027-03-30T00:00:00Z"
links: ["/lanes/cosmos.md", "/decision/mem_4efbf3d7-releases-and-their-repairs-reach-every-project-b.md", "/finding/mem_0448e271-the-watcher-started-a-dream-every-30-seconds-whi.md", "/finding/mem_1db8264f-a-claude-desktop-mcp-entry-named-cosmos-pinned-t.md", "/finding/mem_498078e0-atlas-page-4-of-8-deep-pass-diagrams-failed-unde.md", "/finding/mem_5790a327-cosmos-connect-with-no-agent-argument-failed-arg.md"]
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
- [[mem_4efbf3d7]]
- [[mem_0448e271]]
- [[mem_1db8264f]]
- [[mem_498078e0]]
- [[mem_5790a327]]

## Links
- lane: [cosmos](/lanes/cosmos.md)
- related: [mem_4efbf3d7](/decision/mem_4efbf3d7-releases-and-their-repairs-reach-every-project-b.md)
- related: [mem_0448e271](/finding/mem_0448e271-the-watcher-started-a-dream-every-30-seconds-whi.md)
- related: [mem_1db8264f](/finding/mem_1db8264f-a-claude-desktop-mcp-entry-named-cosmos-pinned-t.md)
- related: [mem_498078e0](/finding/mem_498078e0-atlas-page-4-of-8-deep-pass-diagrams-failed-unde.md)
- related: [mem_5790a327](/finding/mem_5790a327-cosmos-connect-with-no-agent-argument-failed-arg.md)

#finding #medium
