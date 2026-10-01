---
type: "Finding"
title: "Claude Desktop's MCP entry named cosmos silently sent cosmos_remember/cosmos_flare from every Desktop session to one rep"
description: "Claude Desktop's MCP entry named cosmos silently sent cosmos_remember/cosmos_flare from every Desktop session to one repository"
status: "stable"
generated: {"by": "human:Biswajit Tripathy", "at": "2026-10-01T00:00:00Z"}
sources: [{"resource": "cosmos/hooks.py", "title": "hooks.py"}, {"resource": "cosmos/connect.py", "title": "connect.py"}]
stale_after: "2027-03-30T00:00:00Z"
links: ["/lanes/cosmos.md", "/constraint/mem_1192ca15-hooks-must-always-exit-0-the-gate-is-the-only-de.md", "/constraint/mem_4c8727a1-in-claude-desktop-code-tab-sessions-an-mcp-serve.md", "/constraint/mem_a1b7e320-claude-code-caps-each-hook-text-plain-stdout-add.md", "/decision/mem_55db62b9-recall-is-made-visible-with-the-hooks-systemmess.md", "/finding/mem_07187b11-mcp-entries-cosmos-writes-start-python3-which-do.md"]
id: "mem_f87f2319"
aliases: ["mem_f87f2319"]
category: "finding"
lane: "cosmos"
cosmos_status: "active"
confidence: 0.9
importance: 0.65
source: "explicit"
created: "2026-10-01"
updated: "2026-10-01"
last_verified: "2026-10-01"
evidence_count: 1
files: ["cosmos/hooks.py", "cosmos/connect.py"]
tags: ["finding", "medium"]
authors: ["Biswajit Tripathy"]
valid_from: "2026-10-01"
meta_audit_id: "PROD-2d46da"
meta_finding_status: "fixed"
meta_fixed_commit: "4222433"
meta_fixed_on: "2026-10-01"
meta_found_commit: "4222433"
meta_locations: "cosmos/hooks.py:242 \u00b7 cosmos/connect.py:23"
meta_raw_id: "2d46da"
meta_severity: "medium"
meta_source_doc: "manual"
meta_status_at: "2026-10-01"
meta_status_note: "fixed in the working tree (uncommitted): session_start warning cosmos/hooks.py:242; the owner renames the Desktop entry"
---

# Claude Desktop's MCP entry named cosmos silently sent cosmos_remember/cosmos_flare from every Desktop session to one repository

**Category:** finding · **Status:** active · **Confidence:** 90%

## Details
**What** — claude_desktop_config.json pinned 'cosmos' to retent/.cosmos/cosmosw; in Code-tab sessions it shadows the project's .mcp.json server. Only cosmos doctor warned, which autopilot never runs; a flare and a fact from the cosmos repo landed in retent's ledger

**Impact** — facts and flares filed into the wrong repository's committed ledger

**Fix** — session_start warns first thing when CLAUDE_CODE_ENTRYPOINT=claude-desktop and the entry serves another repo, and points to the CLI; test_a_desktop_session_is_told_its_cosmos_tools_write_elsewhere

## Why we believe this
- Observed 1× (first 2026-10-01, last 2026-10-01); source: explicit
- Evidence file: `cosmos/hooks.py`
- Evidence file: `cosmos/connect.py`
- Marked fixed on 2026-10-01: fixed in the working tree (uncommitted): session_start warning cosmos/hooks.py:242; the owner renames the Desktop entry

## Related
- [[mem_1192ca15]]
- [[mem_4c8727a1]]
- [[mem_a1b7e320]]
- [[mem_55db62b9]]
- [[mem_07187b11]]

## Links
- lane: [cosmos](/lanes/cosmos.md)
- related: [mem_1192ca15](/constraint/mem_1192ca15-hooks-must-always-exit-0-the-gate-is-the-only-de.md)
- related: [mem_4c8727a1](/constraint/mem_4c8727a1-in-claude-desktop-code-tab-sessions-an-mcp-serve.md)
- related: [mem_a1b7e320](/constraint/mem_a1b7e320-claude-code-caps-each-hook-text-plain-stdout-add.md)
- related: [mem_55db62b9](/decision/mem_55db62b9-recall-is-made-visible-with-the-hooks-systemmess.md)
- related: [mem_07187b11](/finding/mem_07187b11-mcp-entries-cosmos-writes-start-python3-which-do.md)

#finding #medium
