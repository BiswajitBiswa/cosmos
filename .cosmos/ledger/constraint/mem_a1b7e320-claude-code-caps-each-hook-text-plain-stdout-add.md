---
type: "Constraint"
title: "Claude Code caps each hook text (plain stdout, additionalContext, systemMessage) at 10,000 characters; longer text is sa"
description: "Claude Code caps each hook text (plain stdout, additionalContext, systemMessage) at 10,000 characters; longer text is saved to a file and the model sees only a 2,000-character preview it is not asked to read. So session_start keeps the briefing under retrieval.session_start_chars (9,000) via _fit, and each explicit rule in the Charter summary is one 220-character line with its id. Measured 2026-10-01: retent's briefing was 13,326 chars (12 rules = 8,034), now 8,157."
status: "stable"
generated: {"by": "human:Biswajit Tripathy", "at": "2026-10-01T00:00:00Z"}
sources: [{"resource": "cosmos/hooks.py", "title": "hooks.py"}]
stale_after: "2027-03-30T00:00:00Z"
links: ["/lanes/cosmos.md", "/constraint/mem_1192ca15-hooks-must-always-exit-0-the-gate-is-the-only-de.md", "/constraint/mem_4c8727a1-in-claude-desktop-code-tab-sessions-an-mcp-serve.md", "/decision/mem_55db62b9-recall-is-made-visible-with-the-hooks-systemmess.md", "/finding/mem_0448e271-the-watcher-started-a-dream-every-30-seconds-whi.md", "/finding/mem_a0fa1f2d-several-auto-dreams-ran-at-once-in-one-repositor.md"]
id: "mem_a1b7e320"
aliases: ["mem_a1b7e320"]
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

# Claude Code caps each hook text (plain stdout, additionalContext, systemMessage) at 10,000 characters; longer text is saved to a file and the model sees only a 2,000-character preview it is not asked to read. So session_start keeps the briefing under retrieval.session_start_chars (9,000) via _fit, and each explicit rule in the Charter summary is one 220-character line with its id. Measured 2026-10-01: retent's briefing was 13,326 chars (12 rules = 8,034), now 8,157.

**Category:** constraint · **Status:** active · **Confidence:** 95%

## Why we believe this
- Observed 1× (first 2026-10-01, last 2026-10-01); source: explicit
- Evidence file: `cosmos/hooks.py`

## Related
- [[mem_1192ca15]]
- [[mem_4c8727a1]]
- [[mem_55db62b9]]
- [[mem_0448e271]]
- [[mem_a0fa1f2d]]

## Links
- lane: [cosmos](/lanes/cosmos.md)
- related: [mem_1192ca15](/constraint/mem_1192ca15-hooks-must-always-exit-0-the-gate-is-the-only-de.md)
- related: [mem_4c8727a1](/constraint/mem_4c8727a1-in-claude-desktop-code-tab-sessions-an-mcp-serve.md)
- related: [mem_55db62b9](/decision/mem_55db62b9-recall-is-made-visible-with-the-hooks-systemmess.md)
- related: [mem_0448e271](/finding/mem_0448e271-the-watcher-started-a-dream-every-30-seconds-whi.md)
- related: [mem_a0fa1f2d](/finding/mem_a0fa1f2d-several-auto-dreams-ran-at-once-in-one-repositor.md)
