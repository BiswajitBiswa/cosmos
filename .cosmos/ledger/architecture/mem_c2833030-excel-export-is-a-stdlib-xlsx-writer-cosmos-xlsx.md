---
type: "Architecture"
title: "Excel export is a stdlib xlsx writer (cosmos/xlsx.py: zip of SpreadsheetML parts, inline strings only so no cell is ever"
description: "Excel export is a stdlib xlsx writer (cosmos/xlsx.py: zip of SpreadsheetML parts, inline strings only so no cell is ever a formula); `cosmos export`, `flares export -o *.xlsx` and the console's /api/export.xlsx all use it. Reason: cosmos is stdlib-only, so no openpyxl."
status: "stable"
generated: {"by": "human:Biswajit Tripathy", "at": "2026-09-29T00:00:00Z"}
sources: [{"resource": "cosmos/xlsx.py", "title": "xlsx.py"}]
stale_after: "2027-03-28T00:00:00Z"
links: ["/lanes/cosmos.md"]
id: "mem_c2833030"
aliases: ["mem_c2833030"]
category: "architecture"
lane: "cosmos"
cosmos_status: "active"
confidence: 0.95
importance: 0.95
source: "explicit"
created: "2026-09-29"
updated: "2026-09-29"
last_verified: "2026-09-29"
evidence_count: 1
files: ["cosmos/xlsx.py"]
authors: ["Biswajit Tripathy"]
valid_from: "2026-09-29"
---

# Excel export is a stdlib xlsx writer (cosmos/xlsx.py: zip of SpreadsheetML parts, inline strings only so no cell is ever a formula); `cosmos export`, `flares export -o *.xlsx` and the console's /api/export.xlsx all use it. Reason: cosmos is stdlib-only, so no openpyxl.

**Category:** architecture · **Status:** active · **Confidence:** 95%

## Why we believe this
- Observed 1× (first 2026-09-29, last 2026-09-29); source: explicit
- Evidence file: `cosmos/xlsx.py`

## Links
- lane: [cosmos](/lanes/cosmos.md)
