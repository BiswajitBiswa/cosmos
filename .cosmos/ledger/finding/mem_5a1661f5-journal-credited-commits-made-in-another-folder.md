---
type: "Finding"
title: "Journal credited commits made in another folder (cd /tmp/x && git commit) to this repository"
description: "Journal credited commits made in another folder (cd /tmp/x && git commit) to this repository"
status: "stable"
generated: {"by": "human:Biswajit Tripathy", "at": "2026-10-01T00:00:00Z"}
sources: [{"resource": "cosmos/journal.py", "title": "journal.py"}, {"resource": "cosmos/watch.py", "title": "watch.py"}]
stale_after: "2027-03-30T00:00:00Z"
links: ["/lanes/cosmos.md", "/finding/mem_10ab2ec4-console-docs-said-horizon-notes-are-saved-in-cos.md", "/finding/mem_d4c37ea1-slack-cards-and-the-slack-report-told-people-to.md", "/finding/mem_e522e056-console-rendered-every-fact-rule-and-flare-at-on.md", "/finding/mem_f2ac4098-a-token-pasted-in-a-prompt-was-written-verbatim.md", "/finding/mem_fcf6d908-new-slash-commands-reintroduced-names-retired-in.md"]
id: "mem_5a1661f5"
aliases: ["mem_5a1661f5"]
category: "finding"
lane: "cosmos"
cosmos_status: "active"
confidence: 0.9
importance: 0.45
source: "explicit"
created: "2026-10-01"
updated: "2026-10-01"
last_verified: "2026-10-01"
evidence_count: 1
files: ["cosmos/journal.py", "cosmos/watch.py"]
tags: ["finding", "low"]
authors: ["Biswajit Tripathy"]
valid_from: "2026-10-01"
meta_audit_id: "PROD-ac2747"
meta_finding_status: "fixed"
meta_fixed_commit: "4222433"
meta_fixed_on: "2026-10-01"
meta_found_commit: "4222433"
meta_locations: "cosmos/journal.py:45 \u00b7 cosmos/watch.py:57"
meta_raw_id: "ac2747"
meta_severity: "low"
meta_source_doc: "manual"
meta_status_at: "2026-10-01"
meta_status_note: "fixed in the working tree (uncommitted): cosmos/journal.py:30 _elsewhere"
---

# Journal credited commits made in another folder (cd /tmp/x && git commit) to this repository

**Category:** finding · **Status:** active · **Confidence:** 90%

## Details
**What** — commits_in parsed every git commit in a turn's shell commands wherever it ran; a throwaway test repo's 'init' commit appeared in .cosmos/ledger/journal/2026-10-01.md

**Impact** — wrong journal lines; dreams turn commit messages into facts

**Fix** — commits_in(commands, root) skips a commit after a cd out of root (absolute path elsewhere, a variable or mktemp folder, ..); test_a_commit_made_in_another_folder_is_not_this_repositorys

## Why we believe this
- Observed 1× (first 2026-10-01, last 2026-10-01); source: explicit
- Evidence file: `cosmos/journal.py`
- Evidence file: `cosmos/watch.py`
- Marked fixed on 2026-10-01: fixed in the working tree (uncommitted): cosmos/journal.py:30 _elsewhere

## Related
- [[mem_10ab2ec4]]
- [[mem_d4c37ea1]]
- [[mem_e522e056]]
- [[mem_f2ac4098]]
- [[mem_fcf6d908]]

## Links
- lane: [cosmos](/lanes/cosmos.md)
- related: [mem_10ab2ec4](/finding/mem_10ab2ec4-console-docs-said-horizon-notes-are-saved-in-cos.md)
- related: [mem_d4c37ea1](/finding/mem_d4c37ea1-slack-cards-and-the-slack-report-told-people-to.md)
- related: [mem_e522e056](/finding/mem_e522e056-console-rendered-every-fact-rule-and-flare-at-on.md)
- related: [mem_f2ac4098](/finding/mem_f2ac4098-a-token-pasted-in-a-prompt-was-written-verbatim.md)
- related: [mem_fcf6d908](/finding/mem_fcf6d908-new-slash-commands-reintroduced-names-retired-in.md)

#finding #low
