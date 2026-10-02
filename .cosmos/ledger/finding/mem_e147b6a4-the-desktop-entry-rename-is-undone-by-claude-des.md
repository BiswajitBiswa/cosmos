---
type: "Finding"
title: "The Desktop entry rename is undone by Claude Desktop"
description: "The Desktop entry rename is undone by Claude Desktop, which rewrites its config file from memory"
status: "stable"
generated: {"by": "human:Biswajit Tripathy", "at": "2026-10-07T00:00:00Z"}
sources: [{"resource": "cosmos/upgrade.py", "title": "upgrade.py"}]
stale_after: "2027-04-05T00:00:00Z"
links: ["/lanes/horizon.md"]
id: "mem_e147b6a4"
aliases: ["mem_e147b6a4"]
category: "finding"
lane: "horizon"
cosmos_status: "active"
confidence: 0.9
importance: 0.85
source: "explicit"
created: "2026-10-07"
updated: "2026-10-07"
last_verified: "2026-10-07"
evidence_count: 1
files: ["cosmos/upgrade.py"]
tags: ["finding", "high", "upgrade"]
authors: ["Biswajit Tripathy"]
valid_from: "2026-10-07"
meta_area: "upgrade"
meta_audit_id: "PROD-628c95"
meta_finding_status: "open"
meta_found_commit: "b28253d"
meta_locations: "cosmos/upgrade.py:299"
meta_raw_id: "628c95"
meta_severity: "high"
meta_source_doc: "manual"
---

# The Desktop entry rename is undone by Claude Desktop, which rewrites its config file from memory

**Category:** finding · **Status:** active · **Confidence:** 90%

## Details
**What** — _step_desktop_pin renamed the claude_desktop_config.json entry cosmos to cosmos-retent at 21:37 on 2026-10-07. Claude Desktop keeps that file's contents (its preferences live in the same file) in memory and wrote it back when restarted at 22:21, restoring the cosmos entry. Desktop sessions keep sending cosmos_* writes to retent.

**Impact** — The repair reports success but changes nothing; every Desktop session's cosmos tools still write to one repository.

**Fix** — Edit the file only when Claude Desktop is not running (check for the process; otherwise print the exact steps: quit with Cmd+Q, run one command, reopen), and have session_start keep warning until the entry is gone.

## Why we believe this
- Observed 1× (first 2026-10-07, last 2026-10-07); source: explicit
- Evidence file: `cosmos/upgrade.py`
- Imported from manual on 2026-10-07

## Links
- lane: [horizon](/lanes/horizon.md)

#finding #high #upgrade
