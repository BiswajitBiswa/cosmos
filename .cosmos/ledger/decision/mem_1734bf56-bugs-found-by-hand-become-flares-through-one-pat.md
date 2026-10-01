---
type: "Decision"
title: "Bugs found by hand become flares through one path: cosmos/audit.py import_items (also used by the JSON import and cosmos"
description: "Bugs found by hand become flares through one path: cosmos/audit.py import_items (also used by the JSON import and cosmos_flare). cosmos flares add (typed, --from .txt/.csv/.tsv/.xlsx/.json/-) and the console's Record bugs (POST flares_add) both call record_bugs. A sheet row carrying an id whose status is open never regresses a closed flare (an old export predates the fix); 'reopen' does. A list that names no severity keeps the known one. Reason: the owner and a teammate collected bugs by hand and had no way to record them."
status: "stable"
generated: {"by": "human:Biswajit Tripathy", "at": "2026-10-01T00:00:00Z"}
sources: [{"resource": "cosmos/audit.py", "title": "audit.py"}]
stale_after: "2027-03-30T00:00:00Z"
links: ["/lanes/cosmos.md", "/decision/mem_2b049e3f-a-flares-id-prefix-is-the-projects-lifecycle-sta.md", "/finding/mem_d4c37ea1-slack-cards-and-the-slack-report-told-people-to.md", "/decision/mem_5cfd6c9b-commit-note-by-biswajit-tripathy-autopilot-from.md"]
id: "mem_1734bf56"
aliases: ["mem_1734bf56"]
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
files: ["cosmos/audit.py"]
authors: ["Biswajit Tripathy"]
valid_from: "2026-10-01"
---

# Bugs found by hand become flares through one path: cosmos/audit.py import_items (also used by the JSON import and cosmos_flare). cosmos flares add (typed, --from .txt/.csv/.tsv/.xlsx/.json/-) and the console's Record bugs (POST flares_add) both call record_bugs. A sheet row carrying an id whose status is open never regresses a closed flare (an old export predates the fix); 'reopen' does. A list that names no severity keeps the known one. Reason: the owner and a teammate collected bugs by hand and had no way to record them.

**Category:** decision · **Status:** active · **Confidence:** 95%

## Why we believe this
- Observed 1× (first 2026-10-01, last 2026-10-01); source: explicit
- Evidence file: `cosmos/audit.py`

## Related
- [[mem_2b049e3f]]
- [[mem_d4c37ea1]]
- [[mem_5cfd6c9b]]

## Links
- lane: [cosmos](/lanes/cosmos.md)
- related: [mem_2b049e3f](/decision/mem_2b049e3f-a-flares-id-prefix-is-the-projects-lifecycle-sta.md)
- related: [mem_d4c37ea1](/finding/mem_d4c37ea1-slack-cards-and-the-slack-report-told-people-to.md)
- related: [mem_5cfd6c9b](/decision/mem_5cfd6c9b-commit-note-by-biswajit-tripathy-autopilot-from.md)
