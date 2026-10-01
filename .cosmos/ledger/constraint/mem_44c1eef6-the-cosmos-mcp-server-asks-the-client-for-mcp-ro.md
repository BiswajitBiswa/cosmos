---
type: "Constraint"
title: "The cosmos MCP server asks the client for MCP roots after the handshake (Claude Code 2.1.118 declares roots and answers "
description: "The cosmos MCP server asks the client for MCP roots after the handshake (Claude Code 2.1.118 declares roots and answers roots/list with the session's project folder, verified 2026-10-01). When no root is the repository or a folder above it, every tool returns 'not this project' and nothing is read or recorded (cosmos/mcp.py foreign_session); clients that send no roots are served as before. Reason: a global Desktop MCP entry filed another project's critical bug into retent."
status: "stable"
generated: {"by": "human:Biswajit Tripathy", "at": "2026-10-01T00:00:00Z"}
sources: [{"resource": "cosmos/mcp.py", "title": "mcp.py"}]
stale_after: "2027-03-30T00:00:00Z"
links: ["/lanes/cosmos.md", "/finding/mem_0b83670f-a-session-in-a-project-without-cosmos-filed-its.md"]
id: "mem_44c1eef6"
aliases: ["mem_44c1eef6"]
category: "constraint"
lane: "cosmos"
cosmos_status: "active"
confidence: 0.95
importance: 0.95
source: "explicit"
created: "2026-10-01"
updated: "2026-10-01"
last_verified: "2026-10-01"
evidence_count: 1
files: ["cosmos/mcp.py"]
authors: ["Biswajit Tripathy"]
valid_from: "2026-10-01"
---

# The cosmos MCP server asks the client for MCP roots after the handshake (Claude Code 2.1.118 declares roots and answers roots/list with the session's project folder, verified 2026-10-01). When no root is the repository or a folder above it, every tool returns 'not this project' and nothing is read or recorded (cosmos/mcp.py foreign_session); clients that send no roots are served as before. Reason: a global Desktop MCP entry filed another project's critical bug into retent.

**Category:** constraint · **Status:** active · **Confidence:** 95%

## Why we believe this
- Observed 1× (first 2026-10-01, last 2026-10-01); source: explicit
- Evidence file: `cosmos/mcp.py`

## Related
- [[mem_0b83670f]]

## Links
- lane: [cosmos](/lanes/cosmos.md)
- related: [mem_0b83670f](/finding/mem_0b83670f-a-session-in-a-project-without-cosmos-filed-its.md)
