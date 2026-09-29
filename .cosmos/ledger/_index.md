---
type: Index
title: Ledger index
okf_version: "0.2"
tags: ["cosmos", "moc"]
---

# Ledger index

14 memories · 14 active · 0 contradicted · 0 stale candidates · 3 lanes

Charter: [[charter]] · Atlas: [[inventory]] · [[containers]] · [[deployment]] · [[api]]

## Lane · cosmos
### Architecture
- [[mem_1f13b61a-slash-commands-for-every-agent-come-from-one-cat|Slash commands for every agent come from one catalogue in cosmos/commands.py (Claude .claude/commands, Gemini .gemini/commands TOML, Cursor .cursor/commands, Copilot .github/prompts, Windsurf .windsurf/workflows, Codex only ~/.codex/prompts via --write-user, plugin/commands for the plugin). Files carrying 'written by cosmos' are rewritten; unmarked files are the team's own and never overwritten. plugin/commands must be regenerated when the catalogue changes (a test fails otherwise).]]
### Constraint
- [[mem_1192ca15-hooks-must-always-exit-0-the-gate-is-the-only-de|Hooks must always exit 0; the Gate is the only deliberate exit-2 and it never fires twice in one turn (stop_hook_active).]]
### Decision
- [[mem_043ce3de-playbooks-a-repositorys-own-long-form-agent-prom|Playbooks: a repository's own long-form agent prompts (master QA protocol, runbooks) are detected by cosmos/playbooks.py (name or first heading says protocol/playbook/runbook/master prompt, and the text is written for an agent) plus .cosmos/playbooks/; each becomes a slash command for every agent and /qa follows the QA one. Reason: the owner wanted RETEN's master and QA prompts reusable by any project and detected automatically. cosmos playbooks add <file|qa> brings one in.]]
- [[mem_2b049e3f-a-flares-id-prefix-is-the-projects-lifecycle-sta|A flare's id prefix is the project's lifecycle stage read from git when it is filed (qa/* → QA, uat/staging → UAT, release/* or rc tag → RC, hotfix/* → HOTFIX, main with a reachable version tag → PROD, else DEV); a flare keeps its prefix for life and re-imports match by (source_doc, raw_id). flares.prefix pins one prefix (explicit outranks inferred); `import --prefix` applies to that import only and is no longer saved. Reason: the owner wanted prefixes to follow the project lifecycle without an extra command.]]
### Finding
- [[mem_10ab2ec4-console-docs-said-horizon-notes-are-saved-in-cos|Console docs said Horizon notes are saved in .cosmos/ledger/intake/; they are saved in ledger/horizon/]]
- [[mem_1db8264f-a-claude-desktop-mcp-entry-named-cosmos-pinned-t|A Claude Desktop MCP entry named cosmos pinned to one repo sends every Desktop session's cosmos_remember/cosmos_flare to that repo's ledger]]
- [[mem_5790a327-cosmos-connect-with-no-agent-argument-failed-arg|`cosmos connect` with no agent argument failed: argparse checked the default ['all'] against choices]]
- [[mem_5b583e8d-cosmosw-always-prefers-an-installed-cosmos-over|cosmosw always prefers an installed cosmos over the repo's vendored copy, even when the install is older]]
- [[mem_9391c461-atlas-reported-0-endpoints-for-apps-without-an-o|Atlas reported 0 endpoints for apps without an OpenAPI spec (routes in code were never read)]]
- [[mem_b9641884-an-older-pip-install-shadowed-the-repos-cosmos-a|An older pip install shadowed the repo's cosmos and rendered retired names (`finding:`, `cosmos intake`) into the committed CLAUDE.md / AGENTS.md]]
- [[mem_d4c37ea1-slack-cards-and-the-slack-report-told-people-to|Slack cards and the Slack report told people to run `cosmos audit fix/list` instead of `cosmos flares`]]
- [[mem_fcf6d908-new-slash-commands-reintroduced-names-retired-in|New slash commands reintroduced names retired in 5b289ba: /intake and cosmos_finding / cosmos_intake in command bodies]]

## Lane · docs
### Constraint
- [[mem_62468362-cosmos-dev-is-not-published-on-pypi-404-on-2026|cosmos-dev is not published on PyPI (404 on 2026-09-29): install with `python3 -m pip install "git+https://github.com/BiswajitBiswa/cosmos"`. `/plugin` is a Claude Code CLI command only; the Claude desktop app uses its Plugins screen or `claude plugin marketplace add` / `claude plugin install` in a terminal.]]

## Lane · general
### Constraint
- [[mem_6381abbc-cosmos-is-stdlib-only-the-anthropic-sdk-is-an-op|cosmos is stdlib-only; the anthropic SDK is an optional extra and every feature must work without it.]]
