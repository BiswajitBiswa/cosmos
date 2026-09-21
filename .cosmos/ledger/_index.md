---
tags: ["cosmos", "moc"]
---

# Ledger index

2 memories · 2 active · 0 contradicted · 0 stale candidates · 2 lanes

Charter: [[charter]] · Atlas: [[inventory]] · [[containers]] · [[deployment]] · [[api]]

## Lane · cosmos
### Constraint
- [[mem_1192ca15-hooks-must-always-exit-0-the-gate-is-the-only-de|Hooks must always exit 0; the Gate is the only deliberate exit-2 and it never fires twice in one turn (stop_hook_active).]]

## Lane · general
### Constraint
- [[mem_6381abbc-cosmos-is-stdlib-only-the-anthropic-sdk-is-an-op|cosmos is stdlib-only; the anthropic SDK is an optional extra and every feature must work without it.]]
