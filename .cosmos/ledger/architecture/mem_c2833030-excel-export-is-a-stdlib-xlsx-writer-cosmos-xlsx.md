---
type: "Architecture"
title: "Excel export is a stdlib xlsx writer (cosmos/xlsx.py: zip of SpreadsheetML parts, inline strings only so no cell is ever"
description: "Excel export is a stdlib xlsx writer (cosmos/xlsx.py: zip of SpreadsheetML parts, inline strings only so no cell is ever a formula); `cosmos export`, `flares export -o *.xlsx` and the console's /api/export.xlsx all use it. Reason: cosmos is stdlib-only, so no openpyxl."
status: "stable"
generated: {"by": "human:Biswajit Tripathy", "at": "2026-09-29T00:00:00Z"}
sources: [{"resource": "cosmos/xlsx.py", "title": "xlsx.py"}]
stale_after: "2027-03-28T00:00:00Z"
links: ["/lanes/cosmos.md", "/constraint/mem_0f220612-githubs-secret-scanning-spotted-it-and-blocked-t.md", "/constraint/mem_851c75c5-pausing-cosmoss-commits-to-main-qa-asked-for-thi.md", "/constraint/mem_9e13c334-my-check-was-flawed-it-kept-the-prefixes-so-matc.md", "/constraint/mem_dcdcfe55-the-intake-left-in-the-code-is-internal-names-on.md", "/decision/mem_6eb345df-horizon-entry-now-names-horizon-and-says-flares.md"]
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

## Related
- [[mem_0f220612]]
- [[mem_851c75c5]]
- [[mem_9e13c334]]
- [[mem_dcdcfe55]]
- [[mem_6eb345df]]

## Links
- lane: [cosmos](/lanes/cosmos.md)
- related: [mem_0f220612](/constraint/mem_0f220612-githubs-secret-scanning-spotted-it-and-blocked-t.md)
- related: [mem_851c75c5](/constraint/mem_851c75c5-pausing-cosmoss-commits-to-main-qa-asked-for-thi.md)
- related: [mem_9e13c334](/constraint/mem_9e13c334-my-check-was-flawed-it-kept-the-prefixes-so-matc.md)
- related: [mem_dcdcfe55](/constraint/mem_dcdcfe55-the-intake-left-in-the-code-is-internal-names-on.md)
- related: [mem_6eb345df](/decision/mem_6eb345df-horizon-entry-now-names-horizon-and-says-flares.md)
