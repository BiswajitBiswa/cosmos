---
type: "Finding"
title: "The Charter check reported dot-prefixed paths and globs as missing"
description: "The Charter check reported dot-prefixed paths and globs as missing"
status: "stable"
generated: {"by": "human:Biswajit Tripathy", "at": "2026-10-07T00:00:00Z"}
sources: [{"resource": "cosmos/lanes.py", "title": "lanes.py"}]
stale_after: "2027-04-05T00:00:00Z"
links: ["/lanes/horizon.md"]
id: "mem_4bc7ab16"
aliases: ["mem_4bc7ab16"]
category: "finding"
lane: "horizon"
cosmos_status: "active"
confidence: 0.9
importance: 0.65
source: "explicit"
created: "2026-10-07"
updated: "2026-10-07"
last_verified: "2026-10-07"
evidence_count: 1
files: ["cosmos/lanes.py"]
tags: ["finding", "medium", "charter"]
authors: ["Biswajit Tripathy"]
valid_from: "2026-10-07"
meta_area: "charter"
meta_audit_id: "PROD-c79ef5"
meta_claimed_on: "2026-10-07"
meta_finding_status: "claimed"
meta_found_commit: "d05214c"
meta_locations: "cosmos/lanes.py:115"
meta_raw_id: "c79ef5"
meta_severity: "medium"
meta_source_doc: "manual"
meta_status_at: "2026-10-07"
meta_status_note: "fixed in the main working tree (cosmos/extract.py ANAPHOR, cosmos/lanes.py + charter.py), tests pass, not committed yet"
---

# The Charter check reported dot-prefixed paths and globs as missing

**Category:** finding · **Status:** active · **Confidence:** 90%

## Details
**What** — resolve_evidence stripped every leading dot and slash with lstrip('./'), so .claude/agents/ and .cosmos/cosmosw were looked up as claude/agents/ and cosmos/cosmosw; globs like agents/*.md were never expanded. Reported by the HORIZON session from cosmos doctor.

**Fix** — Strip only a leading ./ (lanes.py), expand globs here and in worktrees (charter._named_path_exists); test test_dotted_paths_and_globs_the_charter_names_are_found.

## Why we believe this
- Observed 1× (first 2026-10-07, last 2026-10-07); source: explicit
- Evidence file: `cosmos/lanes.py`
- Marked claimed on 2026-10-07: fixed in the main working tree (cosmos/extract.py ANAPHOR, cosmos/lanes.py + charter.py), tests pass, not committed yet

## Links
- lane: [horizon](/lanes/horizon.md)

#finding #medium #charter
