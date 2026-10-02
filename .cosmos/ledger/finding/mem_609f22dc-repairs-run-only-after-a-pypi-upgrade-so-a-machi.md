---
type: "Finding"
title: "Repairs run only after a PyPI upgrade"
description: "Repairs run only after a PyPI upgrade, so a machine whose pip copy is the newest release keeps old user hooks and sessions above a repository get no cosmos"
status: "stable"
generated: {"by": "human:Biswajit Tripathy", "at": "2026-10-07T00:00:00Z"}
sources: [{"resource": "cosmos/upgrade.py", "title": "upgrade.py"}]
stale_after: "2027-04-05T00:00:00Z"
links: ["/lanes/horizon.md"]
id: "mem_609f22dc"
aliases: ["mem_609f22dc"]
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
meta_audit_id: "PROD-ed94db"
meta_finding_status: "open"
meta_found_commit: "270e2f9"
meta_locations: "cosmos/upgrade.py:331"
meta_raw_id: "ed94db"
meta_severity: "high"
meta_source_doc: "manual"
---

# Repairs run only after a PyPI upgrade, so a machine whose pip copy is the newest release keeps old user hooks and sessions above a repository get no cosmos

**Category:** finding · **Status:** active · **Confidence:** 90%

## Details
**What** — On 2026-10-07 the user-level hooks in ~/.claude/settings.json were still the 0.1.5 form (only CLAUDE_PROJECT_DIR or its git root). The HORIZON session runs in ~/Desktop/shyftlabs, one level above horizon/, so for about 5 hours it got no briefing, no Gate and no capture; horizon/.cosmos had 16 watcher observations and no journal. The 0.1.7 repair (_step_user_hooks) fixes it, but repair() runs only from the upgrade path after a newer PyPI wheel, and PyPI still had 0.1.5; a repository's vendored or mirrored 0.1.7 never triggers it.

**Impact** — Every session opened in a parent folder (a common Desktop habit) silently runs without cosmos; the doctor does not say so.

**Fix** — Run the repairs once per version whenever the running cosmos is newer than state.repaired, whatever installed it (vendor, mirror, editable, pip), and have doctor flag user hooks that lack the parent-folder dispatch.

## Why we believe this
- Observed 1× (first 2026-10-07, last 2026-10-07); source: explicit
- Evidence file: `cosmos/upgrade.py`
- Imported from manual on 2026-10-07

## Links
- lane: [horizon](/lanes/horizon.md)

#finding #high #upgrade
