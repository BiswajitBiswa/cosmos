# The cosmos plugin (Cowork, Claude Code and Codex)

## Why a plugin

Cowork runs Claude Code in a sandbox. It loads only its own settings, so a repository's hooks and the user-level hooks
never run there, and it takes MCP servers from plugins, not from Claude Desktop's local MCP config. The plugin is how a
Cowork session gets the cosmos tools. Claude Code does not need it (hooks and `.mcp.json` already connect it), but it
works there too.

## Install

This repository is a plugin marketplace (`.claude-plugin/marketplace.json`) with one plugin, **cosmos** (`plugin/`).

- **Cowork:** open Plugins, add a marketplace from GitHub with this repository's `owner/cosmos` path, then install **cosmos**.
  Cowork starts a fresh process for every message, so the tools are there from your next message, in the session you
  already have open.
- **Claude desktop app (Code tab):** `/plugin` is a command of the Claude Code CLI and is not available in the app. Use
  the app's Plugins screen, or run in any terminal:

  ```bash
  claude plugin marketplace add <owner>/cosmos
  claude plugin install cosmos@cosmos
  ```
- **Claude Code CLI:** the same two lines, or `/plugin marketplace add <owner>/cosmos` and `/plugin install cosmos@cosmos`
  inside a session.

- **Codex (app, CLI, IDE extension):** the same repository is a Codex marketplace. In the Codex app, open **Plugins**,
  add a marketplace from GitHub (`BiswajitBiswa/cosmos`), then install **cosmos**. In a terminal: `codex plugin marketplace add BiswajitBiswa/cosmos`, then install
  **cosmos** from `/plugins`. Nothing else to run: no `pip install`, no `cosmos connect codex`, no `cosmos watch`
  (see [Codex](#codex) below). In a repository that has cosmos there is not even that: cosmos writes the repository's
  own listing (`.agents/plugins/marketplace.json`, pointing at this repository's `plugin/`), Codex shows it in the
  Plugins screen of any thread opened there, and a teammate clicks **Install**. The listing keeps the team's other
  entries; `"codex": {"listing": false}` in `.cosmos/config.json` leaves the file alone.

If the tools list shows only `cosmos_status`, the plugin found no folder with `.cosmos/` from where the session started:
share the repository folder (Cowork), or open the session in the repository.

## What it does

`plugin/bin/cosmos-mcp` looks for the repository the session works in: the project directory and the working
directory and their parents, then every folder shared with the session and the folders inside it (a workspace folder
of several projects). The first one with `.cosmos/cosmosw` wins; with several, the one active most recently. It runs
that repository's own copy of cosmos (`.cosmos/cosmosw mcp`), so nothing is installed in the sandbox and the plugin is
never older than the repository's cosmos. With no cosmos repository in reach it serves one tool, `cosmos_status`, that
says so.

The tools: `cosmos_recall`, `cosmos_remember`, `cosmos_flare`, `cosmos_handoff`, `cosmos_charter`, `cosmos_why`,
`cosmos_horizon`, `cosmos_atlas`, `cosmos_lanes`. The commands (`plugin/commands/`, the same catalogue `cosmos connect`
writes into a repository): `/cosmos:cosmos`, `/cosmos:recall`, `/cosmos:remember`, `/cosmos:flare`, `/cosmos:flares`,
`/cosmos:qa`, `/cosmos:reconcile`, `/cosmos:lanes`, `/cosmos:horizon`, `/cosmos:handoff`, `/cosmos:atlas`. The plugin's
skill (`plugin/skills/cosmos/SKILL.md`) tells the agent when to use the tools: the Charter first, recall before editing,
the checks and the record before stopping.

The repository's cosmos is started with `python3`: an installed cosmos wins over the vendored copy in `.cosmos/vendor`.
If that install is older than the repository's copy the tools are the older ones; `cosmos doctor` lists every `cosmos`
on PATH and the Python it belongs to.

## Codex

Codex reads the plugin's own manifest, `plugin/.codex-plugin/plugin.json` (Claude reads `plugin/.claude-plugin/`; the
skill and the commands are shared). Two things differ from Claude:

- **Hooks do the setup.** At the start of each thread and on each prompt, `plugin/bin/cosmos-codex-hook` finds the
  repository the thread is in (its folder or one above; a folder holding several repositories answers for each) and
  hands the event to that repository's own cosmos. What it prints becomes the model's context: the Charter and facts at
  the start, the facts for each prompt. The same call starts the watcher, which captures Codex sessions. There is no
  Gate in Codex: a Stop hook that exits 2 would block the thread.
- **One MCP server for every repository.** Codex starts a plugin's MCP server in the plugin's folder and does not say
  which project the thread is in. `plugin/bin/cosmos-codex-mcp` answers the handshake itself and sends each tool call
  to the repository the hook saw last (recorded in `~/.config/cosmos/codex-last-repo.json`; a thread in a folder
  without cosmos clears it, so nothing reaches the previous repository's ledger). That repository's committed
  `.cosmos/cosmosw mcp` serves the call.

Python must be installed (cosmos is Python; nothing is installed with pip). On Windows, where Python is `python`, the
hook falls back to it and points the plugin's MCP server at that interpreter; restart Codex once after the first
thread for the tools to start.

Codex shows the cosmos mark (`plugin/assets/icon.png`, gold brand colour) on the plugin and its chip. Claude Code has no icon
field for plugins, commands or skills, and does not draw MCP server icons yet, so there it stays a letter or globe.

## What it does not do

- **No Gate and no pre-edit reminders in Cowork.** Both need hooks. The skill asks the agent to follow the same steps.
- **No git from the sandbox.** Inside Cowork the repository is mounted under another path; cosmos never commits,
  pushes or repairs the ledger from there (it would prune the real worktree record). The machine that owns the
  repository does that.
- **Capture does not depend on it.** The watcher on the machine reads Cowork transcripts, maps the sandbox paths
  (`/sessions/<vm>/mnt/<folder>/…`) back and keeps only the exchanges that touched the repository.
