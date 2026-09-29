---
type: "Decision"
title: "Playbooks: a repository's own long-form agent prompts (master QA protocol, runbooks) are detected by cosmos/playbooks.py"
description: "Playbooks: a repository's own long-form agent prompts (master QA protocol, runbooks) are detected by cosmos/playbooks.py (name or first heading says protocol/playbook/runbook/master prompt, and the text is written for an agent) plus .cosmos/playbooks/; each becomes a slash command for every agent and /qa follows the QA one. Reason: the owner wanted RETEN's master and QA prompts reusable by any project and detected automatically. cosmos playbooks add <file|qa> brings one in."
status: "stable"
generated: {"by": "human:Biswajit Tripathy", "at": "2026-09-29T00:00:00Z"}
sources: [{"resource": "cosmos/playbooks.py", "title": "playbooks.py"}, {"resource": "cosmos/commands.py", "title": "commands.py"}]
stale_after: "2027-03-28T00:00:00Z"
id: "mem_043ce3de"
aliases: ["mem_043ce3de"]
category: "decision"
cosmos_status: "active"
confidence: 0.95
importance: 0.95
source: "explicit"
created: "2026-09-29"
updated: "2026-09-29"
last_verified: "2026-09-29"
evidence_count: 1
files: ["cosmos/playbooks.py", "cosmos/commands.py"]
authors: ["Biswajit Tripathy"]
valid_from: "2026-09-29"
---

# Playbooks: a repository's own long-form agent prompts (master QA protocol, runbooks) are detected by cosmos/playbooks.py (name or first heading says protocol/playbook/runbook/master prompt, and the text is written for an agent) plus .cosmos/playbooks/; each becomes a slash command for every agent and /qa follows the QA one. Reason: the owner wanted RETEN's master and QA prompts reusable by any project and detected automatically. cosmos playbooks add <file|qa> brings one in.

**Category:** decision · **Status:** active · **Confidence:** 95%

## Why we believe this
- Observed 1× (first 2026-09-29, last 2026-09-29); source: explicit
- Evidence file: `cosmos/playbooks.py`
- Evidence file: `cosmos/commands.py`
