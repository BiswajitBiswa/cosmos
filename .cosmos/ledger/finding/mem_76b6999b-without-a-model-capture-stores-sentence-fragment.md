---
type: "Finding"
title: "Without a model, capture stores sentence fragments that make no sense out\u2026"
description: "Without a model, capture stores sentence fragments that make no sense out of context"
status: "stable"
generated: {"by": "human:Biswajit Tripathy", "at": "2026-10-07T00:00:00Z"}
sources: [{"resource": "cosmos/extract.py", "title": "extract.py"}]
stale_after: "2027-04-05T00:00:00Z"
links: ["/lanes/cosmos.md", "/finding/mem_0448e271-the-watcher-started-a-dream-every-30-seconds-whi.md", "/finding/mem_1db8264f-a-claude-desktop-mcp-entry-named-cosmos-pinned-t.md", "/finding/mem_498078e0-atlas-page-4-of-8-deep-pass-diagrams-failed-unde.md", "/finding/mem_5790a327-cosmos-connect-with-no-agent-argument-failed-arg.md", "/finding/mem_5b583e8d-cosmosw-always-prefers-an-installed-cosmos-over.md"]
id: "mem_76b6999b"
aliases: ["mem_76b6999b"]
category: "finding"
lane: "cosmos"
cosmos_status: "active"
confidence: 0.9
importance: 0.65
source: "explicit"
created: "2026-10-07"
updated: "2026-10-07"
last_verified: "2026-10-07"
evidence_count: 1
files: ["cosmos/extract.py"]
tags: ["finding", "medium", "capture"]
authors: ["Biswajit Tripathy"]
valid_from: "2026-10-07"
meta_area: "capture"
meta_audit_id: "PROD-98a897"
meta_claimed_on: "2026-10-07"
meta_finding_status: "claimed"
meta_found_commit: "552809d"
meta_locations: "cosmos/extract.py:131"
meta_raw_id: "98a897"
meta_severity: "medium"
meta_source_doc: "manual"
meta_status_at: "2026-10-07"
meta_status_note: "fixed in the main working tree (cosmos/extract.py ANAPHOR, cosmos/lanes.py + charter.py), tests pass, not committed yet"
---

# Without a model, capture stores sentence fragments that make no sense out of context

**Category:** finding · **Status:** active · **Confidence:** 90%

## Details
**What** — extract_from_turn keeps any assistant sentence that scores on the patterns, including ones whose subject is in the previous sentence. In retent, 103 observed notes were made between 2026-10-03 and 10-07 while model use was paused, e.g. '`all` is null only if the business never set one up.', 'The new version lives in `retent-preview`.', 'Keep the capitals as they are, and don't add "WhatsApp" or a slogan.'

**Impact** — The ledger and recall fill with facts nobody can act on; with the model off for days (fallback windows) there is no rewrite step to fix them.

**Fix** — Drop or down-score sentences that open with an anaphor (It, They, This, That, These, Both, Same, Now, Still) or with a bare code span and no verb subject, unless the previous sentence is joined in as context.

## Why we believe this
- Observed 1× (first 2026-10-07, last 2026-10-07); source: explicit
- Evidence file: `cosmos/extract.py`
- Marked claimed on 2026-10-07: fixed in the main working tree (cosmos/extract.py ANAPHOR, cosmos/lanes.py + charter.py), tests pass, not committed yet

## Related
- [[mem_0448e271]]
- [[mem_1db8264f]]
- [[mem_498078e0]]
- [[mem_5790a327]]
- [[mem_5b583e8d]]

## Links
- lane: [cosmos](/lanes/cosmos.md)
- related: [mem_0448e271](/finding/mem_0448e271-the-watcher-started-a-dream-every-30-seconds-whi.md)
- related: [mem_1db8264f](/finding/mem_1db8264f-a-claude-desktop-mcp-entry-named-cosmos-pinned-t.md)
- related: [mem_498078e0](/finding/mem_498078e0-atlas-page-4-of-8-deep-pass-diagrams-failed-unde.md)
- related: [mem_5790a327](/finding/mem_5790a327-cosmos-connect-with-no-agent-argument-failed-arg.md)
- related: [mem_5b583e8d](/finding/mem_5b583e8d-cosmosw-always-prefers-an-installed-cosmos-over.md)

#finding #medium #capture
