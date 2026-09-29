---
type: "Finding"
title: "Atlas reported 0 endpoints for apps without an OpenAPI spec (routes in code were never read)"
description: "Atlas reported 0 endpoints for apps without an OpenAPI spec (routes in code were never read)"
status: "stable"
generated: {"by": "human:Biswajit Tripathy", "at": "2026-09-29T00:00:00Z"}
sources: [{"resource": "cosmos/atlas.py", "title": "atlas.py"}]
stale_after: "2027-03-28T00:00:00Z"
links: ["/lanes/cosmos.md", "/architecture/mem_b6b76950-the-atlas-has-a-peoples-view-cosmos-atlashtml-py.md", "/finding/mem_1db8264f-a-claude-desktop-mcp-entry-named-cosmos-pinned-t.md", "/finding/mem_498078e0-atlas-page-4-of-8-deep-pass-diagrams-failed-unde.md", "/finding/mem_5790a327-cosmos-connect-with-no-agent-argument-failed-arg.md", "/finding/mem_5b583e8d-cosmosw-always-prefers-an-installed-cosmos-over.md"]
id: "mem_9391c461"
aliases: ["mem_9391c461"]
category: "finding"
lane: "cosmos"
cosmos_status: "active"
confidence: 0.9
importance: 0.65
source: "explicit"
created: "2026-09-29"
updated: "2026-09-29"
last_verified: "2026-09-29"
evidence_count: 1
files: ["cosmos/atlas.py"]
tags: ["finding", "medium"]
authors: ["Biswajit Tripathy"]
valid_from: "2026-09-29"
meta_audit_id: "DEV-atlas-code-routes"
meta_finding_status: "fixed"
meta_found_commit: "78b6652"
meta_locations: "`cosmos/atlas.py:168` \u00b7 `cosmos/atlas.py:293`"
meta_raw_id: "atlas-code-routes"
meta_severity: "medium"
meta_source_doc: "session-2026-09-29"
---

# Atlas reported 0 endpoints for apps without an OpenAPI spec (routes in code were never read)

**Category:** finding · **Status:** active · **Confidence:** 90%

## Details
**What** — Endpoints came only from openapi/swagger files; RETEN's ~204 FastAPI routes showed as 0.

**Fix** — code_routes() reads FastAPI/Flask/Express route declarations when no spec has endpoints (203 in RETEN). Test: TestAtlasCodeRoutes.

## Why we believe this
- Observed 1× (first 2026-09-29, last 2026-09-29); source: explicit
- Evidence file: `cosmos/atlas.py`
- Imported from session-2026-09-29 on 2026-09-29

## Related
- [[mem_b6b76950]]
- [[mem_1db8264f]]
- [[mem_498078e0]]
- [[mem_5790a327]]
- [[mem_5b583e8d]]

## Links
- lane: [cosmos](/lanes/cosmos.md)
- related: [mem_b6b76950](/architecture/mem_b6b76950-the-atlas-has-a-peoples-view-cosmos-atlashtml-py.md)
- related: [mem_1db8264f](/finding/mem_1db8264f-a-claude-desktop-mcp-entry-named-cosmos-pinned-t.md)
- related: [mem_498078e0](/finding/mem_498078e0-atlas-page-4-of-8-deep-pass-diagrams-failed-unde.md)
- related: [mem_5790a327](/finding/mem_5790a327-cosmos-connect-with-no-agent-argument-failed-arg.md)
- related: [mem_5b583e8d](/finding/mem_5b583e8d-cosmosw-always-prefers-an-installed-cosmos-over.md)

#finding #medium
