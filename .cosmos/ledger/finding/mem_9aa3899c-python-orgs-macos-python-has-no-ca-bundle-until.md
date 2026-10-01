---
type: "Finding"
title: "python.org's macOS Python has no CA bundle until 'Install Certificates' is run, so every urllib HTTPS call from cosmos f"
description: "python.org's macOS Python has no CA bundle until 'Install Certificates' is run, so every urllib HTTPS call from cosmos failed CERTIFICATE_VERIFY_FAILED"
status: "stable"
generated: {"by": "human:Biswajit Tripathy", "at": "2026-10-01T00:00:00Z"}
sources: [{"resource": "cosmos/upgrade.py", "title": "upgrade.py"}]
stale_after: "2027-03-30T00:00:00Z"
id: "mem_9aa3899c"
aliases: ["mem_9aa3899c"]
category: "finding"
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

#finding #medium
