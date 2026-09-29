---
type: "Finding"
title: "New slash commands reintroduced names retired in 5b289ba: /intake and cosmos_finding / cosmos_intake in command bodies"
description: "New slash commands reintroduced names retired in 5b289ba: /intake and cosmos_finding / cosmos_intake in command bodies"
status: "stable"
generated: {"by": "human:Biswajit Tripathy", "at": "2026-09-29T00:00:00Z"}
sources: [{"resource": "cosmos/commands.py", "title": "commands.py"}, {"resource": "cosmos/render.py", "title": "render.py"}]
stale_after: "2027-03-28T00:00:00Z"
links: ["/lanes/cosmos.md", "/architecture/mem_1f13b61a-slash-commands-for-every-agent-come-from-one-cat.md", "/decision/mem_043ce3de-playbooks-a-repositorys-own-long-form-agent-prom.md", "/finding/mem_10ab2ec4-console-docs-said-horizon-notes-are-saved-in-cos.md", "/finding/mem_d4c37ea1-slack-cards-and-the-slack-report-told-people-to.md"]
id: "mem_fcf6d908"
aliases: ["mem_fcf6d908"]
category: "finding"
lane: "cosmos"
cosmos_status: "active"
confidence: 0.9
importance: 0.45
source: "explicit"
created: "2026-09-29"
updated: "2026-09-29"
last_verified: "2026-09-29"
evidence_count: 1
files: ["cosmos/commands.py", "cosmos/render.py"]
tags: ["finding", "low", "commands"]
authors: ["Biswajit Tripathy"]
valid_from: "2026-09-29"
meta_area: "commands"
meta_audit_id: "DEV-intake-reintroduced"
meta_finding_status: "fixed"
meta_found_commit: "3f80c40"
meta_locations: "`cosmos/commands.py:71` \u00b7 `cosmos/render.py:38`"
meta_raw_id: "intake-reintroduced"
meta_severity: "low"
meta_source_doc: "qa-2026-09-29-commands"
---

# New slash commands reintroduced names retired in 5b289ba: /intake and cosmos_finding / cosmos_intake in command bodies

**Category:** finding · **Status:** active · **Confidence:** 90%

## Details
**What** — The command catalogue named /intake and told agents about cosmos_finding/cosmos_intake, though Intake → Horizon and Findings → Flares were renamed on 2026-09-22.

**Fix** — /horizon; old names only as silent aliases; commands.RETIRED; a renamed command's generated file is removed; TestNoRetiredNames guards it.

## Why we believe this
- Observed 1× (first 2026-09-29, last 2026-09-29); source: explicit
- Evidence file: `cosmos/commands.py`
- Evidence file: `cosmos/render.py`
- Imported from qa-2026-09-29-commands on 2026-09-29

## Related
- [[mem_1f13b61a]]
- [[mem_043ce3de]]
- [[mem_10ab2ec4]]
- [[mem_d4c37ea1]]

## Links
- lane: [cosmos](/lanes/cosmos.md)
- related: [mem_1f13b61a](/architecture/mem_1f13b61a-slash-commands-for-every-agent-come-from-one-cat.md)
- related: [mem_043ce3de](/decision/mem_043ce3de-playbooks-a-repositorys-own-long-form-agent-prom.md)
- related: [mem_10ab2ec4](/finding/mem_10ab2ec4-console-docs-said-horizon-notes-are-saved-in-cos.md)
- related: [mem_d4c37ea1](/finding/mem_d4c37ea1-slack-cards-and-the-slack-report-told-people-to.md)

#finding #low #commands
