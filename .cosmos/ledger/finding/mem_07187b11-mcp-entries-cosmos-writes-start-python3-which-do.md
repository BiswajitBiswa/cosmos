---
type: "Finding"
title: "MCP entries cosmos writes start python3, which does not exist on Windows, so the cosmos tools never start there"
description: "MCP entries cosmos writes start python3, which does not exist on Windows, so the cosmos tools never start there"
status: "stable"
generated: {"by": "human:Biswajit Tripathy", "at": "2026-10-01T00:00:00Z"}
sources: [{"resource": "cosmos/connect.py", "title": "connect.py"}]
stale_after: "2027-03-30T00:00:00Z"
links: ["/lanes/cosmos.md", "/finding/mem_488b620a-every-hook-took-700-790-ms-on-retent-2-925-notes.md", "/finding/mem_ac19fa4c-a-whole-ledger-save-from-a-process-that-loaded-e.md", "/finding/mem_b058375a-a-pip-install-of-the-same-version-string-shadowe.md", "/finding/mem_cb4bccc1-retents-session-briefing-13-326-chars-exceeded-c.md", "/finding/mem_dbc7ae4e-cosmos-connect-codex-write-user-pins-codexs-user.md"]
id: "mem_07187b11"
aliases: ["mem_07187b11"]
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
files: ["cosmos/connect.py"]
tags: ["finding", "high"]
authors: ["Biswajit Tripathy"]
valid_from: "2026-10-01"
meta_audit_id: "PROD-048c42"
meta_finding_status: "open"
meta_found_commit: "bd7c31a"
meta_locations: "cosmos/connect.py:41"
meta_raw_id: "048c42"
meta_severity: "high"
meta_source_doc: "manual"
---

# MCP entries cosmos writes start python3, which does not exist on Windows, so the cosmos tools never start there

**Category:** finding · **Status:** active · **Confidence:** 90%

## Details
**What** — mcp_server_entry hard-codes command python3 for .mcp.json, Cursor, Gemini and Codex's config.toml; Windows installs python / py

**Fix** — write sys.executable (or py -3 on Windows) when connecting; doctor checks the command resolves

## Why we believe this
- Observed 1× (first 2026-10-01, last 2026-10-01); source: explicit
- Evidence file: `cosmos/connect.py`
- Imported from manual on 2026-10-01

## Related
- [[mem_488b620a]]
- [[mem_ac19fa4c]]
- [[mem_b058375a]]
- [[mem_cb4bccc1]]
- [[mem_dbc7ae4e]]

## Links
- lane: [cosmos](/lanes/cosmos.md)
- related: [mem_488b620a](/finding/mem_488b620a-every-hook-took-700-790-ms-on-retent-2-925-notes.md)
- related: [mem_ac19fa4c](/finding/mem_ac19fa4c-a-whole-ledger-save-from-a-process-that-loaded-e.md)
- related: [mem_b058375a](/finding/mem_b058375a-a-pip-install-of-the-same-version-string-shadowe.md)
- related: [mem_cb4bccc1](/finding/mem_cb4bccc1-retents-session-briefing-13-326-chars-exceeded-c.md)
- related: [mem_dbc7ae4e](/finding/mem_dbc7ae4e-cosmos-connect-codex-write-user-pins-codexs-user.md)

#finding #high
