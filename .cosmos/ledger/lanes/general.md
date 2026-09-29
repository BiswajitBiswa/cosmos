---
type: "Lane"
title: "general"
description: "5 active facts, 2 open flares, 1 people active in the last 30 days"
status: "stable"
sources: [{"resource": "/../../cosmos", "title": "cosmos"}, {"resource": "/../../docs", "title": "docs"}, {"resource": "/../../plugin", "title": "plugin"}]
links: ["/architecture/mem_1f13b61a-slash-commands-for-every-agent-come-from-one-cat.md", "/constraint/mem_62468362-cosmos-dev-is-not-published-on-pypi-404-on-2026.md", "/constraint/mem_6381abbc-cosmos-is-stdlib-only-the-anthropic-sdk-is-an-op.md", "/decision/mem_043ce3de-playbooks-a-repositorys-own-long-form-agent-prom.md", "/decision/mem_2b049e3f-a-flares-id-prefix-is-the-projects-lifecycle-sta.md"]
tags: ["lane", "general"]
---


# Lane · general

5 active facts, 2 open flares, 1 people active in the last 30 days.

## Open flares

- [DEV-desktop-mcp-pinned](/finding/mem_1db8264f-a-claude-desktop-mcp-entry-named-cosmos-pinned-t.md) [medium] A Claude Desktop MCP entry named cosmos pinned to one repo sends every Desktop session's cosmos_remember/cosmos_flare to
- [DEV-wrapper-prefers-stale-install](/finding/mem_5b583e8d-cosmosw-always-prefers-an-installed-cosmos-over.md) [medium] cosmosw always prefers an installed cosmos over the repo's vendored copy, even when the install is older

## Facts

### Architecture
- [Slash commands for every agent come from one catalogue in cosmos/commands.py (Claude .claude/commands, Gemini .gemini/commands TOML, Cursor ](/architecture/mem_1f13b61a-slash-commands-for-every-agent-come-from-one-cat.md)

### Constraint
- [cosmos-dev is not published on PyPI (404 on 2026-09-29): install with `python3 -m pip install "git+https://github.com/BiswajitBiswa/cosmos"`](/constraint/mem_62468362-cosmos-dev-is-not-published-on-pypi-404-on-2026.md)
- [cosmos is stdlib-only; the anthropic SDK is an optional extra and every feature must work without it.](/constraint/mem_6381abbc-cosmos-is-stdlib-only-the-anthropic-sdk-is-an-op.md)

### Decision
- [Playbooks: a repository's own long-form agent prompts (master QA protocol, runbooks) are detected by cosmos/playbooks.py (name or first head](/decision/mem_043ce3de-playbooks-a-repositorys-own-long-form-agent-prom.md)
- [A flare's id prefix is the project's lifecycle stage read from git when it is filed (qa/* → QA, uat/staging → UAT, release/* or rc tag → RC,](/decision/mem_2b049e3f-a-flares-id-prefix-is-the-projects-lifecycle-sta.md)

## People

- Biswajit Tripathy
