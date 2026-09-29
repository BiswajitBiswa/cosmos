---
type: "Finding"
title: "A whole-ledger save from a process that loaded earlier (a dream, the console, an MCP call) wrote every note back and rev"
description: "A whole-ledger save from a process that loaded earlier (a dream, the console, an MCP call) wrote every note back and reverted flare lifecycle changes made meanwhile"
status: "stable"
generated: {"by": "human:Biswajit Tripathy", "at": "2026-09-29T00:00:00Z"}
sources: [{"resource": "cosmos/store.py", "title": "store.py"}, {"resource": "cosmos/dream.py", "title": "dream.py"}]
stale_after: "2027-03-28T00:00:00Z"
id: "mem_ac19fa4c"
aliases: ["mem_ac19fa4c"]
category: "finding"
cosmos_status: "active"
confidence: 0.9
importance: 0.85
source: "explicit"
created: "2026-09-29"
updated: "2026-09-29"
last_verified: "2026-09-29"
evidence_count: 1
files: ["cosmos/store.py", "cosmos/dream.py"]
tags: ["finding", "high", "ledger"]
authors: ["Biswajit Tripathy"]
valid_from: "2026-09-29"
meta_area: "ledger"
meta_audit_id: "PROD-stale-save-reverts-lifecycle"
meta_finding_status: "fixed"
meta_found_commit: "fe51967"
meta_locations: "`cosmos/store.py:283` \u00b7 `cosmos/dream.py:522`"
meta_raw_id: "stale-save-reverts-lifecycle"
meta_severity: "high"
meta_source_doc: "qa-report-2026-09-29"
---

# A whole-ledger save from a process that loaded earlier (a dream, the console, an MCP call) wrote every note back and reverted flare lifecycle changes made meanwhile

**Category:** finding · **Status:** active · **Confidence:** 90%

## Details
**What** — Reported by the QA session: ~50 flares set to pr_open/claimed in RETEN between 11:00 and 16:00 IST went back to open, text intact. Ledger.save_all rewrote every note from the caller's in-memory copy; the git history shows no revert, so it happened in the working tree between the 10-minute commits (a dream ran at 13:49 IST).

**Fix** — Three-way save: notes remember their loaded state; an unchanged note never overwrites a newer file; a note changed on both sides keeps this process's fields and the file's others. TestConcurrentSaves reproduces it and fails on the old code.

## Why we believe this
- Observed 1× (first 2026-09-29, last 2026-09-29); source: explicit
- Evidence file: `cosmos/store.py`
- Evidence file: `cosmos/dream.py`
- Imported from qa-report-2026-09-29 on 2026-09-29

#finding #high #ledger
