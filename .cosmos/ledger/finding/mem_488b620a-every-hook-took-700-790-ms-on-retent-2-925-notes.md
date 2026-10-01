---
type: "Finding"
title: "Every hook took 700-790 ms on retent (2,925 notes) because Ledger.load re-parsed every markdown note on every call"
description: "Every hook took 700-790 ms on retent (2,925 notes) because Ledger.load re-parsed every markdown note on every call"
status: "stable"
generated: {"by": "human:Biswajit Tripathy", "at": "2026-10-01T00:00:00Z"}
sources: [{"resource": "cosmos/store.py", "title": "store.py"}]
stale_after: "2027-03-30T00:00:00Z"
links: ["/lanes/cosmos.md", "/finding/mem_07187b11-mcp-entries-cosmos-writes-start-python3-which-do.md", "/finding/mem_93255725-cosmosremember-and-cosmosflare-took-40-48-s-on-r.md", "/finding/mem_ac19fa4c-a-whole-ledger-save-from-a-process-that-loaded-e.md", "/finding/mem_b058375a-a-pip-install-of-the-same-version-string-shadowe.md", "/finding/mem_cb4bccc1-retents-session-briefing-13-326-chars-exceeded-c.md"]
id: "mem_488b620a"
aliases: ["mem_488b620a"]
category: "finding"
lane: "cosmos"
cosmos_status: "active"
confidence: 0.9
importance: 0.85
source: "explicit"
created: "2026-10-01"
updated: "2026-10-01"
last_verified: "2026-10-01"
evidence_count: 1
files: ["cosmos/store.py"]
tags: ["finding", "high"]
authors: ["Biswajit Tripathy"]
valid_from: "2026-10-01"
meta_audit_id: "PROD-2bd662"
meta_finding_status: "fixed"
meta_fixed_commit: "a7eca9e"
meta_fixed_on: "2026-10-01"
meta_found_commit: "a7eca9e"
meta_locations: "cosmos/store.py"
meta_raw_id: "2bd662"
meta_severity: "high"
meta_source_doc: "manual"
meta_status_at: "2026-10-01"
meta_status_note: "local commit; retrieval index cache next"
---

# Every hook took 700-790 ms on retent (2,925 notes) because Ledger.load re-parsed every markdown note on every call

**Category:** finding · **Status:** active · **Confidence:** 90%

## Details
**What** — profiled 2026-10-01: python start 33 ms, imports 85 ms, Ledger.load 702 ms

**Fix** — machine-local parsed-ledger cache keyed by each note's mtime and size (~/.cache/cosmos): warm load 74 ms; hooks 235-394 ms median (cosmos pulse --bench). Next: cache the retrieval index

## Why we believe this
- Observed 1× (first 2026-10-01, last 2026-10-01); source: explicit
- Evidence file: `cosmos/store.py`
- Marked fixed on 2026-10-01: local commit; retrieval index cache next

## Related
- [[mem_07187b11]]
- [[mem_93255725]]
- [[mem_ac19fa4c]]
- [[mem_b058375a]]
- [[mem_cb4bccc1]]

## Links
- lane: [cosmos](/lanes/cosmos.md)
- related: [mem_07187b11](/finding/mem_07187b11-mcp-entries-cosmos-writes-start-python3-which-do.md)
- related: [mem_93255725](/finding/mem_93255725-cosmosremember-and-cosmosflare-took-40-48-s-on-r.md)
- related: [mem_ac19fa4c](/finding/mem_ac19fa4c-a-whole-ledger-save-from-a-process-that-loaded-e.md)
- related: [mem_b058375a](/finding/mem_b058375a-a-pip-install-of-the-same-version-string-shadowe.md)
- related: [mem_cb4bccc1](/finding/mem_cb4bccc1-retents-session-briefing-13-326-chars-exceeded-c.md)

#finding #high
