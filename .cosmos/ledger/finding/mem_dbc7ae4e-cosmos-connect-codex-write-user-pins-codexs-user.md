---
type: "Finding"
title: "cosmos connect codex --write-user pins Codex's user-level cosmos MCP server to the first repository and never updates it"
description: "cosmos connect codex --write-user pins Codex's user-level cosmos MCP server to the first repository and never updates it"
status: "stable"
generated: {"by": "human:Biswajit Tripathy", "at": "2026-10-01T00:00:00Z"}
sources: [{"resource": "cosmos/connect.py", "title": "connect.py"}]
stale_after: "2027-03-30T00:00:00Z"
links: ["/lanes/cosmos.md", "/finding/mem_0448e271-the-watcher-started-a-dream-every-30-seconds-whi.md", "/finding/mem_07187b11-mcp-entries-cosmos-writes-start-python3-which-do.md", "/finding/mem_1db8264f-a-claude-desktop-mcp-entry-named-cosmos-pinned-t.md", "/finding/mem_498078e0-atlas-page-4-of-8-deep-pass-diagrams-failed-unde.md", "/finding/mem_5790a327-cosmos-connect-with-no-agent-argument-failed-arg.md"]
id: "mem_dbc7ae4e"
aliases: ["mem_dbc7ae4e"]
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
files: ["cosmos/connect.py"]
tags: ["finding", "medium"]
authors: ["Biswajit Tripathy"]
valid_from: "2026-10-01"
meta_audit_id: "PROD-459673"
meta_finding_status: "open"
meta_found_commit: "4222433"
meta_locations: "cosmos/connect.py:86"
meta_raw_id: "459673"
meta_severity: "medium"
meta_source_doc: "manual"
---

# cosmos connect codex --write-user pins Codex's user-level cosmos MCP server to the first repository and never updates it

**Category:** finding · **Status:** active · **Confidence:** 90%

## Details
**What** — write_codex_user_config writes [mcp_servers.cosmos] with an absolute cosmosw path and returns early when the section exists

**Impact** — a Codex user on two cosmos repositories files the second one's facts and flares into the first (same class as the Desktop pin)

**Fix** — name the server per repository (cosmos-<repo>) or start it from the session's cwd; warn in doctor when the entry serves another repo

## Why we believe this
- Observed 1× (first 2026-10-01, last 2026-10-01); source: explicit
- Evidence file: `cosmos/connect.py`
- Imported from manual on 2026-10-01

## Related
- [[mem_0448e271]]
- [[mem_07187b11]]
- [[mem_1db8264f]]
- [[mem_498078e0]]
- [[mem_5790a327]]

## Links
- lane: [cosmos](/lanes/cosmos.md)
- related: [mem_0448e271](/finding/mem_0448e271-the-watcher-started-a-dream-every-30-seconds-whi.md)
- related: [mem_07187b11](/finding/mem_07187b11-mcp-entries-cosmos-writes-start-python3-which-do.md)
- related: [mem_1db8264f](/finding/mem_1db8264f-a-claude-desktop-mcp-entry-named-cosmos-pinned-t.md)
- related: [mem_498078e0](/finding/mem_498078e0-atlas-page-4-of-8-deep-pass-diagrams-failed-unde.md)
- related: [mem_5790a327](/finding/mem_5790a327-cosmos-connect-with-no-agent-argument-failed-arg.md)

#finding #medium
