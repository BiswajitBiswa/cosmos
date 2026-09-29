---
type: "Finding"
title: "Atlas reported 0 endpoints for apps without an OpenAPI spec (routes in code were never read)"
description: "Atlas reported 0 endpoints for apps without an OpenAPI spec (routes in code were never read)"
status: "stable"
generated: {"by": "human:Biswajit Tripathy", "at": "2026-09-29T00:00:00Z"}
sources: [{"resource": "cosmos/atlas.py", "title": "atlas.py"}]
stale_after: "2027-03-28T00:00:00Z"
id: "mem_9391c461"
aliases: ["mem_9391c461"]
category: "finding"
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

#finding #medium
