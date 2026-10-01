---
type: "Decision"
title: "The Gate runs security checks every turn on every touched file (cosmos/security.py): high-precision credential patterns "
description: "The Gate runs security checks every turn on every touched file (cosmos/security.py): high-precision credential patterns (placeholders, local or docker-compose URLs and 'cosmos: allow-secret' lines skipped), hidden Unicode (bidi overrides, tag characters, zero-width spaces; not emoji joiners, RTL marks or BOMs), and agent-steering text only in instruction files; a changed dependency manifest needs its audit; large changes add bandit or semgrep. Ledger notes that steer agents are withheld from briefings and recall until allowed with cosmos scan --allow. Reason: cosmos injects these files into every agent, so a poisoned one reaches every session."
status: "stable"
generated: {"by": "human:Biswajit Tripathy", "at": "2026-10-02T00:00:00Z"}
sources: [{"resource": "cosmos/security.py", "title": "security.py"}]
stale_after: "2027-03-31T00:00:00Z"
links: ["/lanes/cosmos.md"]
id: "mem_f044be42"
aliases: ["mem_f044be42"]
category: "decision"
lane: "cosmos"
cosmos_status: "active"
confidence: 0.95
importance: 0.95
source: "explicit"
created: "2026-10-02"
updated: "2026-10-02"
last_verified: "2026-10-02"
evidence_count: 1
files: ["cosmos/security.py"]
authors: ["Biswajit Tripathy"]
valid_from: "2026-10-02"
---

# The Gate runs security checks every turn on every touched file (cosmos/security.py): high-precision credential patterns (placeholders, local or docker-compose URLs and 'cosmos: allow-secret' lines skipped), hidden Unicode (bidi overrides, tag characters, zero-width spaces; not emoji joiners, RTL marks or BOMs), and agent-steering text only in instruction files; a changed dependency manifest needs its audit; large changes add bandit or semgrep. Ledger notes that steer agents are withheld from briefings and recall until allowed with cosmos scan --allow. Reason: cosmos injects these files into every agent, so a poisoned one reaches every session.

**Category:** decision · **Status:** active · **Confidence:** 95%

## Why we believe this
- Observed 1× (first 2026-10-02, last 2026-10-02); source: explicit
- Evidence file: `cosmos/security.py`

## Links
- lane: [cosmos](/lanes/cosmos.md)
