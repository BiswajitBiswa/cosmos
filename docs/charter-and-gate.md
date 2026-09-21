# Charter and Gate

## Charter — one working agreement for every AI session
`.cosmos/charter.md` is prose the team owns: how we write code, how we test, how we point at things, how we review our own work, architecture rules. It is committed and changed in pull requests. Every Claude Code session on every machine receives a compact version of it at **SessionStart**, before the first prompt, so individual preferences stop leaking into the codebase.

- `cosmos charter` prints it · `cosmos charter edit` opens it · `cosmos charter add "rule" [--section "How we test"]` appends a bullet **and** records it as an explicit rule in the ledger.
- Explicit rules typed in a session (`remember: …`) are shown next to the charter and outrank any inferred fact.
- The Charter page in `cosmos ui` shows the prose, the explicit rules and the Gate settings, and lets you add a rule.

## Gate — the checklist the machine applies
The Gate runs on Claude Code's **Stop** event. It looks at the current turn only (everything since the last human message):

| check | when it applies | what Claude is told |
|---|---|---|
| tests ran | code files were edited (per `code_globs`, minus `skip_globs`) and no command matched `test_patterns` | run the tests covering the edited files, or state explicitly what was not tested |
| precise references | code files were edited and the summary has no `path/to/file.ext:line` | cite the exact location of each change |
| findings addressed | an open finding anchors to an edited file and its id is not mentioned | address or explicitly defer each finding |
| self-review | any of the above | re-read the diff against the Charter, then stop |

When something is missing the hook exits **2** with that list; Claude continues, does the work, and stops again. `stop_hook_active` is honoured, so a turn is held at most once — no loops. Documentation-only edits are never gated. Everything else in cosmos still exits 0.

Configuration lives in the charter frontmatter (`gate: {...}`) or `.cosmos/config.json → gate`: `enabled`, `require_tests`, `require_refs`, `test_patterns`, `code_globs`, `skip_globs`. `cosmos gate` shows the effective rules; `cosmos gate --transcript FILE` dry-runs it on a saved session.
