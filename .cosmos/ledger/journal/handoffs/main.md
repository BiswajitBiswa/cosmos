---
type: Handoff
kind: handoff
branch: "main"
by: "Biswajit Tripathy"
at: "2026-09-29T14:52:37Z"
how: auto
---

Because cosmos is built that way: it commits the ledger by itself but never pushes. In the default mode, the ledger lives in your own branch: - **What it commits:** it commits `.cosmos/` to the branch you're on every 10 minutes and after each dream, touching only `.cosmos/` files. - **Where that happens:** `sync_background` in `cosmos/sync.py` commits and returns, with no push; `cosmos doctor` shows it as "push: never — .cosmos/ … goes out when you push it". - **Why:** pushing your branch is your decision. An automatic push would also send your unfinished work on that branch, and some projects forbid it; `retent`'s owner has a "never push" rule, for example. - **The exception:** only the opt …
