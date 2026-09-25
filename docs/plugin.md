# The cosmos plugin (Cowork, and Claude Code)

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
- **Claude Code:**

  ```
  /plugin marketplace add <owner>/cosmos
  /plugin install cosmos@cosmos
  ```

## What it does

`plugin/bin/cosmos-mcp` looks for the repository the session works in: the project directory and the working
directory and their parents, then every folder shared with the session and the folders inside it (a workspace folder
of several projects). The first one with `.cosmos/cosmosw` wins; with several, the one active most recently. It runs
that repository's own copy of cosmos (`.cosmos/cosmosw mcp`), so nothing is installed in the sandbox and the plugin is
never older than the repository's cosmos. With no cosmos repository in reach it serves one tool, `cosmos_status`, that
says so.

The tools: `cosmos_recall`, `cosmos_remember`, `cosmos_flare`, `cosmos_handoff`, `cosmos_charter`, `cosmos_why`,
`cosmos_horizon`, `cosmos_atlas`, `cosmos_lanes`. The plugin's skill (`plugin/skills/cosmos/SKILL.md`) tells the agent
when to use them: the Charter first, recall before editing, the checks and the record before stopping.

## What it does not do

- **No Gate and no pre-edit reminders in Cowork.** Both need hooks. The skill asks the agent to follow the same steps.
- **No git from the sandbox.** Inside Cowork the repository is mounted under another path; cosmos never commits,
  pushes or repairs the ledger from there (it would prune the real worktree record). The machine that owns the
  repository does that.
- **Capture does not depend on it.** The watcher on the machine reads Cowork transcripts, maps the sandbox paths
  (`/sessions/<vm>/mnt/<folder>/…`) back and keeps only the exchanges that touched the repository.
