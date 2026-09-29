---
type: "Architecture"
title: "Slash commands for every agent come from one catalogue in cosmos/commands.py (Claude .claude/commands, Gemini .gemini/co"
description: "Slash commands for every agent come from one catalogue in cosmos/commands.py (Claude .claude/commands, Gemini .gemini/commands TOML, Cursor .cursor/commands, Copilot .github/prompts, Windsurf .windsurf/workflows, Codex only ~/.codex/prompts via --write-user, plugin/commands for the plugin). Files carrying 'written by cosmos' are rewritten; unmarked files are the team's own and never overwritten. plugin/commands must be regenerated when the catalogue changes (a test fails otherwise)."
status: "stable"
generated: {"by": "human:Biswajit Tripathy", "at": "2026-09-29T00:00:00Z"}
sources: [{"resource": "cosmos/commands.py", "title": "commands.py"}, {"resource": "plugin/commands/", "title": ""}]
stale_after: "2027-03-28T00:00:00Z"
links: ["/lanes/cosmos.md", "/decision/mem_043ce3de-playbooks-a-repositorys-own-long-form-agent-prom.md", "/finding/mem_fcf6d908-new-slash-commands-reintroduced-names-retired-in.md"]
id: "mem_1f13b61a"
aliases: ["mem_1f13b61a"]
category: "architecture"
lane: "cosmos"
cosmos_status: "active"
confidence: 0.95
importance: 0.95
source: "explicit"
created: "2026-09-29"
updated: "2026-09-29"
last_verified: "2026-09-29"
evidence_count: 1
files: ["cosmos/commands.py", "plugin/commands/"]
authors: ["Biswajit Tripathy"]
valid_from: "2026-09-29"
---

# Slash commands for every agent come from one catalogue in cosmos/commands.py (Claude .claude/commands, Gemini .gemini/commands TOML, Cursor .cursor/commands, Copilot .github/prompts, Windsurf .windsurf/workflows, Codex only ~/.codex/prompts via --write-user, plugin/commands for the plugin). Files carrying 'written by cosmos' are rewritten; unmarked files are the team's own and never overwritten. plugin/commands must be regenerated when the catalogue changes (a test fails otherwise).

**Category:** architecture · **Status:** active · **Confidence:** 95%

## Why we believe this
- Observed 1× (first 2026-09-29, last 2026-09-29); source: explicit
- Evidence file: `cosmos/commands.py`
- Evidence file: `plugin/commands/`

## Related
- [[mem_043ce3de]]
- [[mem_fcf6d908]]

## Links
- lane: [cosmos](/lanes/cosmos.md)
- related: [mem_043ce3de](/decision/mem_043ce3de-playbooks-a-repositorys-own-long-form-agent-prom.md)
- related: [mem_fcf6d908](/finding/mem_fcf6d908-new-slash-commands-reintroduced-names-retired-in.md)
