---
name: cosmos
description: Use when working in a repository that has a .cosmos/ folder (the team's cosmos), before planning or editing code there, and before finishing a change. Gives the team's rules (Charter), what the team already knows about the files (Ledger facts and open flares), the architecture (Atlas) and the last handoff, and records what was learned.
---

# cosmos

This repository keeps its team memory in `.cosmos/`. Use it the way a new teammate would use the team's notes.

**Before you start**
- Call `cosmos_charter` once and follow it over your own style. Without the tools, read `.cosmos/charter.md`.
- Call `cosmos_recall` with the files you are about to change and a few words about the task. It returns the facts, rules and open flares anchored to them. Without the tools, read `.cosmos/ledger/_index.md` and the notes it links for those files.
- For structural changes, read `.cosmos/ledger/atlas/containers.md` and `data-flow.md`.

**Before you stop**
- Run the tests for the files you touched and cite each change as `path/to/file.ext:line`.
- A large change (5+ files or 4,000+ characters): run a dead-code scan (vulture for Python, knip for JavaScript/TypeScript) and remove what is unused in what you touched.
- Record what the team should keep: `cosmos_remember` for a decision with its reason, a constraint or a correction the user made (kind `rule` only for something the user stated as a rule). `cosmos_flare` for a bug you found, fixed or not, without asking. `cosmos_handoff` when you stop with work unfinished.

`.cosmos/` is committed in the branch like code and cosmos commits it by itself: do not stage, revert or delete its files, and keep them when resolving a merge. If `.cosmos/` is a separate git worktree (the opt-in `cosmos` branch), never merge, rebase or cherry-pick that branch into another one.
