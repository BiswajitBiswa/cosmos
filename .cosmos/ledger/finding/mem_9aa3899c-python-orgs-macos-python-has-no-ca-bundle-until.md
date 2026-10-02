---
type: "Finding"
title: "python.org's macOS Python has no CA bundle until 'Install Certificates' is run, so every urllib HTTPS call from cosmos f"
description: "python.org's macOS Python has no CA bundle until 'Install Certificates' is run, so every urllib HTTPS call from cosmos failed CERTIFICATE_VERIFY_FAILED"
status: "stable"
generated: {"by": "human:Biswajit Tripathy", "at": "2026-10-01T00:00:00Z"}
sources: [{"resource": "cosmos/upgrade.py", "title": "upgrade.py"}]
stale_after: "2027-03-30T00:00:00Z"
links: ["/lanes/cosmos.md", "/constraint/mem_15da1401-for-clients-that-dont-report-their-folders-every.md", "/constraint/mem_cf1dd94b-tests-already-set-cosmosnobackground-so-they-can.md", "/decision/mem_4efbf3d7-releases-and-their-repairs-reach-every-project-b.md", "/dependency/mem_06dacbf0-self-upgrade-at-most-once-a-day-per-machine-a-se.md", "/dependency/mem_0c3037f2-cosmos-upgrade-py-210-maybebackground-the-daily.md"]
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
- [[mem_15da1401]]
- [[mem_cf1dd94b]]
- [[mem_4efbf3d7]]
- [[mem_06dacbf0]]
- [[mem_0c3037f2]]

## Links
- lane: [cosmos](/lanes/cosmos.md)
- related: [mem_15da1401](/constraint/mem_15da1401-for-clients-that-dont-report-their-folders-every.md)
- related: [mem_cf1dd94b](/constraint/mem_cf1dd94b-tests-already-set-cosmosnobackground-so-they-can.md)
- related: [mem_4efbf3d7](/decision/mem_4efbf3d7-releases-and-their-repairs-reach-every-project-b.md)
- related: [mem_06dacbf0](/dependency/mem_06dacbf0-self-upgrade-at-most-once-a-day-per-machine-a-se.md)
- related: [mem_0c3037f2](/dependency/mem_0c3037f2-cosmos-upgrade-py-210-maybebackground-the-daily.md)

#finding #medium
