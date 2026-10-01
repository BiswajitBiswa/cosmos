---
type: "Finding"
title: "A session opened in a subfolder of the repository gets no briefing, facts or capture: load_config takes the folder it is"
description: "A session opened in a subfolder of the repository gets no briefing, facts or capture: load_config takes the folder it is given as the repository root"
status: "stable"
generated: {"by": "human:Biswajit Tripathy", "at": "2026-10-01T00:00:00Z"}
sources: [{"resource": "cosmos/hooks.py", "title": "hooks.py"}, {"resource": "cosmos/config.py", "title": "config.py"}]
stale_after: "2027-03-30T00:00:00Z"
links: ["/lanes/cosmos.md", "/constraint/mem_1192ca15-hooks-must-always-exit-0-the-gate-is-the-only-de.md", "/constraint/mem_4c8727a1-in-claude-desktop-code-tab-sessions-an-mcp-serve.md", "/constraint/mem_a1b7e320-claude-code-caps-each-hook-text-plain-stdout-add.md", "/decision/mem_55db62b9-recall-is-made-visible-with-the-hooks-systemmess.md", "/finding/mem_1db8264f-a-claude-desktop-mcp-entry-named-cosmos-pinned-t.md"]
id: "mem_b9901dfb"
aliases: ["mem_b9901dfb"]
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
files: ["cosmos/hooks.py", "cosmos/config.py"]
tags: ["finding", "medium"]
authors: ["Biswajit Tripathy"]
valid_from: "2026-10-01"
meta_audit_id: "PROD-2e63ea"
meta_finding_status: "open"
meta_found_commit: "a9ecbee"
meta_locations: "cosmos/hooks.py:432 \u00b7 cosmos/config.py"
meta_raw_id: "2e63ea"
meta_severity: "medium"
meta_source_doc: "manual"
---

# A session opened in a subfolder of the repository gets no briefing, facts or capture: load_config takes the folder it is given as the repository root

**Category:** finding · **Status:** active · **Confidence:** 90%

## Details
**What** — handle() calls load_config(CLAUDE_PROJECT_DIR or event cwd); load_config never walks up, so from src/deep it finds no .cosmos/config.json and returns 0 silently. Found building the Codex plugin, whose hook now passes the root itself.

**Fix** — handle: resolve the root with find_repo_root(cwd) (git toplevel, or the nearest parent with .cosmos/) before load_config; test a SessionStart from a subfolder

## Why we believe this
- Observed 1× (first 2026-10-01, last 2026-10-01); source: explicit
- Evidence file: `cosmos/hooks.py`
- Evidence file: `cosmos/config.py`
- Imported from manual on 2026-10-01

## Related
- [[mem_1192ca15]]
- [[mem_4c8727a1]]
- [[mem_a1b7e320]]
- [[mem_55db62b9]]
- [[mem_1db8264f]]

## Links
- lane: [cosmos](/lanes/cosmos.md)
- related: [mem_1192ca15](/constraint/mem_1192ca15-hooks-must-always-exit-0-the-gate-is-the-only-de.md)
- related: [mem_4c8727a1](/constraint/mem_4c8727a1-in-claude-desktop-code-tab-sessions-an-mcp-serve.md)
- related: [mem_a1b7e320](/constraint/mem_a1b7e320-claude-code-caps-each-hook-text-plain-stdout-add.md)
- related: [mem_55db62b9](/decision/mem_55db62b9-recall-is-made-visible-with-the-hooks-systemmess.md)
- related: [mem_1db8264f](/finding/mem_1db8264f-a-claude-desktop-mcp-entry-named-cosmos-pinned-t.md)

#finding #medium
