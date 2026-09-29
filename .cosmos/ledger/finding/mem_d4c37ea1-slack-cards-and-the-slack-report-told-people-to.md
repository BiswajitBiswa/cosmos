---
type: "Finding"
title: "Slack cards and the Slack report told people to run `cosmos audit fix/list` instead of `cosmos flares`"
description: "Slack cards and the Slack report told people to run `cosmos audit fix/list` instead of `cosmos flares`"
status: "stable"
generated: {"by": "human:Biswajit Tripathy", "at": "2026-09-29T00:00:00Z"}
sources: [{"resource": "cosmos/audit.py", "title": "audit.py"}]
stale_after: "2027-03-28T00:00:00Z"
id: "mem_d4c37ea1"
aliases: ["mem_d4c37ea1"]
category: "finding"
cosmos_status: "active"
confidence: 0.9
importance: 0.45
source: "explicit"
created: "2026-09-29"
updated: "2026-09-29"
last_verified: "2026-09-29"
evidence_count: 1
files: ["cosmos/audit.py"]
tags: ["finding", "low", "flares"]
authors: ["Biswajit Tripathy"]
valid_from: "2026-09-29"
meta_area: "flares"
meta_audit_id: "DEV-slack-audit-name"
meta_finding_status: "fixed"
meta_found_commit: "3f80c40"
meta_locations: "`cosmos/audit.py:285` \u00b7 `cosmos/audit.py:295`"
meta_raw_id: "slack-audit-name"
meta_severity: "low"
meta_source_doc: "qa-2026-09-29-commands"
---

# Slack cards and the Slack report told people to run `cosmos audit fix/list` instead of `cosmos flares`

**Category:** finding · **Status:** active · **Confidence:** 90%

## Details
**What** — Every published card ended with `cosmos audit fix <id>`, the pre-rename name; docs say `cosmos flares`.

**Fix** — Messages use `cosmos flares`; `audit` stays an alias.

## Why we believe this
- Observed 1× (first 2026-09-29, last 2026-09-29); source: explicit
- Evidence file: `cosmos/audit.py`
- Imported from qa-2026-09-29-commands on 2026-09-29

#finding #low #flares
