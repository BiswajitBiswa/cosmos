---
type: "Decision"
title: "Releases and their repairs reach every project by themselves (cosmos/upgrade.py): a session start checks PyPI at most on"
description: "Releases and their repairs reach every project by themselves (cosmos/upgrade.py): a session start checks PyPI at most once a day per machine; a newer wheel is sha256-checked against PyPI, import-tested, swapped into .cosmos/vendor and committed, and the pip install is upgraded when pip allows; each version runs repair once per machine and repository (wrapper, repo and user hooks, slash commands, .agents/plugins/marketplace.json for Codex, a Desktop MCP entry named cosmos renamed to cosmos-<repo> with a backup). New repairs go in REPAIRS and must be idempotent and touch only what cosmos wrote. update.auto false turns it off. Reason: the owner cannot push fixes into every team's project."
status: "stable"
generated: {"by": "human:Biswajit Tripathy", "at": "2026-10-01T00:00:00Z"}
sources: [{"resource": "cosmos/upgrade.py", "title": "upgrade.py"}]
stale_after: "2027-03-30T00:00:00Z"
id: "mem_4efbf3d7"
aliases: ["mem_4efbf3d7"]
category: "decision"
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
