---
type: "Constraint"
title: "Hooks must always exit 0; the Gate is the only deliberate exit-2 and it never fires twice in one turn (stop_hook_active)"
description: "Hooks must always exit 0; the Gate is the only deliberate exit-2 and it never fires twice in one turn (stop_hook_active)."
status: "stable"
generated: {"by": "human:Biswajit Tripathy", "at": "2026-09-21T00:00:00Z"}
sources: [{"resource": "cosmos/hooks.py", "title": "hooks.py"}, {"resource": "cosmos/gate.py", "title": "gate.py"}]
stale_after: "2027-03-20T00:00:00Z"
links: ["/lanes/cosmos.md"]
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

## Links
- lane: [cosmos](/lanes/cosmos.md)
