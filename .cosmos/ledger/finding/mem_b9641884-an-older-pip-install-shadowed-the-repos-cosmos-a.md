---
type: "Finding"
title: "An older pip install shadowed the repo's cosmos and rendered retired names (`finding:`, `cosmos intake`) into the commit"
description: "An older pip install shadowed the repo's cosmos and rendered retired names (`finding:`, `cosmos intake`) into the committed CLAUDE.md / AGENTS.md"
status: "stable"
generated: {"by": "human:Biswajit Tripathy", "at": "2026-09-29T00:00:00Z"}
sources: [{"resource": "cosmos/wrapper.py", "title": "wrapper.py"}]
stale_after: "2027-03-28T00:00:00Z"
links: ["/lanes/cosmos.md", "/finding/mem_1db8264f-a-claude-desktop-mcp-entry-named-cosmos-pinned-t.md", "/finding/mem_5790a327-cosmos-connect-with-no-agent-argument-failed-arg.md", "/finding/mem_5b583e8d-cosmosw-always-prefers-an-installed-cosmos-over.md", "/finding/mem_9391c461-atlas-reported-0-endpoints-for-apps-without-an-o.md"]
id: "mem_b9641884"
aliases: ["mem_b9641884"]
category: "finding"
lane: "cosmos"
cosmos_status: "active"
confidence: 0.9
importance: 0.65
source: "explicit"
created: "2026-09-29"
updated: "2026-09-29"
last_verified: "2026-09-29"
evidence_count: 1
files: ["cosmos/wrapper.py"]
tags: ["finding", "medium", "install"]
authors: ["Biswajit Tripathy"]
valid_from: "2026-09-29"
meta_area: "install"
meta_audit_id: "DEV-stale-install-rendered-old-block"
meta_finding_status: "fixed"
meta_found_commit: "3f80c40"
meta_locations: "`cosmos/wrapper.py:18` \u00b7 `CLAUDE.md:15`"
meta_raw_id: "stale-install-rendered-old-block"
meta_severity: "medium"
meta_source_doc: "qa-2026-09-29-commands"
---

# An older pip install shadowed the repo's cosmos and rendered retired names (`finding:`, `cosmos intake`) into the committed CLAUDE.md / AGENTS.md

**Category:** finding · **Status:** active · **Confidence:** 90%

## Details
**What** — cosmosw imports an installed cosmos before the vendored copy; the 3.11 site-packages copy predated 5b289ba, so hooks re-rendered the old block, committed at HEAD.

**Fix** — Editable install on this machine and a re-render. Remaining: the wrapper still prefers any installed copy over a newer vendored one (see open flare wrapper-prefers-stale-install).

## Why we believe this
- Observed 1× (first 2026-09-29, last 2026-09-29); source: explicit
- Evidence file: `cosmos/wrapper.py`
- Imported from qa-2026-09-29-commands on 2026-09-29

## Related
- [[mem_1db8264f]]
- [[mem_5790a327]]
- [[mem_5b583e8d]]
- [[mem_9391c461]]

## Links
- lane: [cosmos](/lanes/cosmos.md)
- related: [mem_1db8264f](/finding/mem_1db8264f-a-claude-desktop-mcp-entry-named-cosmos-pinned-t.md)
- related: [mem_5790a327](/finding/mem_5790a327-cosmos-connect-with-no-agent-argument-failed-arg.md)
- related: [mem_5b583e8d](/finding/mem_5b583e8d-cosmosw-always-prefers-an-installed-cosmos-over.md)
- related: [mem_9391c461](/finding/mem_9391c461-atlas-reported-0-endpoints-for-apps-without-an-o.md)

#finding #medium #install
