---
type: "Finding"
title: "Console rendered every fact, rule and flare at once and rules sat in a narrow sidebar with unclamped text"
description: "Console rendered every fact, rule and flare at once and rules sat in a narrow sidebar with unclamped text"
status: "stable"
generated: {"by": "human:Biswajit Tripathy", "at": "2026-09-29T00:00:00Z"}
sources: [{"resource": "cosmos/ui.py", "title": "ui.py"}]
stale_after: "2027-03-28T00:00:00Z"
id: "mem_e522e056"
aliases: ["mem_e522e056"]
category: "finding"
cosmos_status: "active"
confidence: 0.9
importance: 0.45
source: "explicit"
created: "2026-09-29"
updated: "2026-09-29"
last_verified: "2026-09-29"
evidence_count: 1
files: ["cosmos/ui.py"]
tags: ["finding", "low", "console"]
authors: ["Biswajit Tripathy"]
valid_from: "2026-09-29"
meta_area: "console"
meta_audit_id: "DEV-console-no-paging"
meta_finding_status: "fixed"
meta_found_commit: "28db571"
meta_locations: "`cosmos/ui.py:666`"
meta_raw_id: "console-no-paging"
meta_severity: "low"
meta_source_doc: "session-2026-09-29"
---

# Console rendered every fact, rule and flare at once and rules sat in a narrow sidebar with unclamped text

**Category:** finding · **Status:** active · **Confidence:** 90%

## Details
**Fix** — In-page paging (ledger 50, rules 10 with a filter, flares 30 per column), three-line clamp with click to expand, rules full width.

## Why we believe this
- Observed 1× (first 2026-09-29, last 2026-09-29); source: explicit
- Evidence file: `cosmos/ui.py`
- Imported from session-2026-09-29 on 2026-09-29

#finding #low #console
