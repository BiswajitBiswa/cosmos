---
type: "Finding"
title: "python.org's macOS Python has no CA bundle until 'Install Certificates' is run, so every urllib HTTPS call from cosmos f"
description: "python.org's macOS Python has no CA bundle until 'Install Certificates' is run, so every urllib HTTPS call from cosmos failed CERTIFICATE_VERIFY_FAILED"
status: "stable"
generated: {"by": "human:Biswajit Tripathy", "at": "2026-10-01T00:00:00Z"}
sources: [{"resource": "cosmos/upgrade.py", "title": "upgrade.py"}]
stale_after: "2027-03-30T00:00:00Z"
links: ["/lanes/cosmos.md", "/decision/mem_4efbf3d7-releases-and-their-repairs-reach-every-project-b.md", "/finding/mem_1db8264f-a-claude-desktop-mcp-entry-named-cosmos-pinned-t.md", "/finding/mem_498078e0-atlas-page-4-of-8-deep-pass-diagrams-failed-unde.md", "/finding/mem_5790a327-cosmos-connect-with-no-agent-argument-failed-arg.md", "/finding/mem_5b583e8d-cosmosw-always-prefers-an-installed-cosmos-over.md"]
id: "mem_9aa3899c"
aliases: ["mem_9aa3899c"]
category: "finding"
lane: "cosmos"
cosmos_status: "active"
confidence: 0.9
importance: 0.65
source: "explicit"
created: "2026-10-01"
updated: "2026-10-01"
last_verified: "2026-10-01"
evidence_count: 1
files: ["cosmos/upgrade.py"]
tags: ["finding", "medium"]
authors: ["Biswajit Tripathy"]
valid_from: "2026-10-01"
meta_audit_id: "PROD-828ba3"
meta_finding_status: "fixed"
meta_fixed_commit: "4580d07"
meta_fixed_on: "2026-10-01"
meta_found_commit: "4580d07"
meta_locations: "cosmos/upgrade.py"
meta_raw_id: "828ba3"
meta_severity: "medium"
meta_source_doc: "manual"
meta_status_at: "2026-10-01"
meta_status_note: "cosmos/upgrade.py _contexts/_get (local commit 47747f8, not pushed)"
---

# python.org's macOS Python has no CA bundle until 'Install Certificates' is run, so every urllib HTTPS call from cosmos failed CERTIFICATE_VERIFY_FAILED

**Category:** finding · **Status:** active · **Confidence:** 90%

## Details
**Fix** — upgrade._get retries with certifi, then the system bundle (/etc/ssl/cert.pem …); verification is never disabled

## Why we believe this
- Observed 1× (first 2026-10-01, last 2026-10-01); source: explicit
- Evidence file: `cosmos/upgrade.py`
- Marked fixed on 2026-10-01: cosmos/upgrade.py _contexts/_get (local commit 47747f8, not pushed)

## Related
- [[mem_4efbf3d7]]
- [[mem_1db8264f]]
- [[mem_498078e0]]
- [[mem_5790a327]]
- [[mem_5b583e8d]]

## Links
- lane: [cosmos](/lanes/cosmos.md)
- related: [mem_4efbf3d7](/decision/mem_4efbf3d7-releases-and-their-repairs-reach-every-project-b.md)
- related: [mem_1db8264f](/finding/mem_1db8264f-a-claude-desktop-mcp-entry-named-cosmos-pinned-t.md)
- related: [mem_498078e0](/finding/mem_498078e0-atlas-page-4-of-8-deep-pass-diagrams-failed-unde.md)
- related: [mem_5790a327](/finding/mem_5790a327-cosmos-connect-with-no-agent-argument-failed-arg.md)
- related: [mem_5b583e8d](/finding/mem_5b583e8d-cosmosw-always-prefers-an-installed-cosmos-over.md)

#finding #medium
