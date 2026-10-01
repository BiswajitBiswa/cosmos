---
type: "Lane"
title: "cosmos"
description: "13 active facts, 5 open flares, 2 people active in the last 30 days"
status: "stable"
sources: [{"resource": "/../../.claude", "title": ".claude"}, {"resource": "/../../.claude-plugin", "title": ".claude-plugin"}, {"resource": "/../../cosmos", "title": "cosmos"}, {"resource": "/../../plugin", "title": "plugin"}]
links: ["/architecture/mem_1f13b61a-slash-commands-for-every-agent-come-from-one-cat.md", "/architecture/mem_b6b76950-the-atlas-has-a-peoples-view-cosmos-atlashtml-py.md", "/architecture/mem_c2833030-excel-export-is-a-stdlib-xlsx-writer-cosmos-xlsx.md", "/constraint/mem_1192ca15-hooks-must-always-exit-0-the-gate-is-the-only-de.md", "/constraint/mem_4c8727a1-in-claude-desktop-code-tab-sessions-an-mcp-serve.md", "/constraint/mem_a1b7e320-claude-code-caps-each-hook-text-plain-stdout-add.md", "/decision/mem_043ce3de-playbooks-a-repositorys-own-long-form-agent-prom.md", "/decision/mem_1734bf56-bugs-found-by-hand-become-flares-through-one-pat.md", "/decision/mem_2b049e3f-a-flares-id-prefix-is-the-projects-lifecycle-sta.md", "/decision/mem_4efbf3d7-releases-and-their-repairs-reach-every-project-b.md", "/decision/mem_55db62b9-recall-is-made-visible-with-the-hooks-systemmess.md", "/decision/mem_5cfd6c9b-commit-note-by-biswajit-tripathy-autopilot-from.md", "/workflow/mem_9fe4f5ce-horizon-notes-exist-only-when-someone-asks-for-o.md"]
tags: ["lane", "cosmos"]
---


# Lane · cosmos

13 active facts, 5 open flares, 2 people active in the last 30 days.

**Overlap:** 2 people active here this month: BiswajitBiswa, Biswajit Tripathy.

## Open flares

- [PROD-048c42](/finding/mem_07187b11-mcp-entries-cosmos-writes-start-python3-which-do.md) [high] MCP entries cosmos writes start python3, which does not exist on Windows, so the cosmos tools never start there
- [PROD-0180e8](/finding/mem_6fa48630-a-repository-whose-committed-hook-command-is-old.md) [medium] A repository whose committed hook command is older than the user-level one runs every hook twice (two Gates, two briefin
- [PROD-2e63ea](/finding/mem_b9901dfb-a-session-opened-in-a-subfolder-of-the-repositor.md) [medium] A session opened in a subfolder of the repository gets no briefing, facts or capture: load_config takes the folder it is
- [PROD-459673](/finding/mem_dbc7ae4e-cosmos-connect-codex-write-user-pins-codexs-user.md) [medium] cosmos connect codex --write-user pins Codex's user-level cosmos MCP server to the first repository and never updates it
- [PROD-fec6d4](/finding/mem_fcae919e-a-dream-that-started-before-cosmos-was-updated-r.md) [low] A dream that started before cosmos was updated rewrites slash command files with its stale in-memory catalogue at the en

## Facts

### Architecture
- [Slash commands for every agent come from one catalogue in cosmos/commands.py (Claude .claude/commands, Gemini .gemini/commands TOML, Cursor ](/architecture/mem_1f13b61a-slash-commands-for-every-agent-come-from-one-cat.md)
- [The Atlas has a people's view: cosmos/atlas_html.py renders every ledger/atlas/*.md into ledger/atlas/atlas.html (sidebar, pan/zoom/fit/full](/architecture/mem_b6b76950-the-atlas-has-a-peoples-view-cosmos-atlashtml-py.md)
- [Excel export is a stdlib xlsx writer (cosmos/xlsx.py: zip of SpreadsheetML parts, inline strings only so no cell is ever a formula); `cosmos](/architecture/mem_c2833030-excel-export-is-a-stdlib-xlsx-writer-cosmos-xlsx.md)

### Constraint
- [Hooks must always exit 0; the Gate is the only deliberate exit-2 and it never fires twice in one turn (stop_hook_active).](/constraint/mem_1192ca15-hooks-must-always-exit-0-the-gate-is-the-only-de.md)
- [In Claude Desktop Code-tab sessions an MCP server named cosmos in claude_desktop_config.json shadows the project's .mcp.json server, so cosm](/constraint/mem_4c8727a1-in-claude-desktop-code-tab-sessions-an-mcp-serve.md)
- [Claude Code caps each hook text (plain stdout, additionalContext, systemMessage) at 10,000 characters; longer text is saved to a file and th](/constraint/mem_a1b7e320-claude-code-caps-each-hook-text-plain-stdout-add.md)

### Decision
- [Playbooks: a repository's own long-form agent prompts (master QA protocol, runbooks) are detected by cosmos/playbooks.py (name or first head](/decision/mem_043ce3de-playbooks-a-repositorys-own-long-form-agent-prom.md)
- [Bugs found by hand become flares through one path: cosmos/audit.py import_items (also used by the JSON import and cosmos_flare). cosmos flar](/decision/mem_1734bf56-bugs-found-by-hand-become-flares-through-one-pat.md)
- [A flare's id prefix is the project's lifecycle stage read from git when it is filed (qa/* → QA, uat/staging → UAT, release/* or rc tag → RC,](/decision/mem_2b049e3f-a-flares-id-prefix-is-the-projects-lifecycle-sta.md)
- [Releases and their repairs reach every project by themselves (cosmos/upgrade.py): a session start checks PyPI at most once a day per machine](/decision/mem_4efbf3d7-releases-and-their-repairs-reach-every-project-b.md)
- [Recall is made visible with the hook's systemMessage: SessionStart, UserPromptSubmit and PreToolUse print JSON with a one-line cosm◎s notice](/decision/mem_55db62b9-recall-is-made-visible-with-the-hooks-systemmess.md)
- [Commit note by Biswajit Tripathy: autopilot from parent folders, bugs recorded by hand, recall you can see, a briefing under the hook cap, u](/decision/mem_5cfd6c9b-commit-note-by-biswajit-tripathy-autopilot-from.md)

### Workflow
- [Horizon notes exist only when someone asks for one (/horizon, cosmos horizon, cosmos_horizon, the console's Horizon page); nothing creates t](/workflow/mem_9fe4f5ce-horizon-notes-exist-only-when-someone-asks-for-o.md)

## People

- BiswajitBiswa
- Biswajit Tripathy
