---
type: "Workflow"
title: "Never modify a project's cosmos copy (.cosmos/vendor, cosmosw) directly from the cosmos repository; changes reach projec"
description: "Never modify a project's cosmos copy (.cosmos/vendor, cosmosw) directly from the cosmos repository; changes reach projects only through a release and the auto-upgrade (cosmos upgrade, daily from a session start). Reason: the owner wants every project to get fixes the same way, without anyone pushing into each repository."
status: "stable"
generated: {"by": "human:Biswajit Tripathy", "at": "2026-10-02T00:00:00Z"}
sources: [{"resource": "cosmos/upgrade.py", "title": "upgrade.py"}]
stale_after: "2027-03-31T00:00:00Z"
links: ["/lanes/cosmos.md", "/decision/mem_4efbf3d7-releases-and-their-repairs-reach-every-project-b.md", "/finding/mem_6fa48630-a-repository-whose-committed-hook-command-is-old.md", "/finding/mem_9aa3899c-python-orgs-macos-python-has-no-ca-bundle-until.md"]
id: "mem_764f889d"
aliases: ["mem_764f889d"]
category: "workflow"
lane: "cosmos"
cosmos_status: "active"
confidence: 0.95
importance: 0.95
source: "explicit"
created: "2026-10-02"
updated: "2026-10-02"
last_verified: "2026-10-02"
evidence_count: 1
files: ["cosmos/upgrade.py"]
authors: ["Biswajit Tripathy"]
valid_from: "2026-10-02"
---

# Never modify a project's cosmos copy (.cosmos/vendor, cosmosw) directly from the cosmos repository; changes reach projects only through a release and the auto-upgrade (cosmos upgrade, daily from a session start). Reason: the owner wants every project to get fixes the same way, without anyone pushing into each repository.

**Category:** workflow · **Status:** active · **Confidence:** 95%

## Why we believe this
- Observed 1× (first 2026-10-02, last 2026-10-02); source: explicit
- Evidence file: `cosmos/upgrade.py`

## Related
- [[mem_4efbf3d7]]
- [[mem_6fa48630]]
- [[mem_9aa3899c]]

## Links
- lane: [cosmos](/lanes/cosmos.md)
- related: [mem_4efbf3d7](/decision/mem_4efbf3d7-releases-and-their-repairs-reach-every-project-b.md)
- related: [mem_6fa48630](/finding/mem_6fa48630-a-repository-whose-committed-hook-command-is-old.md)
- related: [mem_9aa3899c](/finding/mem_9aa3899c-python-orgs-macos-python-has-no-ca-bundle-until.md)
