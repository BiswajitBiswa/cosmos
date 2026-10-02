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

### Large changes

A turn that edits `large_change_files` (5) or more code files, or `large_change_chars` (4,000) or more characters, runs the
`large_change_checks` the repository configures. Each check names the files it applies to (`when`), the command patterns that
satisfy it (`patterns`) and the command to suggest. The Gate holds the turn until a matching command ran.

Every repository gets four checks by default, from the Charter template: a vulture dead-code scan when Python changed, a knip scan (unused files, exports and dependencies) when JavaScript or TypeScript changed, and a security scan, bandit for Python and semgrep for JavaScript, TypeScript, Go, Java, Kotlin and Ruby. A check can carry its own `ask` (what the agent does with the results). A repository can replace them in its own `gate:` block, for example to scan only its source folders:

```json
"large_change_checks": [
  {"name": "dead-code scan (vulture)", "patterns": ["vulture"], "when": ["**/*.py"], "command": "python3 -m vulture src --min-confidence 80"},
  {"name": "unused exports scan (knip)", "patterns": ["knip"], "when": ["web/**"], "command": "cd web && npx knip"}
]
```

The agent removes the unused and redundant code it finds in what it touched, compacts duplicated logic, and names false positives
(framework entry points, routes, fixtures) instead of deleting them.

## Security, on every turn

Whatever the size of the change, the Gate reads every file the turn touched (code, docs and config) for:

- **a credential**: provider keys and tokens, private keys, a password in a URL. Obvious placeholders (`…EXAMPLE`,
  `user:pass@`), local or docker-compose database URLs, and a line marked `cosmos: allow-secret` are left alone. The
  Gate names the file and line, never the value.
- **hidden characters**: bidi overrides and isolates (Trojan Source), tag characters, zero-width spaces and word joiners.
  The zero-width joiner inside an emoji, RTL marks and byte-order marks are ordinary text.
- **text that steers an agent**, in the files agents read as instructions (`CLAUDE.md`, `AGENTS.md`, `GEMINI.md`, rules,
  playbooks, commands, skills, `.cosmos/`): "ignore previous instructions", a new system prompt, keeping something from
  the user, piping a download into a shell. cosmos puts these files in front of every agent, so a poisoned one would
  reach every session.

A changed dependency manifest (`requirements*.txt`, `pyproject.toml`, `package.json` and lock files, `go.mod`,
`Cargo.toml`, `Gemfile`) holds the turn until its audit ran: pip-audit, npm audit, govulncheck, cargo audit or bundle
audit. `"security": false` in the `gate:` block turns these checks off.

A ledger note that reads like instructions to an agent is withheld from briefings, recall and the rules until a person
looks at it; `cosmos scan --allow <id>` shows a deliberate one (a quoted prompt-injection test case) again.
`cosmos scan` runs the same checks over every tracked file; `--tools` also runs bandit, pip-audit, npm audit, semgrep
and gitleaks when they are installed. On retent (4,106 tracked files, 2026-10-02) it reported one withheld note, a
quoted injection test, and one URL with credentials in a test.
