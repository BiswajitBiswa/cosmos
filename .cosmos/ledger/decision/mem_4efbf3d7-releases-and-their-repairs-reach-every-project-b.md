---
type: "Decision"
title: "Releases and their repairs reach every project by themselves (cosmos/upgrade.py): a session start checks PyPI at most on"
description: "Releases and their repairs reach every project by themselves (cosmos/upgrade.py): a session start checks PyPI at most once a day per machine; a newer wheel is sha256-checked against PyPI, import-tested, swapped into .cosmos/vendor and committed, and the pip install is upgraded when pip allows; each version runs repair once per machine and repository (wrapper, repo and user hooks, slash commands, .agents/plugins/marketplace.json for Codex, a Desktop MCP entry named cosmos renamed to cosmos-<repo> with a backup). New repairs go in REPAIRS and must be idempotent and touch only what cosmos wrote. update.auto false turns it off. Reason: the owner cannot push fixes into every team's project."
status: "stable"
generated: {"by": "human:Biswajit Tripathy", "at": "2026-10-01T00:00:00Z"}
sources: [{"resource": "cosmos/upgrade.py", "title": "upgrade.py"}]
stale_after: "2027-03-30T00:00:00Z"
links: ["/lanes/cosmos.md", "/constraint/mem_15da1401-for-clients-that-dont-report-their-folders-every.md", "/constraint/mem_cf1dd94b-tests-already-set-cosmosnobackground-so-they-can.md", "/dependency/mem_06dacbf0-self-upgrade-at-most-once-a-day-per-machine-a-se.md", "/dependency/mem_0c3037f2-cosmos-upgrade-py-210-maybebackground-the-daily.md", "/dependency/mem_10ab0e02-cosmos-upgrade-py-282-stepcodexlisting-writes-th.md"]
id: "mem_4efbf3d7"
aliases: ["mem_4efbf3d7"]
category: "decision"
lane: "cosmos"
cosmos_status: "active"
confidence: 0.95
importance: 0.95
source: "explicit"
created: "2026-10-01"
updated: "2026-10-01"
last_verified: "2026-10-01"
evidence_count: 1
files: ["cosmos/upgrade.py"]
authors: ["Biswajit Tripathy"]
valid_from: "2026-10-01"
---

# Releases and their repairs reach every project by themselves (cosmos/upgrade.py): a session start checks PyPI at most once a day per machine; a newer wheel is sha256-checked against PyPI, import-tested, swapped into .cosmos/vendor and committed, and the pip install is upgraded when pip allows; each version runs repair once per machine and repository (wrapper, repo and user hooks, slash commands, .agents/plugins/marketplace.json for Codex, a Desktop MCP entry named cosmos renamed to cosmos-<repo> with a backup). New repairs go in REPAIRS and must be idempotent and touch only what cosmos wrote. update.auto false turns it off. Reason: the owner cannot push fixes into every team's project.

**Category:** decision · **Status:** active · **Confidence:** 95%

## Why we believe this
- Observed 1× (first 2026-10-01, last 2026-10-01); source: explicit
- Evidence file: `cosmos/upgrade.py`

## Related
- [[mem_15da1401]]
- [[mem_cf1dd94b]]
- [[mem_06dacbf0]]
- [[mem_0c3037f2]]
- [[mem_10ab0e02]]

## Links
- lane: [cosmos](/lanes/cosmos.md)
- related: [mem_15da1401](/constraint/mem_15da1401-for-clients-that-dont-report-their-folders-every.md)
- related: [mem_cf1dd94b](/constraint/mem_cf1dd94b-tests-already-set-cosmosnobackground-so-they-can.md)
- related: [mem_06dacbf0](/dependency/mem_06dacbf0-self-upgrade-at-most-once-a-day-per-machine-a-se.md)
- related: [mem_0c3037f2](/dependency/mem_0c3037f2-cosmos-upgrade-py-210-maybebackground-the-daily.md)
- related: [mem_10ab0e02](/dependency/mem_10ab0e02-cosmos-upgrade-py-282-stepcodexlisting-writes-th.md)
