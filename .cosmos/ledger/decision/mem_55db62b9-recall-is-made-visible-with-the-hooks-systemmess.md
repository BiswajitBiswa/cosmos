---
type: "Decision"
title: "Recall is made visible with the hook's systemMessage: SessionStart, UserPromptSubmit and PreToolUse print JSON with a on"
description: "Recall is made visible with the hook's systemMessage: SessionStart, UserPromptSubmit and PreToolUse print JSON with a one-line cosm\u25ces notice for the person and the context in hookSpecificOutput.additionalContext (cosmos/hooks.py _say/notice). Codex (COSMOS_AGENT=codex) gets plain text; ui.notices false turns the line off. Claude Code's own 'Recalled a memory' chip has no documented way for a tool to contribute. Reason: the owner saw Claude's memory recalls but never cosmos's."
status: "stable"
generated: {"by": "human:Biswajit Tripathy", "at": "2026-10-01T00:00:00Z"}
sources: [{"resource": "cosmos/hooks.py", "title": "hooks.py"}]
stale_after: "2027-03-30T00:00:00Z"
links: ["/lanes/cosmos.md", "/constraint/mem_1192ca15-hooks-must-always-exit-0-the-gate-is-the-only-de.md", "/constraint/mem_4c8727a1-in-claude-desktop-code-tab-sessions-an-mcp-serve.md", "/constraint/mem_a1b7e320-claude-code-caps-each-hook-text-plain-stdout-add.md", "/finding/mem_b9901dfb-a-session-opened-in-a-subfolder-of-the-repositor.md", "/finding/mem_cb4bccc1-retents-session-briefing-13-326-chars-exceeded-c.md"]
id: "mem_55db62b9"
aliases: ["mem_55db62b9"]
category: "decision"
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

# Recall is made visible with the hook's systemMessage: SessionStart, UserPromptSubmit and PreToolUse print JSON with a one-line cosm◎s notice for the person and the context in hookSpecificOutput.additionalContext (cosmos/hooks.py _say/notice). Codex (COSMOS_AGENT=codex) gets plain text; ui.notices false turns the line off. Claude Code's own 'Recalled a memory' chip has no documented way for a tool to contribute. Reason: the owner saw Claude's memory recalls but never cosmos's.

**Category:** decision · **Status:** active · **Confidence:** 95%

## Why we believe this
- Observed 1× (first 2026-10-01, last 2026-10-01); source: explicit
- Evidence file: `cosmos/hooks.py`

## Related
- [[mem_1192ca15]]
- [[mem_4c8727a1]]
- [[mem_a1b7e320]]
- [[mem_b9901dfb]]
- [[mem_cb4bccc1]]

## Links
- lane: [cosmos](/lanes/cosmos.md)
- related: [mem_1192ca15](/constraint/mem_1192ca15-hooks-must-always-exit-0-the-gate-is-the-only-de.md)
- related: [mem_4c8727a1](/constraint/mem_4c8727a1-in-claude-desktop-code-tab-sessions-an-mcp-serve.md)
- related: [mem_a1b7e320](/constraint/mem_a1b7e320-claude-code-caps-each-hook-text-plain-stdout-add.md)
- related: [mem_b9901dfb](/finding/mem_b9901dfb-a-session-opened-in-a-subfolder-of-the-repositor.md)
- related: [mem_cb4bccc1](/finding/mem_cb4bccc1-retents-session-briefing-13-326-chars-exceeded-c.md)
