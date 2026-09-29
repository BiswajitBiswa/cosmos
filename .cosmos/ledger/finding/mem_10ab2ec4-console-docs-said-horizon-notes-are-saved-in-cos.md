---
type: "Finding"
title: "Console docs said Horizon notes are saved in .cosmos/ledger/intake/; they are saved in ledger/horizon/"
description: "Console docs said Horizon notes are saved in .cosmos/ledger/intake/; they are saved in ledger/horizon/"
status: "stable"
generated: {"by": "human:Biswajit Tripathy", "at": "2026-09-29T00:00:00Z"}
sources: [{"resource": "cosmos/ui.py", "title": "ui.py"}, {"resource": "cosmos/intake.py", "title": "intake.py"}]
stale_after: "2027-03-28T00:00:00Z"
id: "mem_10ab2ec4"
aliases: ["mem_10ab2ec4"]
category: "finding"
cosmos_status: "active"
confidence: 0.9
importance: 0.45
source: "explicit"
created: "2026-09-29"
updated: "2026-09-29"
last_verified: "2026-09-29"
evidence_count: 1
files: ["cosmos/ui.py", "cosmos/intake.py"]
tags: ["finding", "low", "docs"]
authors: ["Biswajit Tripathy"]
valid_from: "2026-09-29"
meta_area: "docs"
meta_audit_id: "DEV-horizon-doc-path"
meta_finding_status: "fixed"
meta_found_commit: "3f80c40"
meta_locations: "`cosmos/ui.py:1000` \u00b7 `cosmos/intake.py:23`"
meta_raw_id: "horizon-doc-path"
meta_severity: "low"
meta_source_doc: "qa-2026-09-29-commands"
---

# Console docs said Horizon notes are saved in .cosmos/ledger/intake/; they are saved in ledger/horizon/

**Category:** finding · **Status:** active · **Confidence:** 90%

## Details
**Fix** — Doc names ledger/horizon/.

## Why we believe this
- Observed 1× (first 2026-09-29, last 2026-09-29); source: explicit
- Evidence file: `cosmos/ui.py`
- Evidence file: `cosmos/intake.py`
- Imported from qa-2026-09-29-commands on 2026-09-29

#finding #low #docs
