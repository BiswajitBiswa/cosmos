---
type: "Decision"
title: "A flare's id prefix is the project's lifecycle stage read from git when it is filed (qa/* \u2192 QA, uat/staging \u2192 UAT, relea"
description: "A flare's id prefix is the project's lifecycle stage read from git when it is filed (qa/* \u2192 QA, uat/staging \u2192 UAT, release/* or rc tag \u2192 RC, hotfix/* \u2192 HOTFIX, main with a reachable version tag \u2192 PROD, else DEV); a flare keeps its prefix for life and re-imports match by (source_doc, raw_id). flares.prefix pins one prefix (explicit outranks inferred); `import --prefix` applies to that import only and is no longer saved. Reason: the owner wanted prefixes to follow the project lifecycle without an extra command."
status: "stable"
generated: {"by": "human:Biswajit Tripathy", "at": "2026-09-29T00:00:00Z"}
sources: [{"resource": "cosmos/audit.py", "title": "audit.py"}]
stale_after: "2027-03-28T00:00:00Z"
links: ["/lanes/cosmos.md", "/decision/mem_1734bf56-bugs-found-by-hand-become-flares-through-one-pat.md", "/decision/mem_5cfd6c9b-commit-note-by-biswajit-tripathy-autopilot-from.md", "/finding/mem_d4c37ea1-slack-cards-and-the-slack-report-told-people-to.md"]
id: "mem_2b049e3f"
aliases: ["mem_2b049e3f"]
category: "decision"
lane: "cosmos"
cosmos_status: "active"
confidence: 0.95
importance: 0.95
source: "explicit"
created: "2026-09-29"
updated: "2026-09-29"
last_verified: "2026-09-29"
evidence_count: 1
files: ["cosmos/audit.py"]
authors: ["Biswajit Tripathy"]
valid_from: "2026-09-29"
---

# A flare's id prefix is the project's lifecycle stage read from git when it is filed (qa/* → QA, uat/staging → UAT, release/* or rc tag → RC, hotfix/* → HOTFIX, main with a reachable version tag → PROD, else DEV); a flare keeps its prefix for life and re-imports match by (source_doc, raw_id). flares.prefix pins one prefix (explicit outranks inferred); `import --prefix` applies to that import only and is no longer saved. Reason: the owner wanted prefixes to follow the project lifecycle without an extra command.

**Category:** decision · **Status:** active · **Confidence:** 95%

## Why we believe this
- Observed 1× (first 2026-09-29, last 2026-09-29); source: explicit
- Evidence file: `cosmos/audit.py`

## Related
- [[mem_1734bf56]]
- [[mem_5cfd6c9b]]
- [[mem_d4c37ea1]]

## Links
- lane: [cosmos](/lanes/cosmos.md)
- related: [mem_1734bf56](/decision/mem_1734bf56-bugs-found-by-hand-become-flares-through-one-pat.md)
- related: [mem_5cfd6c9b](/decision/mem_5cfd6c9b-commit-note-by-biswajit-tripathy-autopilot-from.md)
- related: [mem_d4c37ea1](/finding/mem_d4c37ea1-slack-cards-and-the-slack-report-told-people-to.md)
