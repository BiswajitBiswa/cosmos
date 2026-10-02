---
type: "Decision"
title: "Horizon is the owner's SDLC product built on cosmos: its API imports this repository's source as an editable path depend"
description: "Horizon (~/Desktop/shyftlabs/horizon, built in the HORIZON session from ~/Desktop/shyftlabs) is the owner's SDLC product built on cosmos: its API imports this repository's source as an editable path dependency, and scripts/mirror-cosmos.sh refreshes horizon/.cosmos/vendor from it on every pnpm dev. So a cosmos change reaches Horizon without a release, and Horizon is cosmos's feedback loop: HORIZON reports cosmos problems to the COSMOS session, which files and fixes them here; Horizon never patches cosmos (owner, 2026-10-07)."
status: "stable"
generated: {"by": "human:Biswajit Tripathy", "at": "2026-10-07T00:00:00Z"}
stale_after: "2027-04-05T00:00:00Z"
links: ["/lanes/horizon.md"]
id: "mem_5dfd6673"
aliases: ["mem_5dfd6673"]
category: "decision"
lane: "horizon"
cosmos_status: "active"
confidence: 0.95
importance: 0.95
source: "explicit"
created: "2026-10-07"
updated: "2026-10-07"
last_verified: "2026-10-07"
evidence_count: 1
authors: ["Biswajit Tripathy"]
valid_from: "2026-10-07"
---

# Horizon (~/Desktop/shyftlabs/horizon, built in the HORIZON session from ~/Desktop/shyftlabs) is the owner's SDLC product built on cosmos: its API imports this repository's source as an editable path dependency, and scripts/mirror-cosmos.sh refreshes horizon/.cosmos/vendor from it on every pnpm dev. So a cosmos change reaches Horizon without a release, and Horizon is cosmos's feedback loop: HORIZON reports cosmos problems to the COSMOS session, which files and fixes them here; Horizon never patches cosmos (owner, 2026-10-07).

**Category:** decision · **Status:** active · **Confidence:** 95%

## Why we believe this
- Observed 1× (first 2026-10-07, last 2026-10-07); source: explicit

## Links
- lane: [horizon](/lanes/horizon.md)
