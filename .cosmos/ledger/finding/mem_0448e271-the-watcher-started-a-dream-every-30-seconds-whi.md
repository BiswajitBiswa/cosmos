---
type: "Finding"
title: "The watcher started a dream every 30 seconds while model ranges waited and no model was available"
description: "The watcher started a dream every 30 seconds while model ranges waited and no model was available"
status: "stable"
generated: {"by": "human:Biswajit Tripathy", "at": "2026-10-01T00:00:00Z"}
sources: [{"resource": "cosmos/hooks.py", "title": "hooks.py"}]
stale_after: "2027-03-30T00:00:00Z"
links: ["/lanes/cosmos.md", "/constraint/mem_1192ca15-hooks-must-always-exit-0-the-gate-is-the-only-de.md", "/constraint/mem_4c8727a1-in-claude-desktop-code-tab-sessions-an-mcp-serve.md", "/constraint/mem_a1b7e320-claude-code-caps-each-hook-text-plain-stdout-add.md", "/decision/mem_55db62b9-recall-is-made-visible-with-the-hooks-systemmess.md", "/finding/mem_1db8264f-a-claude-desktop-mcp-entry-named-cosmos-pinned-t.md"]
id: "mem_0448e271"
aliases: ["mem_0448e271"]
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
files: ["cosmos/hooks.py"]
tags: ["finding", "medium"]
authors: ["Biswajit Tripathy"]
valid_from: "2026-10-01"
meta_audit_id: "PROD-07ab58"
meta_finding_status: "open"
meta_found_commit: "20aa94f"
meta_locations: "cosmos/hooks.py"
meta_raw_id: "07ab58"
meta_severity: "medium"
meta_source_doc: "manual"
---

# The watcher started a dream every 30 seconds while model ranges waited and no model was available

**Category:** finding · **Status:** active · **Confidence:** 90%

## Details
**What** — should_auto_dream measured age from the last dream record, but a dream that changes nothing writes none, so 'an hour since the last dream' stayed true every tick (dream.log: one auto-dream each 30 s, each rewriting the slash commands)

**Fix** — auto_dream stamps state/dream.started and should_auto_dream counts it; test_a_dream_that_changed_nothing_still_waits_its_turn

## Why we believe this
- Observed 1× (first 2026-10-01, last 2026-10-01); source: explicit
- Evidence file: `cosmos/hooks.py`
- Imported from manual on 2026-10-01

## Related
- [[mem_1192ca15]]
- [[mem_4c8727a1]]
- [[mem_a1b7e320]]
- [[mem_55db62b9]]
- [[mem_1db8264f]]

## Links
- lane: [cosmos](/lanes/cosmos.md)
- related: [mem_1192ca15](/constraint/mem_1192ca15-hooks-must-always-exit-0-the-gate-is-the-only-de.md)
- related: [mem_4c8727a1](/constraint/mem_4c8727a1-in-claude-desktop-code-tab-sessions-an-mcp-serve.md)
- related: [mem_a1b7e320](/constraint/mem_a1b7e320-claude-code-caps-each-hook-text-plain-stdout-add.md)
- related: [mem_55db62b9](/decision/mem_55db62b9-recall-is-made-visible-with-the-hooks-systemmess.md)
- related: [mem_1db8264f](/finding/mem_1db8264f-a-claude-desktop-mcp-entry-named-cosmos-pinned-t.md)

#finding #medium
