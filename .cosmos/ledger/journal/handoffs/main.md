---
type: Handoff
kind: handoff
branch: "main"
by: "Biswajit Tripathy"
at: "2026-10-01T10:58:42Z"
how: auto
---

The Gate's points are done: 1. **Dead-code scan:** vulture found one unused import, `iter_turns` at `cosmos/hooks.py:17`, left over from 0.1.0. Removed, and 154 tests pass. 2. **Exact locations of today's changes:** - `cosmos/upgrade.py:72` `_get` — downloads with certificate checking kept on, falling back to `certifi` or the system bundle. - `cosmos/upgrade.py:170` `run` — check PyPI, upgrade the bundled copy, repair, commit. - `cosmos/upgrade.py:210` `maybe_background` — the daily background check, started from a session start. - `cosmos/upgrade.py:282` `_step_codex_listing` — writes the Codex plugin listing. - `cosmos/upgrade.py:298` `_step_desktop_pin` — renames the pinned Desktop entry, …
