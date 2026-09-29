---
type: "Finding"
title: "Plugin changes never reached installed plugins: the plugin version stayed 0.1.0, so `claude plugin update` saw nothing n"
description: "Plugin changes never reached installed plugins: the plugin version stayed 0.1.0, so `claude plugin update` saw nothing new"
status: "draft"
generated: {"by": "human:Biswajit Tripathy", "at": "2026-09-29T00:00:00Z"}
sources: [{"resource": "plugin/.claude-plugin/plugin.js", "title": "plugin.js"}, {"resource": ".claude-plugin/marketplace.js", "title": "marketplace.js"}]
links: ["/lanes/plugin.md", "/finding/mem_1db8264f-a-claude-desktop-mcp-entry-named-cosmos-pinned-t.md", "/finding/mem_498078e0-atlas-page-4-of-8-deep-pass-diagrams-failed-unde.md", "/finding/mem_5790a327-cosmos-connect-with-no-agent-argument-failed-arg.md", "/finding/mem_5b583e8d-cosmosw-always-prefers-an-installed-cosmos-over.md", "/finding/mem_9391c461-atlas-reported-0-endpoints-for-apps-without-an-o.md"]
id: "mem_a41e3c70"
aliases: ["mem_a41e3c70"]
category: "finding"
lane: "plugin"
cosmos_status: "stale-candidate"
confidence: 0.9
importance: 0.65
source: "explicit"
created: "2026-09-29"
updated: "2026-09-29"
last_verified: "2026-09-29"
evidence_count: 1
files: ["plugin/.claude-plugin/plugin.js", ".claude-plugin/marketplace.js"]
tags: ["finding", "medium", "plugin"]
authors: ["Biswajit Tripathy"]
valid_from: "2026-09-29"
meta_area: "plugin"
meta_audit_id: "DEV-plugin-version-frozen"
meta_finding_status: "fixed"
meta_found_commit: "28db571"
meta_locations: "`plugin/.claude-plugin/plugin.json:3` \u00b7 `.claude-plugin/marketplace.json:9`"
meta_raw_id: "plugin-version-frozen"
meta_severity: "medium"
meta_source_doc: "session-2026-09-29"
---

# Plugin changes never reached installed plugins: the plugin version stayed 0.1.0, so `claude plugin update` saw nothing new

**Category:** finding · **Status:** stale-candidate · **Confidence:** 90%

## Details
**Fix** — Bumped to 0.2.0; installs now get /cosmos:recall … (verified: updated from 0.1.0 to 0.2.0).

## Why we believe this
- Observed 1× (first 2026-09-29, last 2026-09-29); source: explicit
- Evidence file: `plugin/.claude-plugin/plugin.js`
- Evidence file: `.claude-plugin/marketplace.js`
- Stale candidate since 2026-09-29: none of the evidence files exist anymore, in any worktree

## Related
- [[mem_1db8264f]]
- [[mem_498078e0]]
- [[mem_5790a327]]
- [[mem_5b583e8d]]
- [[mem_9391c461]]

## Links
- lane: [plugin](/lanes/plugin.md)
- related: [mem_1db8264f](/finding/mem_1db8264f-a-claude-desktop-mcp-entry-named-cosmos-pinned-t.md)
- related: [mem_498078e0](/finding/mem_498078e0-atlas-page-4-of-8-deep-pass-diagrams-failed-unde.md)
- related: [mem_5790a327](/finding/mem_5790a327-cosmos-connect-with-no-agent-argument-failed-arg.md)
- related: [mem_5b583e8d](/finding/mem_5b583e8d-cosmosw-always-prefers-an-installed-cosmos-over.md)
- related: [mem_9391c461](/finding/mem_9391c461-atlas-reported-0-endpoints-for-apps-without-an-o.md)

#finding #medium #plugin
