---
type: "Finding"
title: "Atlas page: 4 of 8 deep-pass diagrams failed under mermaid 10.9.1 (unquoted ( ) { } in labels, ; in sequence text) and o"
description: "Atlas page: 4 of 8 deep-pass diagrams failed under mermaid 10.9.1 (unquoted ( ) { } in labels, ; in sequence text) and only the first diagram of a document was drawn"
status: "stable"
generated: {"by": "human:Biswajit Tripathy", "at": "2026-09-29T00:00:00Z"}
sources: [{"resource": "cosmos/ui.py", "title": "ui.py"}, {"resource": "cosmos/atlas.py", "title": "atlas.py"}]
stale_after: "2027-03-28T00:00:00Z"
links: ["/lanes/cosmos.md", "/architecture/mem_b6b76950-the-atlas-has-a-peoples-view-cosmos-atlashtml-py.md", "/decision/mem_1ac630fe-commit-note-by-biswajit-tripathy-plugin-0-2-1-co.md", "/finding/mem_10ab2ec4-console-docs-said-horizon-notes-are-saved-in-cos.md", "/finding/mem_1db8264f-a-claude-desktop-mcp-entry-named-cosmos-pinned-t.md", "/finding/mem_5790a327-cosmos-connect-with-no-agent-argument-failed-arg.md"]
id: "mem_498078e0"
aliases: ["mem_498078e0"]
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
files: ["cosmos/ui.py", "cosmos/atlas.py"]
tags: ["finding", "medium", "console"]
authors: ["Biswajit Tripathy"]
valid_from: "2026-09-29"
meta_area: "console"
meta_audit_id: "DEV-atlas-mermaid-parse"
meta_finding_status: "fixed"
meta_found_commit: "28db571"
meta_locations: "`cosmos/ui.py:570` \u00b7 `cosmos/ui.py:572` \u00b7 `cosmos/atlas.py:452`"
meta_raw_id: "atlas-mermaid-parse"
meta_severity: "medium"
meta_source_doc: "session-2026-09-29"
---

# Atlas page: 4 of 8 deep-pass diagrams failed under mermaid 10.9.1 (unquoted ( ) { } in labels, ; in sequence text) and only the first diagram of a document was drawn

**Category:** finding · **Status:** active · **Confidence:** 90%

## Details
**Fix** — mmdFix quotes labels and escapes ; before parsing, every diagram in a document is drawn, a failing one shows as text with its error; the Atlas prompt asks for quoted, classed diagrams. All 8 of RETEN's parse.

## Why we believe this
- Observed 1× (first 2026-09-29, last 2026-09-29); source: explicit
- Evidence file: `cosmos/ui.py`
- Evidence file: `cosmos/atlas.py`
- Imported from session-2026-09-29 on 2026-09-29

## Related
- [[mem_b6b76950]]
- [[mem_1ac630fe]]
- [[mem_10ab2ec4]]
- [[mem_1db8264f]]
- [[mem_5790a327]]

## Links
- lane: [cosmos](/lanes/cosmos.md)
- related: [mem_b6b76950](/architecture/mem_b6b76950-the-atlas-has-a-peoples-view-cosmos-atlashtml-py.md)
- related: [mem_1ac630fe](/decision/mem_1ac630fe-commit-note-by-biswajit-tripathy-plugin-0-2-1-co.md)
- related: [mem_10ab2ec4](/finding/mem_10ab2ec4-console-docs-said-horizon-notes-are-saved-in-cos.md)
- related: [mem_1db8264f](/finding/mem_1db8264f-a-claude-desktop-mcp-entry-named-cosmos-pinned-t.md)
- related: [mem_5790a327](/finding/mem_5790a327-cosmos-connect-with-no-agent-argument-failed-arg.md)

#finding #medium #console
