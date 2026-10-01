---
type: "Finding"
title: "A session in a project without cosmos filed its bug into retent's ledger through Claude Desktop's global cosmos MCP entr"
description: "A session in a project without cosmos filed its bug into retent's ledger through Claude Desktop's global cosmos MCP entry (RET-WATERFALL-cabf52, Odin LogMasker)"
status: "stable"
generated: {"by": "human:Biswajit Tripathy", "at": "2026-10-01T00:00:00Z"}
sources: [{"resource": "cosmos/mcp.py", "title": "mcp.py"}]
stale_after: "2027-03-30T00:00:00Z"
links: ["/lanes/cosmos.md", "/constraint/mem_44c1eef6-the-cosmos-mcp-server-asks-the-client-for-mcp-ro.md", "/finding/mem_93255725-cosmosremember-and-cosmosflare-took-40-48-s-on-r.md"]
id: "mem_0b83670f"
aliases: ["mem_0b83670f"]
category: "finding"
lane: "cosmos"
cosmos_status: "active"
confidence: 0.9
importance: 1.0
source: "explicit"
created: "2026-10-01"
updated: "2026-10-01"
last_verified: "2026-10-01"
evidence_count: 1
files: ["cosmos/mcp.py"]
tags: ["finding", "critical"]
authors: ["Biswajit Tripathy"]
valid_from: "2026-10-01"
meta_audit_id: "PROD-8f82b0"
meta_finding_status: "fixed"
meta_fixed_commit: "cc68916"
meta_fixed_on: "2026-10-01"
meta_found_commit: "cc68916"
meta_locations: "cosmos/mcp.py"
meta_raw_id: "8f82b0"
meta_severity: "critical"
meta_source_doc: "manual"
meta_status_at: "2026-10-01"
meta_status_note: "cosmos/mcp.py foreign_session (local, not pushed); live machines get it with the next release"
---

# A session in a project without cosmos filed its bug into retent's ledger through Claude Desktop's global cosmos MCP entry (RET-WATERFALL-cabf52, Odin LogMasker)

**Category:** finding · **Status:** active · **Confidence:** 90%

## Details
**What** — the global entry is offered to every Desktop session; with no .cosmos in that project there was no briefing warning, and the tool reply did not name the repository

**Fix** — serve() asks the client for MCP roots and refuses every tool when no root is the repository or above it (foreign_session); writes name the repository; a flare naming only files the repository lacks gets a warning; misfiled flare withdrawn in retent

## Why we believe this
- Observed 1× (first 2026-10-01, last 2026-10-01); source: explicit
- Evidence file: `cosmos/mcp.py`
- Marked fixed on 2026-10-01: cosmos/mcp.py foreign_session (local, not pushed); live machines get it with the next release

## Related
- [[mem_44c1eef6]]
- [[mem_93255725]]

## Links
- lane: [cosmos](/lanes/cosmos.md)
- related: [mem_44c1eef6](/constraint/mem_44c1eef6-the-cosmos-mcp-server-asks-the-client-for-mcp-ro.md)
- related: [mem_93255725](/finding/mem_93255725-cosmosremember-and-cosmosflare-took-40-48-s-on-r.md)

#finding #critical
