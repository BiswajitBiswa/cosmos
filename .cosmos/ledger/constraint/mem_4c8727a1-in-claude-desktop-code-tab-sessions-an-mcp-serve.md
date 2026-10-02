---
type: "Constraint"
title: "In Claude Desktop Code-tab sessions an MCP server named cosmos in claude_desktop_config.json shadows the project's .mcp."
description: "In Claude Desktop Code-tab sessions an MCP server named cosmos in claude_desktop_config.json shadows the project's .mcp.json server, so cosmos_* tools write to that pinned repository. session_start warns when CLAUDE_CODE_ENTRYPOINT=claude-desktop; agents then record with python3 -m cosmos / .cosmos/cosmosw on the command line."
status: "stable"
generated: {"by": "human:Biswajit Tripathy", "at": "2026-10-01T00:00:00Z"}
sources: [{"resource": "cosmos/hooks.py", "title": "hooks.py"}]
stale_after: "2027-03-30T00:00:00Z"
links: ["/lanes/cosmos.md", "/constraint/mem_1192ca15-hooks-must-always-exit-0-the-gate-is-the-only-de.md", "/constraint/mem_a1b7e320-claude-code-caps-each-hook-text-plain-stdout-add.md", "/decision/mem_55db62b9-recall-is-made-visible-with-the-hooks-systemmess.md", "/finding/mem_0448e271-the-watcher-started-a-dream-every-30-seconds-whi.md", "/finding/mem_a0fa1f2d-several-auto-dreams-ran-at-once-in-one-repositor.md"]
id: "mem_4c8727a1"
aliases: ["mem_4c8727a1"]
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
files: ["cosmos/hooks.py"]
authors: ["Biswajit Tripathy"]
valid_from: "2026-10-01"
---

# In Claude Desktop Code-tab sessions an MCP server named cosmos in claude_desktop_config.json shadows the project's .mcp.json server, so cosmos_* tools write to that pinned repository. session_start warns when CLAUDE_CODE_ENTRYPOINT=claude-desktop; agents then record with python3 -m cosmos / .cosmos/cosmosw on the command line.

**Category:** constraint · **Status:** active · **Confidence:** 95%

## Why we believe this
- Observed 1× (first 2026-10-01, last 2026-10-01); source: explicit
- Evidence file: `cosmos/hooks.py`

## Related
- [[mem_1192ca15]]
- [[mem_a1b7e320]]
- [[mem_55db62b9]]
- [[mem_0448e271]]
- [[mem_a0fa1f2d]]

## Links
- lane: [cosmos](/lanes/cosmos.md)
- related: [mem_1192ca15](/constraint/mem_1192ca15-hooks-must-always-exit-0-the-gate-is-the-only-de.md)
- related: [mem_a1b7e320](/constraint/mem_a1b7e320-claude-code-caps-each-hook-text-plain-stdout-add.md)
- related: [mem_55db62b9](/decision/mem_55db62b9-recall-is-made-visible-with-the-hooks-systemmess.md)
- related: [mem_0448e271](/finding/mem_0448e271-the-watcher-started-a-dream-every-30-seconds-whi.md)
- related: [mem_a0fa1f2d](/finding/mem_a0fa1f2d-several-auto-dreams-ran-at-once-in-one-repositor.md)
