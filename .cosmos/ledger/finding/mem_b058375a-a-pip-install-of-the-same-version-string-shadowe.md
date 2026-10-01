---
type: "Finding"
title: "A pip install of the same version string shadowed the repository's newer copy and silently turned off capture and briefi"
description: "A pip install of the same version string shadowed the repository's newer copy and silently turned off capture and briefings for every retent session for about 8 hours"
status: "stable"
generated: {"by": "human:Biswajit Tripathy", "at": "2026-10-01T00:00:00Z"}
sources: [{"resource": "cosmos/wrapper.py", "title": "wrapper.py"}]
stale_after: "2027-03-30T00:00:00Z"
links: ["/lanes/cosmos.md", "/finding/mem_07187b11-mcp-entries-cosmos-writes-start-python3-which-do.md", "/finding/mem_488b620a-every-hook-took-700-790-ms-on-retent-2-925-notes.md", "/finding/mem_5b583e8d-cosmosw-always-prefers-an-installed-cosmos-over.md", "/finding/mem_ac19fa4c-a-whole-ledger-save-from-a-process-that-loaded-e.md", "/finding/mem_b9641884-an-older-pip-install-shadowed-the-repos-cosmos-a.md"]
id: "mem_b058375a"
aliases: ["mem_b058375a"]
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
files: ["cosmos/wrapper.py"]
tags: ["finding", "high"]
authors: ["Biswajit Tripathy"]
valid_from: "2026-10-01"
meta_audit_id: "PROD-ffef5d"
meta_finding_status: "fixed"
meta_fixed_commit: "0c9628f"
meta_fixed_on: "2026-10-01"
meta_found_commit: "0c9628f"
meta_locations: "cosmos/wrapper.py:37"
meta_raw_id: "ffef5d"
meta_severity: "high"
meta_source_doc: "manual"
meta_status_at: "2026-10-01"
meta_status_note: "local commit; retent needs 0.1.6 to recover"
---

# A pip install of the same version string shadowed the repository's newer copy and silently turned off capture and briefings for every retent session for about 8 hours

**Category:** finding · **Status:** active · **Confidence:** 90%

## Details
**What** — cosmosw preferred the installed cosmos on a version tie; PyPI 0.1.5 (without parent-folder support) replaced the editable checkout, so retent hooks from the ideator/ parent folder returned 0 from 09:09Z (hook.log, inject.log)

**Fix** — a tie goes to the repository's copy unless the install is an editable checkout; test_the_repositorys_copy_wins_a_tie_and_a_newer_install_wins

## Why we believe this
- Observed 1× (first 2026-10-01, last 2026-10-01); source: explicit
- Evidence file: `cosmos/wrapper.py`
- Marked fixed on 2026-10-01: local commit; retent needs 0.1.6 to recover

## Related
- [[mem_07187b11]]
- [[mem_488b620a]]
- [[mem_5b583e8d]]
- [[mem_ac19fa4c]]
- [[mem_b9641884]]

## Links
- lane: [cosmos](/lanes/cosmos.md)
- related: [mem_07187b11](/finding/mem_07187b11-mcp-entries-cosmos-writes-start-python3-which-do.md)
- related: [mem_488b620a](/finding/mem_488b620a-every-hook-took-700-790-ms-on-retent-2-925-notes.md)
- related: [mem_5b583e8d](/finding/mem_5b583e8d-cosmosw-always-prefers-an-installed-cosmos-over.md)
- related: [mem_ac19fa4c](/finding/mem_ac19fa4c-a-whole-ledger-save-from-a-process-that-loaded-e.md)
- related: [mem_b9641884](/finding/mem_b9641884-an-older-pip-install-shadowed-the-repos-cosmos-a.md)

#finding #high
