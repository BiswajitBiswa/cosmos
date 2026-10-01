---
type: "Finding"
title: "cosmos_remember and cosmos_flare took 40-48 s on retent (2,975 notes), so agents' saves timed out"
description: "cosmos_remember and cosmos_flare took 40-48 s on retent (2,975 notes), so agents' saves timed out"
status: "stable"
generated: {"by": "human:Biswajit Tripathy", "at": "2026-10-02T00:00:00Z"}
sources: [{"resource": "cosmos/store.py", "title": "store.py"}]
stale_after: "2027-03-31T00:00:00Z"
links: ["/lanes/cosmos.md", "/finding/mem_0b83670f-a-session-in-a-project-without-cosmos-filed-its.md", "/finding/mem_488b620a-every-hook-took-700-790-ms-on-retent-2-925-notes.md", "/finding/mem_ac19fa4c-a-whole-ledger-save-from-a-process-that-loaded-e.md"]
id: "mem_93255725"
aliases: ["mem_93255725"]
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
files: ["cosmos/store.py"]
tags: ["finding", "critical"]
authors: ["Biswajit Tripathy"]
valid_from: "2026-10-02"
meta_audit_id: "PROD-7358f3"
meta_finding_status: "open"
meta_found_commit: "c01474c"
meta_locations: "cosmos/store.py"
meta_raw_id: "7358f3"
meta_severity: "critical"
meta_source_doc: "manual"
---

# cosmos_remember and cosmos_flare took 40-48 s on retent (2,975 notes), so agents' saves timed out

**Category:** finding · **Status:** active · **Confidence:** 90%

## Details
**What** — every save_all rewrote every note, each with two rglob walks of the ledger (57 of 64 s in a profile); the RETEN session reported a decision it could not save while cosmos was timing out

**Fix** — save_all writes only notes changed since load, with one folder walk per batch; remember 1.4-2.8 s, flare 1.3 s on a retent clone

## Why we believe this
- Observed 1× (first 2026-10-02, last 2026-10-02); source: explicit
- Evidence file: `cosmos/store.py`
- Imported from manual on 2026-10-02

## Related
- [[mem_0b83670f]]
- [[mem_488b620a]]
- [[mem_ac19fa4c]]

## Links
- lane: [cosmos](/lanes/cosmos.md)
- related: [mem_0b83670f](/finding/mem_0b83670f-a-session-in-a-project-without-cosmos-filed-its.md)
- related: [mem_488b620a](/finding/mem_488b620a-every-hook-took-700-790-ms-on-retent-2-925-notes.md)
- related: [mem_ac19fa4c](/finding/mem_ac19fa4c-a-whole-ledger-save-from-a-process-that-loaded-e.md)

#finding #critical
