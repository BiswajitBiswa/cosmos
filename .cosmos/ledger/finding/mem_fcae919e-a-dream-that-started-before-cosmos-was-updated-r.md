---
type: "Finding"
title: "A dream that started before cosmos was updated rewrites slash command files with its stale in-memory catalogue at the en"
description: "A dream that started before cosmos was updated rewrites slash command files with its stale in-memory catalogue at the end (commands.refresh)"
status: "stable"
generated: {"by": "human:Biswajit Tripathy", "at": "2026-10-01T00:00:00Z"}
sources: [{"resource": "cosmos/dream.py", "title": "dream.py"}]
stale_after: "2027-03-30T00:00:00Z"
links: ["/lanes/cosmos.md", "/finding/mem_10ab2ec4-console-docs-said-horizon-notes-are-saved-in-cos.md", "/finding/mem_5a1661f5-journal-credited-commits-made-in-another-folder.md", "/finding/mem_ac19fa4c-a-whole-ledger-save-from-a-process-that-loaded-e.md", "/finding/mem_d4c37ea1-slack-cards-and-the-slack-report-told-people-to.md", "/finding/mem_e522e056-console-rendered-every-fact-rule-and-flare-at-on.md"]
id: "mem_fcae919e"
aliases: ["mem_fcae919e"]
category: "finding"
lane: "cosmos"
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

## Related
- [[mem_10ab2ec4]]
- [[mem_5a1661f5]]
- [[mem_ac19fa4c]]
- [[mem_d4c37ea1]]
- [[mem_e522e056]]

## Links
- lane: [cosmos](/lanes/cosmos.md)
- related: [mem_10ab2ec4](/finding/mem_10ab2ec4-console-docs-said-horizon-notes-are-saved-in-cos.md)
- related: [mem_5a1661f5](/finding/mem_5a1661f5-journal-credited-commits-made-in-another-folder.md)
- related: [mem_ac19fa4c](/finding/mem_ac19fa4c-a-whole-ledger-save-from-a-process-that-loaded-e.md)
- related: [mem_d4c37ea1](/finding/mem_d4c37ea1-slack-cards-and-the-slack-report-told-people-to.md)
- related: [mem_e522e056](/finding/mem_e522e056-console-rendered-every-fact-rule-and-flare-at-on.md)

#finding #low
