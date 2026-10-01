---
type: "Decision"
title: "Commit note by Biswajit Tripathy: plugin 0.2.1: Codex installs cosmos from its Plugins screen, nothing else to run \u2014 The"
description: "Commit note by Biswajit Tripathy: plugin 0.2.1: Codex installs cosmos from its Plugins screen, nothing else to run \u2014 The repository is already a marketplace Codex reads (.claude-plugin/marketplace.json). The plugin gains its own Codex manifest (plugin/.codex-plugin/plugin.json); Claude keeps reading plugin/.claude-plugin/. - Hooks (SessionStart, UserPromptSubmit) find the thread's repository and hand the event to its committed cosmos: the Charter and facts become the model's context, and the watcher that captures Codex sessions starts. No Stop hook: exit 2 would block a Codex thread. - One MCP server for every repository: Codex starts it in the plugin's folder, so it answers the handshake it"
status: "stable"
generated: {"by": "cosmos/git", "at": "2026-10-01T00:00:00Z"}
sources: [{"resource": ".claude-plugin/marketplace.json", "title": "marketplace.json"}, {"resource": "README.md", "title": "README.md"}, {"resource": "cosmos/ui.py", "title": "ui.py"}, {"resource": "docs/index.html", "title": "index.html"}, {"resource": "docs/plugin.md", "title": "plugin.md"}, {"resource": "plugin/.claude-plugin/plugin.json", "title": "plugin.json"}]
stale_after: "2027-03-30T00:00:00Z"
links: ["/lanes/docs.md", "/constraint/mem_2518367d-cosmos-is-on-pypi-as-cosmos-dev-0-1-0-published.md", "/constraint/mem_62468362-cosmos-dev-is-not-published-on-pypi-404-on-2026.md", "/constraint/mem_97f2aa55-installed-plugins-update-only-when-the-version-c.md", "/decision/mem_5cfd6c9b-commit-note-by-biswajit-tripathy-autopilot-from.md", "/finding/mem_10ab2ec4-console-docs-said-horizon-notes-are-saved-in-cos.md"]
id: "mem_1ac630fe"
aliases: ["mem_1ac630fe"]
category: "decision"
lane: "docs"
cosmos_status: "active"
confidence: 0.69
importance: 0.6
source: "git"
created: "2026-10-01"
updated: "2026-10-01"
last_verified: "2026-10-01"
evidence_count: 1
files: [".claude-plugin/marketplace.json", "README.md", "cosmos/ui.py", "docs/index.html", "docs/plugin.md", "plugin/.claude-plugin/plugin.json"]
tags: ["claude-plugin", "cosmos", "decision", "docs"]
authors: ["Biswajit Tripathy"]
valid_from: "2026-10-01"
---

# Commit note by Biswajit Tripathy: plugin 0.2.1: Codex installs cosmos from its Plugins screen, nothing else to run — The repository is already a marketplace Codex reads (.claude-plugin/marketplace.json). The plugin gains its own Codex manifest (plugin/.codex-plugin/plugin.json); Claude keeps reading plugin/.claude-plugin/. - Hooks (SessionStart, UserPromptSubmit) find the thread's repository and hand the event to its committed cosmos: the Charter and facts become the model's context, and the watcher that captures Codex sessions starts. No Stop hook: exit 2 would block a Codex thread. - One MCP server for every repository: Codex starts it in the plugin's folder, so it answers the handshake it

**Category:** decision · **Status:** active · **Confidence:** 69%

## Why we believe this
- Observed 1× (first 2026-10-01, last 2026-10-01); source: git
- Evidence file: `.claude-plugin/marketplace.json`
- Evidence file: `README.md`
- Evidence file: `cosmos/ui.py`
- Evidence file: `docs/index.html`
- Evidence file: `docs/plugin.md`
- Evidence file: `plugin/.claude-plugin/plugin.json`

## Related
- [[mem_2518367d]]
- [[mem_62468362]]
- [[mem_97f2aa55]]
- [[mem_5cfd6c9b]]
- [[mem_10ab2ec4]]

## Links
- lane: [docs](/lanes/docs.md)
- related: [mem_2518367d](/constraint/mem_2518367d-cosmos-is-on-pypi-as-cosmos-dev-0-1-0-published.md)
- related: [mem_62468362](/constraint/mem_62468362-cosmos-dev-is-not-published-on-pypi-404-on-2026.md)
- related: [mem_97f2aa55](/constraint/mem_97f2aa55-installed-plugins-update-only-when-the-version-c.md)
- related: [mem_5cfd6c9b](/decision/mem_5cfd6c9b-commit-note-by-biswajit-tripathy-autopilot-from.md)
- related: [mem_10ab2ec4](/finding/mem_10ab2ec4-console-docs-said-horizon-notes-are-saved-in-cos.md)

#claude-plugin #cosmos #decision #docs
