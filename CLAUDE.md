<!-- cosmos:start -->
## Cosmos — how this team works with AI

1. **Charter** `.cosmos/charter.md` — the team's coding style, testing and review rules. Follow it over any personal preference.
2. **Ledger** `.cosmos/ledger/` — one note per fact with evidence, grouped by lane (`_index.md`). Consult before changing architecture, conventions or workflows.
3. **Atlas** `.cosmos/ledger/atlas/` — architecture diagrams generated from the repo. Read `containers.md` before structural changes.
4. **Gate** — before you stop: run the tests for files you touched, cite `file:line` for each change, address open flares on those files, self-review against the Charter, and record what the team learned (cosmos_remember kind=fact; cosmos_flare for bugs found - fixed or open - without asking).
Explicit rules outrank inferred facts.

The rules are in `.cosmos/charter.md` and the facts, by lane, in `.cosmos/ledger/_index.md`. `.cosmos/` is committed in this branch like code and travels with every branch made from it; cosmos commits it by itself (never stage or revert its files, and keep them when resolving a merge). Claude Code receives the relevant ones through hooks; any other agent reads those two files or calls `cosmos_recall` before changing code it did not write.

`cosmos why <id>` explains a fact · `remember: …` adds a rule · `flare: …` files a flare · `cosmos horizon "…"` maps a feature before coding
Slash commands (Claude Code, Gemini CLI, Cursor, Copilot, Windsurf; Codex: /prompts:cosmos-…): /cosmos /recall /remember /flare /flares /qa /reconcile /lanes /horizon /handoff /atlas. Asked for one where it is not installed, do what `.claude/commands/<name>.md` says.
<!-- cosmos:end -->
