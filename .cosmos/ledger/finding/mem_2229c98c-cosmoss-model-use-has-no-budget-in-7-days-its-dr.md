---
type: "Finding"
title: "cosmos's model use has no budget: in 7 days its dreams made 57 model runs through the user's Claude login and read 6,290"
description: "cosmos's model use has no budget: in 7 days its dreams made 57 model runs through the user's Claude login and read 6,290 session turns, likely exhausting the weekly limit"
status: "stable"
generated: {"by": "human:Biswajit Tripathy", "at": "2026-10-03T00:00:00Z"}
sources: [{"resource": "cosmos/dream.py", "title": "dream.py"}, {"resource": "cosmos/providers.py", "title": "providers.py"}]
stale_after: "2027-04-01T00:00:00Z"
links: ["/lanes/cosmos.md", "/finding/mem_0b83670f-a-session-in-a-project-without-cosmos-filed-its.md", "/finding/mem_93255725-cosmosremember-and-cosmosflare-took-40-48-s-on-r.md", "/finding/mem_a0fa1f2d-several-auto-dreams-ran-at-once-in-one-repositor.md", "/finding/mem_ac19fa4c-a-whole-ledger-save-from-a-process-that-loaded-e.md", "/finding/mem_fcae919e-a-dream-that-started-before-cosmos-was-updated-r.md"]
id: "mem_2229c98c"
aliases: ["mem_2229c98c"]
category: "finding"
lane: "cosmos"
cosmos_status: "active"
confidence: 0.9
importance: 1.0
source: "explicit"
created: "2026-10-03"
updated: "2026-10-03"
last_verified: "2026-10-03"
evidence_count: 1
files: ["cosmos/dream.py", "cosmos/providers.py"]
tags: ["finding", "critical"]
authors: ["Biswajit Tripathy"]
valid_from: "2026-10-03"
meta_audit_id: "PROD-f488dd"
meta_finding_status: "open"
meta_found_commit: "0144d43"
meta_locations: "cosmos/dream.py \u00b7 cosmos/providers.py"
meta_raw_id: "f488dd"
meta_severity: "critical"
meta_source_doc: "manual"
---

# cosmos's model use has no budget: in 7 days its dreams made 57 model runs through the user's Claude login and read 6,290 session turns, likely exhausting the weekly limit

**Category:** finding · **Status:** active · **Confidence:** 90%

## Details
**What** — retent 35 model dreams / 5,674 turns (five ran at once on 2026-10-02), rms-backend 21 / 616, retent-site 1; each claude -p call counts against the same weekly limit as the user's own sessions; the Atlas deep pass ignored COSMOS_LLM_PROVIDER=none

**Fix** — paused by the owner (COSMOS_LLM_PROVIDER=none in ~/.claude/settings.json env); deep pass now honours the switch; next: a weekly model budget (estimated tokens, default low), model dreams only in the main checkout, usage shown in cosmos pulse

## Why we believe this
- Observed 1× (first 2026-10-03, last 2026-10-03); source: explicit
- Evidence file: `cosmos/dream.py`
- Evidence file: `cosmos/providers.py`
- Imported from manual on 2026-10-03

## Related
- [[mem_0b83670f]]
- [[mem_93255725]]
- [[mem_a0fa1f2d]]
- [[mem_ac19fa4c]]
- [[mem_fcae919e]]

## Links
- lane: [cosmos](/lanes/cosmos.md)
- related: [mem_0b83670f](/finding/mem_0b83670f-a-session-in-a-project-without-cosmos-filed-its.md)
- related: [mem_93255725](/finding/mem_93255725-cosmosremember-and-cosmosflare-took-40-48-s-on-r.md)
- related: [mem_a0fa1f2d](/finding/mem_a0fa1f2d-several-auto-dreams-ran-at-once-in-one-repositor.md)
- related: [mem_ac19fa4c](/finding/mem_ac19fa4c-a-whole-ledger-save-from-a-process-that-loaded-e.md)
- related: [mem_fcae919e](/finding/mem_fcae919e-a-dream-that-started-before-cosmos-was-updated-r.md)

#finding #critical
