---
type: Handoff
kind: handoff
branch: "main"
by: "Biswajit Tripathy"
at: "2026-09-29T15:11:06Z"
how: auto
---

Nothing was removed by accident. All of `retent`'s project commands are still there: 12 files in `.claude/commands/`, committed in `d9027209`. The screenshot shows one intended rename, plus a naming difference between plugin and project commands. **1. `intake` is now `horizon`.** The project renamed Intake to Horizon on 2026-09-22 (commit `5b289ba`). My first version of the commands brought the old `/intake` name back by mistake, and the QA pass you asked for flagged it as a reintroduced retired name. So it's `/horizon` now; that's the `cosmos:horizon` highlighted in your screenshot, "Map a feature before coding", and it's the same command. `cosmos intake "…"` still works on the command line …
