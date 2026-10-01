---
type: "Finding"
title: "Retent's session briefing (13,326 chars) exceeded Claude Code's 10,000-char hook cap, so sessions saw a 2,000-char previ"
description: "Retent's session briefing (13,326 chars) exceeded Claude Code's 10,000-char hook cap, so sessions saw a 2,000-char preview: most of the Charter and none of the facts"
status: "stable"
generated: {"by": "human:Biswajit Tripathy", "at": "2026-10-01T00:00:00Z"}
sources: [{"resource": "cosmos/hooks.py", "title": "hooks.py"}, {"resource": "cosmos/charter.py", "title": "charter.py"}]
stale_after: "2027-03-30T00:00:00Z"
links: ["/lanes/cosmos.md", "/constraint/mem_1192ca15-hooks-must-always-exit-0-the-gate-is-the-only-de.md", "/constraint/mem_4c8727a1-in-claude-desktop-code-tab-sessions-an-mcp-serve.md", "/constraint/mem_a1b7e320-claude-code-caps-each-hook-text-plain-stdout-add.md", "/decision/mem_55db62b9-recall-is-made-visible-with-the-hooks-systemmess.md", "/finding/mem_07187b11-mcp-entries-cosmos-writes-start-python3-which-do.md"]
id: "mem_cb4bccc1"
aliases: ["mem_cb4bccc1"]
category: "finding"
lane: "cosmos"
cosmos_status: "active"
confidence: 0.9
importance: 0.85
source: "explicit"
created: "2026-10-01"
updated: "2026-10-01"
last_verified: "2026-10-01"
evidence_count: 1
files: ["cosmos/hooks.py", "cosmos/charter.py"]
tags: ["finding", "high"]
authors: ["Biswajit Tripathy"]
valid_from: "2026-10-01"
meta_audit_id: "PROD-43f521"
meta_finding_status: "fixed"
meta_fixed_commit: "df8b7ef"
meta_fixed_on: "2026-10-01"
meta_found_commit: "df8b7ef"
meta_locations: "cosmos/hooks.py \u00b7 cosmos/charter.py:130"
meta_raw_id: "43f521"
meta_severity: "high"
meta_source_doc: "manual"
meta_status_at: "2026-10-01"
meta_status_note: "fixed in the working tree (not pushed): cosmos/charter.py:130, cosmos/hooks.py _fit"
---

# Retent's session briefing (13,326 chars) exceeded Claude Code's 10,000-char hook cap, so sessions saw a 2,000-char preview: most of the Charter and none of the facts

**Category:** finding · **Status:** active · **Confidence:** 90%

## Details
**What** — charter.summary injected the 12 explicit rules in full (8,034 chars; single rules over 1,100)

**Fix** — rules clipped to one 220-char line with id; whole briefing budgeted to 9,000 (_fit); test_a_long_briefing_stays_under_the_hook_cap

## Why we believe this
- Observed 1× (first 2026-10-01, last 2026-10-01); source: explicit
- Evidence file: `cosmos/hooks.py`
- Evidence file: `cosmos/charter.py`
- Marked fixed on 2026-10-01: fixed in the working tree (not pushed): cosmos/charter.py:130, cosmos/hooks.py _fit

## Related
- [[mem_1192ca15]]
- [[mem_4c8727a1]]
- [[mem_a1b7e320]]
- [[mem_55db62b9]]
- [[mem_07187b11]]

## Links
- lane: [cosmos](/lanes/cosmos.md)
- related: [mem_1192ca15](/constraint/mem_1192ca15-hooks-must-always-exit-0-the-gate-is-the-only-de.md)
- related: [mem_4c8727a1](/constraint/mem_4c8727a1-in-claude-desktop-code-tab-sessions-an-mcp-serve.md)
- related: [mem_a1b7e320](/constraint/mem_a1b7e320-claude-code-caps-each-hook-text-plain-stdout-add.md)
- related: [mem_55db62b9](/decision/mem_55db62b9-recall-is-made-visible-with-the-hooks-systemmess.md)
- related: [mem_07187b11](/finding/mem_07187b11-mcp-entries-cosmos-writes-start-python3-which-do.md)

#finding #high
