---
type: "Finding"
title: "`cosmos connect` with no agent argument failed: argparse checked the default ['all'] against choices"
description: "`cosmos connect` with no agent argument failed: argparse checked the default ['all'] against choices"
status: "stable"
generated: {"by": "human:Biswajit Tripathy", "at": "2026-09-29T00:00:00Z"}
sources: [{"resource": "cosmos/cli.py", "title": "cli.py"}]
stale_after: "2027-03-28T00:00:00Z"
links: ["/lanes/cosmos.md", "/decision/mem_5cfd6c9b-commit-note-by-biswajit-tripathy-autopilot-from.md", "/finding/mem_1db8264f-a-claude-desktop-mcp-entry-named-cosmos-pinned-t.md", "/finding/mem_498078e0-atlas-page-4-of-8-deep-pass-diagrams-failed-unde.md", "/finding/mem_5b583e8d-cosmosw-always-prefers-an-installed-cosmos-over.md", "/finding/mem_6fa48630-a-repository-whose-committed-hook-command-is-old.md"]
id: "mem_5790a327"
aliases: ["mem_5790a327"]
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
files: ["cosmos/cli.py"]
tags: ["finding", "medium"]
authors: ["Biswajit Tripathy"]
valid_from: "2026-09-29"
meta_audit_id: "DEV-connect-default"
meta_finding_status: "fixed"
meta_found_commit: "78b6652"
meta_locations: "`cosmos/cli.py:272`"
meta_raw_id: "connect-default"
meta_severity: "medium"
meta_source_doc: "session-2026-09-29"
---

# `cosmos connect` with no agent argument failed: argparse checked the default ['all'] against choices

**Category:** finding · **Status:** active · **Confidence:** 90%

## Details
**What** — nargs='*' with default=['all'] and choices made `cosmos connect` exit with invalid choice on Python 3.10.

**Fix** — Positional without choices, validated in cmd_connect; empty means all. Test: TestSlashCommands.test_connect_with_no_agent_wires_all.

## Why we believe this
- Observed 1× (first 2026-09-29, last 2026-09-29); source: explicit
- Evidence file: `cosmos/cli.py`
- Imported from session-2026-09-29 on 2026-09-29

## Related
- [[mem_5cfd6c9b]]
- [[mem_1db8264f]]
- [[mem_498078e0]]
- [[mem_5b583e8d]]
- [[mem_6fa48630]]

## Links
- lane: [cosmos](/lanes/cosmos.md)
- related: [mem_5cfd6c9b](/decision/mem_5cfd6c9b-commit-note-by-biswajit-tripathy-autopilot-from.md)
- related: [mem_1db8264f](/finding/mem_1db8264f-a-claude-desktop-mcp-entry-named-cosmos-pinned-t.md)
- related: [mem_498078e0](/finding/mem_498078e0-atlas-page-4-of-8-deep-pass-diagrams-failed-unde.md)
- related: [mem_5b583e8d](/finding/mem_5b583e8d-cosmosw-always-prefers-an-installed-cosmos-over.md)
- related: [mem_6fa48630](/finding/mem_6fa48630-a-repository-whose-committed-hook-command-is-old.md)

#finding #medium
