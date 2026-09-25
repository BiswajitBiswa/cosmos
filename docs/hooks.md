# Hooks

`cosmos init` merges these entries into the repository's `.claude/settings.json` and, once per machine, into
`~/.claude/settings.json` (other hooks untouched; `cosmos init --no-user-hooks` skips the user level):

```json
{ "hooks": {
  "SessionStart":     [{ "hooks": [{ "type": "command", "command": "<hook>", "timeout": 10 }] }],
  "UserPromptSubmit": [{ "hooks": [{ "type": "command", "command": "<hook>", "timeout": 10 }] }],
  "PreToolUse":       [{ "matcher": "Edit|Write|MultiEdit|NotebookEdit", "hooks": [{ "type": "command", "command": "<hook>", "timeout": 10 }] }],
  "Stop":             [{ "hooks": [{ "type": "command", "command": "<hook>", "timeout": 20 }] }],
  "PreCompact":       [{ "hooks": [{ "type": "command", "command": "<hook>", "timeout": 20 }] }],
  "SessionEnd":       [{ "hooks": [{ "type": "command", "command": "<hook>", "timeout": 20 }] }]
}}
```

`<hook>` finds the repository's wrapper: in the project directory Claude Code passes to hooks; failing that, in the
main checkout (a worktree on a branch that does not carry the wiring still reaches it); failing that, on a fresh clone,
it attaches `.cosmos/` from `origin/cosmos` first. In a repository without cosmos it exits 0 silently. The user-level
entry is what makes every worktree and every repository covered, including sessions that were already open when
`cosmos init` ran.

## One entrypoint, dispatched on `hook_event_name`

- **SessionStart** → the briefing: the Charter summary, the top facts, the branch's last handoff, the Atlas status and
  any warning (for example, the `cosmos` branch merged into this branch). Also refreshes the vendored copy and starts the
  watcher if none runs.
- **UserPromptSubmit** → facts ranked against the prompt (BM25 × confidence × importance × recency). A session that
  never got the briefing, because cosmos arrived after it started, gets it with this prompt, once.
- **PreToolUse** (edits only) → what the team knows about the file about to change: open flares and active facts
  anchored to the file or to a folder that contains it (`frontend/src/`), explicit rules first. Once per file per session.
- **Stop** → the Gate (see [charter and gate](charter-and-gate.md)); exit 2 holds the turn once with the exact list.
  Then capture: the turn's journal line (ask, files, commits, tests, branch) and a byte range of the transcript
  registered for the model to read at the next dream. The final message of an editing turn becomes the branch's handoff.
- **PreCompact / SessionEnd** → capture, as for Stop.

## Guarantees

Every hook exits 0 on any error (the Gate's deliberate 2 is the only other code); errors go to
`.cosmos/state/hook.log`; nothing is sent anywhere. `COSMOS_HOOKS_OFF=1` turns every hook into a no-op for one
process; cosmos sets it on its own headless runs (the Atlas deep pass) so they neither capture nor gate themselves.

## Where hooks do not run

- **Cowork** runs Claude Code in a sandbox with only its own settings, so neither the repository's nor the user's hooks
  run there. Capture still happens: the watcher reads Cowork transcripts on the machine, maps the sandbox paths
  (`/sessions/<vm>/mnt/<folder>/…`) back and keeps only the exchanges that touched the repository. The tools come from
  the cosmos plugin (this repository is its marketplace), which finds the shared folder with `.cosmos/` and serves it;
  Cowork starts a process per message, so an installed plugin is there from the next message. The Gate and the
  pre-edit reminders need hooks and are not available in Cowork; the plugin's skill asks the agent to follow the same steps.
- **Codex, Gemini CLI and other agents** read the instruction files (`AGENTS.md`, `GEMINI.md`, …) and call the MCP
  tools; the watcher follows their session files.

If `cosmos` is not on PATH when you run `init`, the command is written as `<python> -m cosmos hook`. Override with
`cosmos init --command "..."`.
