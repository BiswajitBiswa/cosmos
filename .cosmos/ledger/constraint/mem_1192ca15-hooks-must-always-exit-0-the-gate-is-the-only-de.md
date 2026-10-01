---
type: "Constraint"
title: "Hooks must always exit 0; the Gate is the only deliberate exit-2 and it never fires twice in one turn (stop_hook_active)"
description: "Hooks must always exit 0; the Gate is the only deliberate exit-2 and it never fires twice in one turn (stop_hook_active)."
status: "stable"
generated: {"by": "human:Biswajit Tripathy", "at": "2026-09-21T00:00:00Z"}
sources: [{"resource": "cosmos/hooks.py", "title": "hooks.py"}, {"resource": "cosmos/gate.py", "title": "gate.py"}]
stale_after: "2027-03-20T00:00:00Z"
links: ["/lanes/cosmos.md", "/constraint/mem_4c8727a1-in-claude-desktop-code-tab-sessions-an-mcp-serve.md", "/constraint/mem_a1b7e320-claude-code-caps-each-hook-text-plain-stdout-add.md", "/decision/mem_55db62b9-recall-is-made-visible-with-the-hooks-systemmess.md", "/finding/mem_0448e271-the-watcher-started-a-dream-every-30-seconds-whi.md", "/finding/mem_b9901dfb-a-session-opened-in-a-subfolder-of-the-repositor.md"]
id: "mem_1192ca15"
aliases: ["mem_1192ca15"]
category: "constraint"
lane: "cosmos"
cosmos_status: "active"
confidence: 0.95
importance: 0.95
source: "explicit"
created: "2026-09-21"
updated: "2026-09-21"
last_verified: "2026-09-21"
evidence_count: 1
files: ["cosmos/hooks.py", "cosmos/gate.py"]
authors: ["Biswajit Tripathy"]
valid_from: "2026-09-21"
---

# Hooks must always exit 0; the Gate is the only deliberate exit-2 and it never fires twice in one turn (stop_hook_active).

**Category:** constraint · **Status:** active · **Confidence:** 95%

## Why we believe this
- Observed 1× (first 2026-09-21, last 2026-09-21); source: explicit
- Evidence file: `cosmos/hooks.py`
- Evidence file: `cosmos/gate.py`

## Related
- [[mem_4c8727a1]]
- [[mem_a1b7e320]]
- [[mem_55db62b9]]
- [[mem_0448e271]]
- [[mem_b9901dfb]]

## Links
- lane: [cosmos](/lanes/cosmos.md)
- related: [mem_4c8727a1](/constraint/mem_4c8727a1-in-claude-desktop-code-tab-sessions-an-mcp-serve.md)
- related: [mem_a1b7e320](/constraint/mem_a1b7e320-claude-code-caps-each-hook-text-plain-stdout-add.md)
- related: [mem_55db62b9](/decision/mem_55db62b9-recall-is-made-visible-with-the-hooks-systemmess.md)
- related: [mem_0448e271](/finding/mem_0448e271-the-watcher-started-a-dream-every-30-seconds-whi.md)
- related: [mem_b9901dfb](/finding/mem_b9901dfb-a-session-opened-in-a-subfolder-of-the-repositor.md)
