---
type: "Finding"
title: "A dream that started before cosmos was updated rewrites slash command files with its stale in-memory catalogue at the en"
description: "A dream that started before cosmos was updated rewrites slash command files with its stale in-memory catalogue at the end (commands.refresh)"
status: "stable"
generated: {"by": "human:Biswajit Tripathy", "at": "2026-10-01T00:00:00Z"}
sources: [{"resource": "cosmos/dream.py", "title": "dream.py"}]
stale_after: "2027-03-30T00:00:00Z"
id: "mem_fcae919e"
aliases: ["mem_fcae919e"]
category: "finding"
cosmos_status: "active"
confidence: 0.9
importance: 0.45
source: "explicit"
created: "2026-10-01"
updated: "2026-10-01"
last_verified: "2026-10-01"
evidence_count: 1
files: ["cosmos/dream.py"]
tags: ["finding", "low"]
authors: ["Biswajit Tripathy"]
valid_from: "2026-10-01"
meta_audit_id: "PROD-fec6d4"
meta_finding_status: "open"
meta_found_commit: "4580d07"
meta_locations: "cosmos/dream.py:587"
meta_raw_id: "fec6d4"
meta_severity: "low"
meta_source_doc: "manual"
---

# A dream that started before cosmos was updated rewrites slash command files with its stale in-memory catalogue at the end (commands.refresh)

**Category:** finding · **Status:** active · **Confidence:** 90%

## Details
**What** — the dream process loaded the old commands.py; its final refresh restored .claude/commands/flare.md and the other agents' copies to the previous text

**Fix** — dream: skip refresh (or re-exec) when code_stamp() changed since it started, like the watcher

## Why we believe this
- Observed 1× (first 2026-10-01, last 2026-10-01); source: explicit
- Evidence file: `cosmos/dream.py`
- Imported from manual on 2026-10-01

#finding #low
