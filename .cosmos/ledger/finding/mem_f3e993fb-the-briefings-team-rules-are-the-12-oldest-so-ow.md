---
type: "Finding"
title: "The briefing's team rules are the 12 oldest, so owner rules added later never reach a session"
description: "The briefing's team rules are the 12 oldest, so owner rules added later never reach a session"
status: "stable"
generated: {"by": "human:Biswajit Tripathy", "at": "2026-10-07T00:00:00Z"}
sources: [{"resource": "cosmos/charter.py", "title": "charter.py"}]
stale_after: "2027-04-05T00:00:00Z"
links: ["/lanes/cosmos.md", "/decision/mem_5cfd6c9b-commit-note-by-biswajit-tripathy-autopilot-from.md", "/finding/mem_07187b11-mcp-entries-cosmos-writes-start-python3-which-do.md", "/finding/mem_488b620a-every-hook-took-700-790-ms-on-retent-2-925-notes.md", "/finding/mem_ac19fa4c-a-whole-ledger-save-from-a-process-that-loaded-e.md", "/finding/mem_b058375a-a-pip-install-of-the-same-version-string-shadowe.md"]
id: "mem_f3e993fb"
aliases: ["mem_f3e993fb"]
category: "finding"
lane: "cosmos"
cosmos_status: "active"
confidence: 0.9
importance: 0.85
source: "explicit"
created: "2026-10-07"
updated: "2026-10-07"
last_verified: "2026-10-07"
evidence_count: 1
files: ["cosmos/charter.py"]
tags: ["finding", "high", "briefing"]
authors: ["Biswajit Tripathy"]
valid_from: "2026-10-07"
meta_area: "briefing"
meta_audit_id: "PROD-725032"
meta_finding_status: "open"
meta_found_commit: "552809d"
meta_locations: "cosmos/charter.py:131"
meta_raw_id: "725032"
meta_severity: "high"
meta_source_doc: "manual"
---

# The briefing's team rules are the 12 oldest, so owner rules added later never reach a session

**Category:** finding · **Status:** active · **Confidence:** 90%

## Details
**What** — charter.summary sorts explicit rules by (category, created) and keeps the first 12. retent has 67 explicit rules (2026-10-07): the briefing shows 2 architecture and 10 constraint rules from 2026-09-24 to 09-29, and none of the 47 conventions or workflows, including every owner rule since 2026-09-30 (one shared worktree, release flow, picture colours).

**Impact** — The rules the owner set most recently, which sessions most need, are never in the session-start briefing; they surface only when a prompt happens to match them in recall.

**Fix** — Rank rules by recency and importance (newest first, a cap per category), or show the newest 12 and say how many more there are with the command that lists them.

## Why we believe this
- Observed 1× (first 2026-10-07, last 2026-10-07); source: explicit
- Evidence file: `cosmos/charter.py`
- Imported from manual on 2026-10-07

## Related
- [[mem_5cfd6c9b]]
- [[mem_07187b11]]
- [[mem_488b620a]]
- [[mem_ac19fa4c]]
- [[mem_b058375a]]

## Links
- lane: [cosmos](/lanes/cosmos.md)
- related: [mem_5cfd6c9b](/decision/mem_5cfd6c9b-commit-note-by-biswajit-tripathy-autopilot-from.md)
- related: [mem_07187b11](/finding/mem_07187b11-mcp-entries-cosmos-writes-start-python3-which-do.md)
- related: [mem_488b620a](/finding/mem_488b620a-every-hook-took-700-790-ms-on-retent-2-925-notes.md)
- related: [mem_ac19fa4c](/finding/mem_ac19fa4c-a-whole-ledger-save-from-a-process-that-loaded-e.md)
- related: [mem_b058375a](/finding/mem_b058375a-a-pip-install-of-the-same-version-string-shadowe.md)

#finding #high #briefing
