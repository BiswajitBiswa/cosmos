---
type: "Constraint"
title: "Installed plugins update only when the version changes: bump plugin/.claude-plugin/plugin.json and .claude-plugin/market"
description: "Installed plugins update only when the version changes: bump plugin/.claude-plugin/plugin.json and .claude-plugin/marketplace.json together whenever plugin files (commands, skill, bin) change, or `claude plugin update` reports 'already at the latest version'. The plugin version (0.2.0) is independent of the PyPI package version."
status: "stable"
generated: {"by": "human:Biswajit Tripathy", "at": "2026-09-29T00:00:00Z"}
sources: [{"resource": "plugin/.claude-plugin/plugin.json", "title": "plugin.json"}, {"resource": ".claude-plugin/marketplace.json", "title": "marketplace.json"}]
stale_after: "2027-03-28T00:00:00Z"
links: ["/lanes/plugin.md", "/decision/mem_1ac630fe-commit-note-by-biswajit-tripathy-plugin-0-2-1-co.md", "/decision/mem_5cfd6c9b-commit-note-by-biswajit-tripathy-autopilot-from.md"]
id: "mem_97f2aa55"
aliases: ["mem_97f2aa55"]
category: "constraint"
lane: "plugin"
cosmos_status: "active"
confidence: 0.95
importance: 0.95
source: "explicit"
created: "2026-09-29"
updated: "2026-09-29"
last_verified: "2026-09-29"
evidence_count: 1
files: ["plugin/.claude-plugin/plugin.json", ".claude-plugin/marketplace.json"]
authors: ["Biswajit Tripathy"]
valid_from: "2026-09-29"
---

# Installed plugins update only when the version changes: bump plugin/.claude-plugin/plugin.json and .claude-plugin/marketplace.json together whenever plugin files (commands, skill, bin) change, or `claude plugin update` reports 'already at the latest version'. The plugin version (0.2.0) is independent of the PyPI package version.

**Category:** constraint · **Status:** active · **Confidence:** 95%

## Why we believe this
- Observed 1× (first 2026-09-29, last 2026-09-29); source: explicit
- Evidence file: `plugin/.claude-plugin/plugin.json`
- Evidence file: `.claude-plugin/marketplace.json`

## Related
- [[mem_1ac630fe]]
- [[mem_5cfd6c9b]]

## Links
- lane: [plugin](/lanes/plugin.md)
- related: [mem_1ac630fe](/decision/mem_1ac630fe-commit-note-by-biswajit-tripathy-plugin-0-2-1-co.md)
- related: [mem_5cfd6c9b](/decision/mem_5cfd6c9b-commit-note-by-biswajit-tripathy-autopilot-from.md)
