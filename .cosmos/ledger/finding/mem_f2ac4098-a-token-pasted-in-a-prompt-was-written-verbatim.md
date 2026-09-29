---
type: "Finding"
title: "A token pasted in a prompt was written verbatim into the journal (`ask`) and the live view, and committed with .cosmos"
description: "A token pasted in a prompt was written verbatim into the journal (`ask`) and the live view, and committed with .cosmos"
status: "stable"
generated: {"by": "human:Biswajit Tripathy", "at": "2026-09-29T00:00:00Z"}
sources: [{"resource": "cosmos/hooks.py", "title": "hooks.py"}, {"resource": "cosmos/watch.py", "title": "watch.py"}, {"resource": "cosmos/privacy.py", "title": "privacy.py"}]
stale_after: "2027-03-28T00:00:00Z"
id: "mem_f2ac4098"
aliases: ["mem_f2ac4098"]
category: "finding"
cosmos_status: "active"
confidence: 0.9
importance: 0.85
source: "explicit"
created: "2026-09-29"
updated: "2026-09-29"
last_verified: "2026-09-29"
evidence_count: 1
files: ["cosmos/hooks.py", "cosmos/watch.py", "cosmos/privacy.py"]
tags: ["finding", "high", "privacy"]
authors: ["Biswajit Tripathy"]
valid_from: "2026-09-29"
meta_area: "privacy"
meta_audit_id: "PROD-pasted-token-in-journal"
meta_finding_status: "fixed"
meta_found_commit: "0c11381"
meta_locations: "`cosmos/hooks.py:96` \u00b7 `cosmos/watch.py:54` \u00b7 `cosmos/privacy.py:14`"
meta_raw_id: "pasted-token-in-journal"
meta_severity: "high"
meta_source_doc: "session-2026-09-29"
---

# A token pasted in a prompt was written verbatim into the journal (`ask`) and the live view, and committed with .cosmos

**Category:** finding · **Status:** active · **Confidence:** 90%

## Details
**What** — The journal's ask field and live.json kept the person's words without redaction; a GitHub PAT pasted in chat reached a local .cosmos commit (never pushed: GitHub push protection rejected the org push). PyPI and npm token formats had no pattern.

**Fix** — ask and the live view go through redact(); pypi- and npm_ patterns; the unpushed commit amended and unreachable objects pruned; TestPastedTokens.

## Why we believe this
- Observed 1× (first 2026-09-29, last 2026-09-29); source: explicit
- Evidence file: `cosmos/hooks.py`
- Evidence file: `cosmos/watch.py`
- Evidence file: `cosmos/privacy.py`
- Imported from session-2026-09-29 on 2026-09-29

#finding #high #privacy
