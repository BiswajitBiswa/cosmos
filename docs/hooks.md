# Hooks

`cosmos init` merges these entries into `.claude/settings.json` (other hooks untouched):

```json
{ "hooks": {
  "SessionStart":     [{ "hooks": [{ "type": "command", "command": "<hook>", "timeout": 10 }] }],
  "UserPromptSubmit": [{ "hooks": [{ "type": "command", "command": "<hook>", "timeout": 10 }] }],
  "Stop":             [{ "hooks": [{ "type": "command", "command": "<hook>", "timeout": 20 }] }],
  "PreCompact":       [{ "hooks": [{ "type": "command", "command": "<hook>", "timeout": 20 }] }],
  "SessionEnd":       [{ "hooks": [{ "type": "command", "command": "<hook>", "timeout": 20 }] }]
}}
```

where `<hook>` is

```sh
d="${CLAUDE_PROJECT_DIR:-.}"; [ -f "$d/.cosmos/cosmosw" ] && exec python3 "$d/.cosmos/cosmosw" hook; exit 0
```

It is anchored to the project directory Claude Code passes to hooks, so a session that `cd`s into a sibling repository still reaches this repository's wrapper; in a repository without `.cosmos/` it exits 0 silently; `exec` keeps the Gate's exit code 2. Re-running `cosmos init` migrates an older command in place.

One entrypoint, dispatched on `hook_event_name` from the stdin JSON:

- **SessionStart** → stdout = orientation block (top N active facts). Claude Code injects stdout as context.
- **UserPromptSubmit** → stdout = facts ranked against the prompt (token + path overlap × confidence × importance × recency).
- **Stop / PreCompact / SessionEnd** → read `transcript_path` from the last saved byte offset (per session, in `.cosmos/state/`), extract observations, redact, append. Runs in ~50 ms for a typical turn.

Guarantees: always exit 0; all errors go to `.cosmos/state/hook.log`; nothing is sent anywhere.

If `cosmos` is not on PATH when you run `init`, the command is written as `<python> -m cosmos hook`. Override with `cosmos init --command "..."`.
