---
type: Index
title: Ledger index
okf_version: "0.2"
tags: ["cosmos", "moc"]
---

# Ledger index

40 memories · 38 active · 0 contradicted · 1 stale candidates · 4 lanes

Charter: [[charter]] · Atlas: [[inventory]] · [[containers]] · [[deployment]] · [[api]]

## Lane · cosmos
### Architecture
- [[mem_1f13b61a-slash-commands-for-every-agent-come-from-one-cat|Slash commands for every agent come from one catalogue in cosmos/commands.py (Claude .claude/commands, Gemini .gemini/commands TOML, Cursor .cursor/commands, Copilot .github/prompts, Windsurf .windsurf/workflows, Codex only ~/.codex/prompts via --write-user, plugin/commands for the plugin). Files carrying 'written by cosmos' are rewritten; unmarked files are the team's own and never overwritten. plugin/commands must be regenerated when the catalogue changes (a test fails otherwise).]]
- [[mem_b6b76950-the-atlas-has-a-peoples-view-cosmos-atlashtml-py|The Atlas has a people's view: cosmos/atlas_html.py renders every ledger/atlas/*.md into ledger/atlas/atlas.html (sidebar, pan/zoom/fit/full-screen diagrams, cosmos theme) after each build and deep pass; --format md or atlas.format md skips it. The Markdown stays the source agents and dreams read. The page reuses the console's mmdFix by extracting it from ui.HTML, so the Mermaid fixes have one copy.]]
- [[mem_c2833030-excel-export-is-a-stdlib-xlsx-writer-cosmos-xlsx|Excel export is a stdlib xlsx writer (cosmos/xlsx.py: zip of SpreadsheetML parts, inline strings only so no cell is ever a formula); `cosmos export`, `flares export -o *.xlsx` and the console's /api/export.xlsx all use it. Reason: cosmos is stdlib-only, so no openpyxl.]]
### Constraint
- [[mem_1192ca15-hooks-must-always-exit-0-the-gate-is-the-only-de|Hooks must always exit 0; the Gate is the only deliberate exit-2 and it never fires twice in one turn (stop_hook_active).]]
- [[mem_4c8727a1-in-claude-desktop-code-tab-sessions-an-mcp-serve|In Claude Desktop Code-tab sessions an MCP server named cosmos in claude_desktop_config.json shadows the project's .mcp.json server, so cosmos_* tools write to that pinned repository. session_start warns when CLAUDE_CODE_ENTRYPOINT=claude-desktop; agents then record with python3 -m cosmos / .cosmos/cosmosw on the command line.]]
- [[mem_a1b7e320-claude-code-caps-each-hook-text-plain-stdout-add|Claude Code caps each hook text (plain stdout, additionalContext, systemMessage) at 10,000 characters; longer text is saved to a file and the model sees only a 2,000-character preview it is not asked to read. So session_start keeps the briefing under retrieval.session_start_chars (9,000) via _fit, and each explicit rule in the Charter summary is one 220-character line with its id. Measured 2026-10-01: retent's briefing was 13,326 chars (12 rules = 8,034), now 8,157.]]
### Decision
- [[mem_043ce3de-playbooks-a-repositorys-own-long-form-agent-prom|Playbooks: a repository's own long-form agent prompts (master QA protocol, runbooks) are detected by cosmos/playbooks.py (name or first heading says protocol/playbook/runbook/master prompt, and the text is written for an agent) plus .cosmos/playbooks/; each becomes a slash command for every agent and /qa follows the QA one. Reason: the owner wanted RETEN's master and QA prompts reusable by any project and detected automatically. cosmos playbooks add <file|qa> brings one in.]]
- [[mem_1734bf56-bugs-found-by-hand-become-flares-through-one-pat|Bugs found by hand become flares through one path: cosmos/audit.py import_items (also used by the JSON import and cosmos_flare). cosmos flares add (typed, --from .txt/.csv/.tsv/.xlsx/.json/-) and the console's Record bugs (POST flares_add) both call record_bugs. A sheet row carrying an id whose status is open never regresses a closed flare (an old export predates the fix); 'reopen' does. A list that names no severity keeps the known one. Reason: the owner and a teammate collected bugs by hand and had no way to record them.]]
- [[mem_2b049e3f-a-flares-id-prefix-is-the-projects-lifecycle-sta|A flare's id prefix is the project's lifecycle stage read from git when it is filed (qa/* → QA, uat/staging → UAT, release/* or rc tag → RC, hotfix/* → HOTFIX, main with a reachable version tag → PROD, else DEV); a flare keeps its prefix for life and re-imports match by (source_doc, raw_id). flares.prefix pins one prefix (explicit outranks inferred); `import --prefix` applies to that import only and is no longer saved. Reason: the owner wanted prefixes to follow the project lifecycle without an extra command.]]
- [[mem_55db62b9-recall-is-made-visible-with-the-hooks-systemmess|Recall is made visible with the hook's systemMessage: SessionStart, UserPromptSubmit and PreToolUse print JSON with a one-line cosm◎s notice for the person and the context in hookSpecificOutput.additionalContext (cosmos/hooks.py _say/notice). Codex (COSMOS_AGENT=codex) gets plain text; ui.notices false turns the line off. Claude Code's own 'Recalled a memory' chip has no documented way for a tool to contribute. Reason: the owner saw Claude's memory recalls but never cosmos's.]]
- [[mem_5cfd6c9b-commit-note-by-biswajit-tripathy-autopilot-from|Commit note by Biswajit Tripathy: autopilot from parent folders, bugs recorded by hand, recall you can see, a briefing under the hook cap, updates that reach every project — - Sessions opened in a folder above the repository are captured and briefed; worktrees answer once. - Bugs found by hand: cosmos flares add (typed, or --from .txt/.csv/.tsv/.xlsx/.json/-) and Record bugs on the console's Flares page; an exported sheet edited and read back moves statuses without false regressions. - The journal no longer credits commits made in another folder. - Claude Desktop sessions are warned when an MCP entry named cosmos serves another repository. - Claude Code shows one line each time cosmos recall]]
### Finding
- [[mem_07187b11-mcp-entries-cosmos-writes-start-python3-which-do|MCP entries cosmos writes start python3, which does not exist on Windows, so the cosmos tools never start there]]
- [[mem_10ab2ec4-console-docs-said-horizon-notes-are-saved-in-cos|Console docs said Horizon notes are saved in .cosmos/ledger/intake/; they are saved in ledger/horizon/]]
- [[mem_1db8264f-a-claude-desktop-mcp-entry-named-cosmos-pinned-t|A Claude Desktop MCP entry named cosmos pinned to one repo sends every Desktop session's cosmos_remember/cosmos_flare to that repo's ledger]]
- [[mem_498078e0-atlas-page-4-of-8-deep-pass-diagrams-failed-unde|Atlas page: 4 of 8 deep-pass diagrams failed under mermaid 10.9.1 (unquoted ( ) { } in labels, ; in sequence text) and only the first diagram of a document was drawn]]
- [[mem_5790a327-cosmos-connect-with-no-agent-argument-failed-arg|`cosmos connect` with no agent argument failed: argparse checked the default ['all'] against choices]]
- [[mem_5a1661f5-journal-credited-commits-made-in-another-folder|Journal credited commits made in another folder (cd /tmp/x && git commit) to this repository]]
- [[mem_5b583e8d-cosmosw-always-prefers-an-installed-cosmos-over|cosmosw always prefers an installed cosmos over the repo's vendored copy, even when the install is older]]
- [[mem_9391c461-atlas-reported-0-endpoints-for-apps-without-an-o|Atlas reported 0 endpoints for apps without an OpenAPI spec (routes in code were never read)]]
- [[mem_ac19fa4c-a-whole-ledger-save-from-a-process-that-loaded-e|A whole-ledger save from a process that loaded earlier (a dream, the console, an MCP call) wrote every note back and reverted flare lifecycle changes made meanwhile]]
- [[mem_b9641884-an-older-pip-install-shadowed-the-repos-cosmos-a|An older pip install shadowed the repo's cosmos and rendered retired names (`finding:`, `cosmos intake`) into the committed CLAUDE.md / AGENTS.md]]
- [[mem_b9901dfb-a-session-opened-in-a-subfolder-of-the-repositor|A session opened in a subfolder of the repository gets no briefing, facts or capture: load_config takes the folder it is given as the repository root]]
- [[mem_cb4bccc1-retents-session-briefing-13-326-chars-exceeded-c|Retent's session briefing (13,326 chars) exceeded Claude Code's 10,000-char hook cap, so sessions saw a 2,000-char preview: most of the Charter and none of the facts]]
- [[mem_d4c37ea1-slack-cards-and-the-slack-report-told-people-to|Slack cards and the Slack report told people to run `cosmos audit fix/list` instead of `cosmos flares`]]
- [[mem_dbc7ae4e-cosmos-connect-codex-write-user-pins-codexs-user|cosmos connect codex --write-user pins Codex's user-level cosmos MCP server to the first repository and never updates it]]
- [[mem_e522e056-console-rendered-every-fact-rule-and-flare-at-on|Console rendered every fact, rule and flare at once and rules sat in a narrow sidebar with unclamped text]]
- [[mem_f2ac4098-a-token-pasted-in-a-prompt-was-written-verbatim|A token pasted in a prompt was written verbatim into the journal (`ask`) and the live view, and committed with .cosmos]]
- [[mem_f87f2319-claude-desktops-mcp-entry-named-cosmos-silently|Claude Desktop's MCP entry named cosmos silently sent cosmos_remember/cosmos_flare from every Desktop session to one repository]]
- [[mem_fcf6d908-new-slash-commands-reintroduced-names-retired-in|New slash commands reintroduced names retired in 5b289ba: /intake and cosmos_finding / cosmos_intake in command bodies]]
### Workflow
- [[mem_9fe4f5ce-horizon-notes-exist-only-when-someone-asks-for-o|Horizon notes exist only when someone asks for one (/horizon, cosmos horizon, cosmos_horizon, the console's Horizon page); nothing creates them by itself, so a repo that never ran one (retent on 2026-09-30) shows 0.]]

## Lane · docs
### Constraint
- [[mem_62468362-cosmos-dev-is-not-published-on-pypi-404-on-2026|cosmos-dev is not published on PyPI (404 on 2026-09-29): install with `python3 -m pip install "git+https://github.com/BiswajitBiswa/cosmos"`. `/plugin` is a Claude Code CLI command only; the Claude desktop app uses its Plugins screen or `claude plugin marketplace add` / `claude plugin install` in a terminal.]] `forgotten`
### Decision
- [[mem_1ac630fe-commit-note-by-biswajit-tripathy-plugin-0-2-1-co|Commit note by Biswajit Tripathy: plugin 0.2.1: Codex installs cosmos from its Plugins screen, nothing else to run — The repository is already a marketplace Codex reads (.claude-plugin/marketplace.json). The plugin gains its own Codex manifest (plugin/.codex-plugin/plugin.json); Claude keeps reading plugin/.claude-plugin/. - Hooks (SessionStart, UserPromptSubmit) find the thread's repository and hand the event to its committed cosmos: the Charter and facts become the model's context, and the watcher that captures Codex sessions starts. No Stop hook: exit 2 would block a Codex thread. - One MCP server for every repository: Codex starts it in the plugin's folder, so it answers the handshake it]]

## Lane · general
### Constraint
- [[mem_2518367d-cosmos-is-on-pypi-as-cosmos-dev-0-1-0-published|cosmos is on PyPI as cosmos-dev (0.1.0 published 2026-09-29; the name cosmos is taken): install with python3 -m pip install cosmos-dev. The README is also the PyPI page, so its images and doc links must be absolute GitHub URLs. /plugin is a Claude Code CLI command only; the desktop app uses its Plugins screen or claude plugin marketplace add / install.]]
- [[mem_6381abbc-cosmos-is-stdlib-only-the-anthropic-sdk-is-an-op|cosmos is stdlib-only; the anthropic SDK is an optional extra and every feature must work without it.]]
### Decision
- [[mem_4efbf3d7-releases-and-their-repairs-reach-every-project-b|Releases and their repairs reach every project by themselves (cosmos/upgrade.py): a session start checks PyPI at most once a day per machine; a newer wheel is sha256-checked against PyPI, import-tested, swapped into .cosmos/vendor and committed, and the pip install is upgraded when pip allows; each version runs repair once per machine and repository (wrapper, repo and user hooks, slash commands, .agents/plugins/marketplace.json for Codex, a Desktop MCP entry named cosmos renamed to cosmos-<repo> with a backup). New repairs go in REPAIRS and must be idempotent and touch only what cosmos wrote. update.auto false turns it off. Reason: the owner cannot push fixes into every team's project.]]
### Finding
- [[mem_6fa48630-a-repository-whose-committed-hook-command-is-old|A repository whose committed hook command is older than the user-level one runs every hook twice (two Gates, two briefings)]]
- [[mem_9aa3899c-python-orgs-macos-python-has-no-ca-bundle-until|python.org's macOS Python has no CA bundle until 'Install Certificates' is run, so every urllib HTTPS call from cosmos failed CERTIFICATE_VERIFY_FAILED]]
- [[mem_fcae919e-a-dream-that-started-before-cosmos-was-updated-r|A dream that started before cosmos was updated rewrites slash command files with its stale in-memory catalogue at the end (commands.refresh)]]

## Lane · plugin
### Constraint
- [[mem_97f2aa55-installed-plugins-update-only-when-the-version-c|Installed plugins update only when the version changes: bump plugin/.claude-plugin/plugin.json and .claude-plugin/marketplace.json together whenever plugin files (commands, skill, bin) change, or `claude plugin update` reports 'already at the latest version'. The plugin version (0.2.0) is independent of the PyPI package version.]]
### Finding
- [[mem_a41e3c70-plugin-changes-never-reached-installed-plugins-t|Plugin changes never reached installed plugins: the plugin version stayed 0.1.0, so `claude plugin update` saw nothing new]] `stale-candidate`
