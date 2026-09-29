---
type: "Finding"
title: "Plugin changes never reached installed plugins: the plugin version stayed 0.1.0, so `claude plugin update` saw nothing n"
description: "Plugin changes never reached installed plugins: the plugin version stayed 0.1.0, so `claude plugin update` saw nothing new"
status: "stable"
generated: {"by": "human:Biswajit Tripathy", "at": "2026-09-29T00:00:00Z"}
sources: [{"resource": "plugin/.claude-plugin/plugin.js", "title": "plugin.js"}, {"resource": ".claude-plugin/marketplace.js", "title": "marketplace.js"}]
stale_after: "2027-03-28T00:00:00Z"
id: "mem_a41e3c70"
aliases: ["mem_a41e3c70"]
category: "finding"
cosmos_status: "active"
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

**Category:** finding · **Status:** active · **Confidence:** 90%

## Details
**Fix** — Bumped to 0.2.0; installs now get /cosmos:recall … (verified: updated from 0.1.0 to 0.2.0).

## Why we believe this
- Observed 1× (first 2026-09-29, last 2026-09-29); source: explicit
- Evidence file: `plugin/.claude-plugin/plugin.js`
- Evidence file: `.claude-plugin/marketplace.js`
- Imported from session-2026-09-29 on 2026-09-29

#finding #medium #plugin
