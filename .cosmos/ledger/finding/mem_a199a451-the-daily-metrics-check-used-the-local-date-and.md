---
type: "Finding"
title: "The daily metrics check used the local date and the file the UTC date, so near midnight every dream rewrote the day's re"
description: "The daily metrics check used the local date and the file the UTC date, so near midnight every dream rewrote the day's report"
status: "stable"
generated: {"by": "human:Biswajit Tripathy", "at": "2026-10-02T00:00:00Z"}
sources: [{"resource": "cosmos/pulse.py", "title": "pulse.py"}]
stale_after: "2027-03-31T00:00:00Z"
links: ["/lanes/cosmos.md", "/decision/mem_8e60778d-cosmos-pulse-measures-a-repository-from-its-own.md", "/finding/mem_0448e271-the-watcher-started-a-dream-every-30-seconds-whi.md", "/finding/mem_1db8264f-a-claude-desktop-mcp-entry-named-cosmos-pinned-t.md", "/finding/mem_498078e0-atlas-page-4-of-8-deep-pass-diagrams-failed-unde.md", "/finding/mem_5790a327-cosmos-connect-with-no-agent-argument-failed-arg.md"]
id: "mem_a199a451"
aliases: ["mem_a199a451"]
category: "finding"
lane: "cosmos"
cosmos_status: "active"
confidence: 0.9
importance: 0.65
source: "explicit"
created: "2026-10-02"
updated: "2026-10-02"
last_verified: "2026-10-02"
evidence_count: 1
files: ["cosmos/pulse.py"]
tags: ["finding", "medium"]
authors: ["Biswajit Tripathy"]
valid_from: "2026-10-02"
meta_audit_id: "PROD-b88419"
meta_finding_status: "fixed"
meta_fixed_commit: "42c8748"
meta_fixed_on: "2026-10-02"
meta_found_commit: "c01474c"
meta_locations: "cosmos/pulse.py"
meta_raw_id: "b88419"
meta_severity: "medium"
meta_source_doc: "manual"
meta_status_at: "2026-10-02"
meta_status_note: "local commit 42c8748"
---

# The daily metrics check used the local date and the file the UTC date, so near midnight every dream rewrote the day's report

**Category:** finding · **Status:** active · **Confidence:** 90%

## Details
**Fix** — due() uses the UTC date save() names the file by; caught by test_an_idle_dream_changes_no_file

## Why we believe this
- Observed 1× (first 2026-10-02, last 2026-10-02); source: explicit
- Evidence file: `cosmos/pulse.py`
- Marked fixed on 2026-10-02: local commit 42c8748

## Related
- [[mem_8e60778d]]
- [[mem_0448e271]]
- [[mem_1db8264f]]
- [[mem_498078e0]]
- [[mem_5790a327]]

## Links
- lane: [cosmos](/lanes/cosmos.md)
- related: [mem_8e60778d](/decision/mem_8e60778d-cosmos-pulse-measures-a-repository-from-its-own.md)
- related: [mem_0448e271](/finding/mem_0448e271-the-watcher-started-a-dream-every-30-seconds-whi.md)
- related: [mem_1db8264f](/finding/mem_1db8264f-a-claude-desktop-mcp-entry-named-cosmos-pinned-t.md)
- related: [mem_498078e0](/finding/mem_498078e0-atlas-page-4-of-8-deep-pass-diagrams-failed-unde.md)
- related: [mem_5790a327](/finding/mem_5790a327-cosmos-connect-with-no-agent-argument-failed-arg.md)

#finding #medium
