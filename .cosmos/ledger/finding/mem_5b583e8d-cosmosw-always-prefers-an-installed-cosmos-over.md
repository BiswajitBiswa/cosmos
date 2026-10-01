---
type: "Finding"
title: "cosmosw always prefers an installed cosmos over the repo's vendored copy, even when the install is older"
description: "cosmosw always prefers an installed cosmos over the repo's vendored copy, even when the install is older"
status: "stable"
generated: {"by": "human:Biswajit Tripathy", "at": "2026-09-29T00:00:00Z"}
sources: [{"resource": "cosmos/wrapper.py", "title": "wrapper.py"}]
stale_after: "2027-03-28T00:00:00Z"
links: ["/lanes/cosmos.md", "/finding/mem_0448e271-the-watcher-started-a-dream-every-30-seconds-whi.md", "/finding/mem_1db8264f-a-claude-desktop-mcp-entry-named-cosmos-pinned-t.md", "/finding/mem_498078e0-atlas-page-4-of-8-deep-pass-diagrams-failed-unde.md", "/finding/mem_5790a327-cosmos-connect-with-no-agent-argument-failed-arg.md", "/finding/mem_6fa48630-a-repository-whose-committed-hook-command-is-old.md"]
id: "mem_5b583e8d"
aliases: ["mem_5b583e8d"]
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
meta_audit_id: "DEV-wrapper-prefers-stale-install"
meta_finding_status: "fixed"
meta_fixed_commit: "0c11381"
meta_fixed_on: "2026-09-29"
meta_found_commit: "3f80c40"
meta_locations: "`cosmos/wrapper.py:18`"
meta_raw_id: "wrapper-prefers-stale-install"
meta_severity: "medium"
meta_source_doc: "qa-2026-09-29-commands"
meta_status_at: "2026-09-29"
meta_status_note: "the wrapper runs the newer of the installed and the vendored copy; doctor shows both versions"
---

# cosmosw always prefers an installed cosmos over the repo's vendored copy, even when the install is older

**Category:** finding · **Status:** active · **Confidence:** 90%

## Details
**What** — Both copies report 0.1.0, so nothing tells them apart; a stale install silently serves old tools, old names and old renders to every agent and the plugin.

**Fix** — Stamp the vendored copy with the source commit or a content hash and a build number; the wrapper uses the vendored copy when it is newer, and doctor names the mismatch.

## Why we believe this
- Observed 1× (first 2026-09-29, last 2026-09-29); source: explicit
- Evidence file: `cosmos/wrapper.py`
- Marked fixed on 2026-09-29: the wrapper runs the newer of the installed and the vendored copy; doctor shows both versions

## Related
- [[mem_0448e271]]
- [[mem_1db8264f]]
- [[mem_498078e0]]
- [[mem_5790a327]]
- [[mem_6fa48630]]

## Links
- lane: [cosmos](/lanes/cosmos.md)
- related: [mem_0448e271](/finding/mem_0448e271-the-watcher-started-a-dream-every-30-seconds-whi.md)
- related: [mem_1db8264f](/finding/mem_1db8264f-a-claude-desktop-mcp-entry-named-cosmos-pinned-t.md)
- related: [mem_498078e0](/finding/mem_498078e0-atlas-page-4-of-8-deep-pass-diagrams-failed-unde.md)
- related: [mem_5790a327](/finding/mem_5790a327-cosmos-connect-with-no-agent-argument-failed-arg.md)
- related: [mem_6fa48630](/finding/mem_6fa48630-a-repository-whose-committed-hook-command-is-old.md)

#finding #medium #install
