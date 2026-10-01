---
type: "Finding"
title: "A Claude Desktop MCP entry named cosmos pinned to one repo sends every Desktop session's cosmos_remember/cosmos_flare to"
description: "A Claude Desktop MCP entry named cosmos pinned to one repo sends every Desktop session's cosmos_remember/cosmos_flare to that repo's ledger"
status: "stable"
generated: {"by": "human:Biswajit Tripathy", "at": "2026-09-29T00:00:00Z"}
sources: [{"resource": "cosmos/cli.py", "title": "cli.py"}]
stale_after: "2027-03-28T00:00:00Z"
links: ["/lanes/cosmos.md", "/decision/mem_5cfd6c9b-commit-note-by-biswajit-tripathy-autopilot-from.md", "/finding/mem_498078e0-atlas-page-4-of-8-deep-pass-diagrams-failed-unde.md", "/finding/mem_5790a327-cosmos-connect-with-no-agent-argument-failed-arg.md", "/finding/mem_5b583e8d-cosmosw-always-prefers-an-installed-cosmos-over.md", "/finding/mem_6fa48630-a-repository-whose-committed-hook-command-is-old.md"]
id: "mem_1db8264f"
aliases: ["mem_1db8264f"]
category: "finding"
lane: "cosmos"
cosmos_status: "active"
confidence: 0.9
importance: 0.65
source: "explicit"
created: "2026-09-29"
updated: "2026-09-29"
last_verified: "2026-09-29"
evidence_count: 1
files: ["cosmos/cli.py"]
tags: ["finding", "medium"]
authors: ["Biswajit Tripathy"]
valid_from: "2026-09-29"
meta_audit_id: "DEV-desktop-mcp-pinned"
meta_finding_status: "fixed"
meta_fixed_commit: "0c11381"
meta_fixed_on: "2026-09-29"
meta_found_commit: "3f80c40"
meta_locations: "`cosmos/cli.py:302`"
meta_raw_id: "desktop-mcp-pinned"
meta_severity: "medium"
meta_source_doc: "session-2026-09-29"
meta_status_at: "2026-09-29"
meta_status_note: "desktop entry renamed cosmos-retent on this machine; doctor names a pinned entry; connect advises cosmos-<repo>"
---

# A Claude Desktop MCP entry named cosmos pinned to one repo sends every Desktop session's cosmos_remember/cosmos_flare to that repo's ledger

**Category:** finding · **Status:** active · **Confidence:** 90%

## Details
**What** — ~/Library/Application Support/Claude/claude_desktop_config.json has cosmos → retent/.cosmos/cosmosw mcp (absolute). In a Desktop session on the cosmos repo, mcp__cosmos__* wrote facts and flares into retent (seen 2026-09-29). `cosmos connect` tells people to add this entry under Settings → Connectors.

**Fix** — Point the Desktop entry at plugin/bin/cosmos-mcp (finds the repository from the session's project dir / cwd) instead of one repo's cosmosw, change the connect hint, and have doctor warn when the Desktop config pins a different repo.

## Why we believe this
- Observed 1× (first 2026-09-29, last 2026-09-29); source: explicit
- Evidence file: `cosmos/cli.py`
- Marked fixed on 2026-09-29: desktop entry renamed cosmos-retent on this machine; doctor names a pinned entry; connect advises cosmos-<repo>

## Related
- [[mem_5cfd6c9b]]
- [[mem_498078e0]]
- [[mem_5790a327]]
- [[mem_5b583e8d]]
- [[mem_6fa48630]]

## Links
- lane: [cosmos](/lanes/cosmos.md)
- related: [mem_5cfd6c9b](/decision/mem_5cfd6c9b-commit-note-by-biswajit-tripathy-autopilot-from.md)
- related: [mem_498078e0](/finding/mem_498078e0-atlas-page-4-of-8-deep-pass-diagrams-failed-unde.md)
- related: [mem_5790a327](/finding/mem_5790a327-cosmos-connect-with-no-agent-argument-failed-arg.md)
- related: [mem_5b583e8d](/finding/mem_5b583e8d-cosmosw-always-prefers-an-installed-cosmos-over.md)
- related: [mem_6fa48630](/finding/mem_6fa48630-a-repository-whose-committed-hook-command-is-old.md)

#finding #medium
