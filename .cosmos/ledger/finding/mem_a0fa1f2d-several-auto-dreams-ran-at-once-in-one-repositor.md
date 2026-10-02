---
type: "Finding"
title: "Several auto-dreams ran at once in one repository (five in retent) and processed the same batch twice, pushing the machi"
description: "Several auto-dreams ran at once in one repository (five in retent) and processed the same batch twice, pushing the machine's load average to 578"
status: "stable"
generated: {"by": "human:Biswajit Tripathy", "at": "2026-10-02T00:00:00Z"}
sources: [{"resource": "cosmos/hooks.py", "title": "hooks.py"}]
stale_after: "2027-03-31T00:00:00Z"
links: ["/lanes/cosmos.md", "/constraint/mem_1192ca15-hooks-must-always-exit-0-the-gate-is-the-only-de.md", "/constraint/mem_4c8727a1-in-claude-desktop-code-tab-sessions-an-mcp-serve.md", "/constraint/mem_a1b7e320-claude-code-caps-each-hook-text-plain-stdout-add.md", "/decision/mem_55db62b9-recall-is-made-visible-with-the-hooks-systemmess.md", "/finding/mem_0448e271-the-watcher-started-a-dream-every-30-seconds-whi.md"]
id: "mem_a0fa1f2d"
aliases: ["mem_a0fa1f2d"]
category: "finding"
lane: "cosmos"
cosmos_status: "active"
confidence: 0.9
importance: 1.0
source: "explicit"
created: "2026-10-02"
updated: "2026-10-02"
last_verified: "2026-10-02"
evidence_count: 1
files: ["cosmos/hooks.py"]
tags: ["finding", "critical"]
authors: ["Biswajit Tripathy"]
valid_from: "2026-10-02"
meta_audit_id: "PROD-4d6787"
meta_finding_status: "fixed"
meta_fixed_commit: "42c8748"
meta_fixed_on: "2026-10-02"
meta_found_commit: "42c8748"
meta_locations: "cosmos/hooks.py"
meta_raw_id: "4d6787"
meta_severity: "critical"
meta_source_doc: "manual"
meta_status_at: "2026-10-02"
meta_status_note: "local commit 42c8748"
---

# Several auto-dreams ran at once in one repository (five in retent) and processed the same batch twice, pushing the machine's load average to 578

**Category:** finding · **Status:** active · **Confidence:** 90%

## Details
**What** — the dream lock expired by age (30 min) while a dream still ran, and was not created atomically; a dream slowed by load let a second start, which slowed both (dream.log: identical '75 observations -> 40 new, 35 merged' at 03:40Z and 04:43Z)

**Fix** — take_dream_lock: O_EXCL create, holds the dream's own pid, stale only when that process is gone or after 6 h; test_one_dream_at_a_time_and_a_dead_ones_lock_is_taken_over

## Why we believe this
- Observed 1× (first 2026-10-02, last 2026-10-02); source: explicit
- Evidence file: `cosmos/hooks.py`
- Marked fixed on 2026-10-02: local commit 42c8748

## Related
- [[mem_1192ca15]]
- [[mem_4c8727a1]]
- [[mem_a1b7e320]]
- [[mem_55db62b9]]
- [[mem_0448e271]]

## Links
- lane: [cosmos](/lanes/cosmos.md)
- related: [mem_1192ca15](/constraint/mem_1192ca15-hooks-must-always-exit-0-the-gate-is-the-only-de.md)
- related: [mem_4c8727a1](/constraint/mem_4c8727a1-in-claude-desktop-code-tab-sessions-an-mcp-serve.md)
- related: [mem_a1b7e320](/constraint/mem_a1b7e320-claude-code-caps-each-hook-text-plain-stdout-add.md)
- related: [mem_55db62b9](/decision/mem_55db62b9-recall-is-made-visible-with-the-hooks-systemmess.md)
- related: [mem_0448e271](/finding/mem_0448e271-the-watcher-started-a-dream-every-30-seconds-whi.md)

#finding #critical
