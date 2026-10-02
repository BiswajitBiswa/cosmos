---
type: Index
title: Ledger index
okf_version: "0.2"
tags: ["cosmos", "moc"]
---

# Ledger index

116 memories · 112 active · 0 contradicted · 3 stale candidates · 6 lanes

Charter: [[charter]] · Atlas: [[inventory]] · [[containers]] · [[deployment]] · [[api]]

## Lane · cosmos
### Architecture
- [[mem_1f13b61a-slash-commands-for-every-agent-come-from-one-cat|Slash commands for every agent come from one catalogue in cosmos/commands.py (Claude .claude/commands, Gemini .gemini/commands TOML, Cursor .cursor/commands, Copilot .github/prompts, Windsurf .windsurf/workflows, Codex only ~/.codex/prompts via --write-user, plugin/commands for the plugin). Files carrying 'written by cosmos' are rewritten; unmarked files are the team's own and never overwritten. plugin/commands must be regenerated when the catalogue changes (a test fails otherwise).]]
- [[mem_79036575-codex-reads-project-skills-from-agents-skills-na|Codex reads project skills from .agents/skills/<name>/SKILL.md (codex-rs/core/tests/suite/skills.rs:73), not project commands: AGENT_DIRS['codex'] writes the command catalogue and every playbook there (frontmatter name + description, no arguments). Claude Code has no icon field for plugins, commands or skills and draws no MCP icons; only the Codex manifest's interface.composerIcon/logo show the cosmos mark. Firebase Studio (IDX) is sunset 2027-03-22; an .idx/ workspace gets .idx/mcp.json and the block in its own .idx/airules.md.]]
- [[mem_b6b76950-the-atlas-has-a-peoples-view-cosmos-atlashtml-py|The Atlas has a people's view: cosmos/atlas_html.py renders every ledger/atlas/*.md into ledger/atlas/atlas.html (sidebar, pan/zoom/fit/full-screen diagrams, cosmos theme) after each build and deep pass; --format md or atlas.format md skips it. The Markdown stays the source agents and dreams read. The page reuses the console's mmdFix by extracting it from ui.HTML, so the Mermaid fixes have one copy.]]
- [[mem_c2833030-excel-export-is-a-stdlib-xlsx-writer-cosmos-xlsx|Excel export is a stdlib xlsx writer (cosmos/xlsx.py: zip of SpreadsheetML parts, inline strings only so no cell is ever a formula); `cosmos export`, `flares export -o *.xlsx` and the console's /api/export.xlsx all use it. Reason: cosmos is stdlib-only, so no openpyxl.]]
### Constraint
- [[mem_1192ca15-hooks-must-always-exit-0-the-gate-is-the-only-de|Hooks must always exit 0; the Gate is the only deliberate exit-2 and it never fires twice in one turn (stop_hook_active).]]
- [[mem_44c1eef6-the-cosmos-mcp-server-asks-the-client-for-mcp-ro|The cosmos MCP server asks the client for MCP roots after the handshake (Claude Code 2.1.118 declares roots and answers roots/list with the session's project folder, verified 2026-10-01). When no root is the repository or a folder above it, every tool returns 'not this project' and nothing is read or recorded (cosmos/mcp.py foreign_session); clients that send no roots are served as before. Reason: a global Desktop MCP entry filed another project's critical bug into retent.]]
- [[mem_4c8727a1-in-claude-desktop-code-tab-sessions-an-mcp-serve|In Claude Desktop Code-tab sessions an MCP server named cosmos in claude_desktop_config.json shadows the project's .mcp.json server, so cosmos_* tools write to that pinned repository. session_start warns when CLAUDE_CODE_ENTRYPOINT=claude-desktop; agents then record with python3 -m cosmos / .cosmos/cosmosw on the command line.]]
- [[mem_a1b7e320-claude-code-caps-each-hook-text-plain-stdout-add|Claude Code caps each hook text (plain stdout, additionalContext, systemMessage) at 10,000 characters; longer text is saved to a file and the model sees only a 2,000-character preview it is not asked to read. So session_start keeps the briefing under retrieval.session_start_chars (9,000) via _fit, and each explicit rule in the Charter summary is one 220-character line with its id. Measured 2026-10-01: retent's briefing was 13,326 chars (12 rules = 8,034), now 8,157.]]
- [[mem_b230553a-cosmos-remember-c-finding-files-an-open-flare-au|cosmos remember -c finding files an open flare: audit.findings lists every note whose category is finding, and a soft forget keeps it listed as withdrawn. Record a status note or open question as decision or domain; use finding only for a bug that belongs in the flares list (seen in retent on 2026-10-07, three status notes showed as open flares until re-recorded).]]
- [[mem_4db48cc5-from-now-on-cosmos-changes-reach-a-project-like|From now on, cosmos changes reach a project like retent only through a release and the auto-upgrade, never by me writing into its `.cosmos/`.]]
- [[mem_c3748e04-revoke-that-token-on-pypi-afterwards-since-its-i|Revoke that token on PyPI afterwards, since it's in this chat. 0.1.0 can never be re-uploaded.]]
- [[mem_0f220612-githubs-secret-scanning-spotted-it-and-blocked-t|GitHub's secret scanning spotted it and blocked the first push to ideatorlabs, so it never reached either GitHub repo.]]
- [[mem_15da1401-for-clients-that-dont-report-their-folders-every|For clients that don't report their folders: every write now says which repo it went to (`filed RET-… in retent's ledger`); a flare whose files don't exist in that repo gets a warning to withdraw it.]]
- [[mem_1c0f1357-becomes-a-command-each-playbook-becomes-a-slash|Becomes a command: each playbook becomes a slash command in every agent, for example `/master-qa-protocol`, which reads the file and follows it, so it never goes stale.]]
- [[mem_58733dee-the-ledger-is-written-from-main-so-lifecycle-pre|The ledger is written from `main`, so lifecycle prefixes would always say DEV, and about 150 ids already use this series.]]
- [[mem_58afadef-weekly-showcase-refresh-re-run-pulse-bench-and-o|Weekly showcase refresh: re-run `pulse --bench` and open a PR updating the site's "Measured on a live repository" numbers, so the site never shows stale figures.]]
- [[mem_7f853acf-this-repos-charter-spells-out-its-own-largechang|This repo's charter spells out its own `large_change_checks`, which replaces the default, so repos with an explicit list never get new default checks.]]
- [[mem_851c75c5-pausing-cosmoss-commits-to-main-qa-asked-for-thi|Pausing cosmos's commits to `main`: QA asked for this. cosmos only commits `.cosmos/` locally and never pushes, so it can't reach GitHub's `main` on its own.]]
- [[mem_9e13c334-my-check-was-flawed-it-kept-the-prefixes-so-matc|My check was flawed: it kept the `+`/`-` prefixes, so matching lines never paired up.]]
- [[mem_a34514eb-what-changed-in-retent-only-its-cosmos-ledger-at|What changed in `retent`: only its `.cosmos/ledger/atlas/` files: the refreshed inventory, API and containers files plus the new page. cosmos commits those locally by itself and never pushes.]]
- [[mem_cf1dd94b-tests-already-set-cosmosnobackground-so-they-can|Tests already set `COSMOS_NO_BACKGROUND`, so they can never reach PyPI.]]
- [[mem_dcdcfe55-the-intake-left-in-the-code-is-internal-names-on|The `intake` left in the code is internal names only; people never see it.]]
- [[mem_f5cb1c55-parsed-notes-are-kept-per-machine-in-cache-cosmo|Parsed notes are kept per machine in `~/.cache/cosmos/`, never in the repo, and a note is re-read only when its file changes.]]
- [[mem_4a242b58-your-rule-is-recorded-and-followed-mem764f889d-c|Your rule is recorded and followed (`mem_764f889d`): cosmos changes reach a project only through a release and the auto-upgrade, never by writing into its `.cosmos/`.]] `stale-candidate`
### Decision
- [[mem_043ce3de-playbooks-a-repositorys-own-long-form-agent-prom|Playbooks: a repository's own long-form agent prompts (master QA protocol, runbooks) are detected by cosmos/playbooks.py (name or first heading says protocol/playbook/runbook/master prompt, and the text is written for an agent) plus .cosmos/playbooks/; each becomes a slash command for every agent and /qa follows the QA one. Reason: the owner wanted RETEN's master and QA prompts reusable by any project and detected automatically. cosmos playbooks add <file|qa> brings one in.]]
- [[mem_1734bf56-bugs-found-by-hand-become-flares-through-one-pat|Bugs found by hand become flares through one path: cosmos/audit.py import_items (also used by the JSON import and cosmos_flare). cosmos flares add (typed, --from .txt/.csv/.tsv/.xlsx/.json/-) and the console's Record bugs (POST flares_add) both call record_bugs. A sheet row carrying an id whose status is open never regresses a closed flare (an old export predates the fix); 'reopen' does. A list that names no severity keeps the known one. Reason: the owner and a teammate collected bugs by hand and had no way to record them.]]
- [[mem_2b049e3f-a-flares-id-prefix-is-the-projects-lifecycle-sta|A flare's id prefix is the project's lifecycle stage read from git when it is filed (qa/* → QA, uat/staging → UAT, release/* or rc tag → RC, hotfix/* → HOTFIX, main with a reachable version tag → PROD, else DEV); a flare keeps its prefix for life and re-imports match by (source_doc, raw_id). flares.prefix pins one prefix (explicit outranks inferred); `import --prefix` applies to that import only and is no longer saved. Reason: the owner wanted prefixes to follow the project lifecycle without an extra command.]]
- [[mem_4efbf3d7-releases-and-their-repairs-reach-every-project-b|Releases and their repairs reach every project by themselves (cosmos/upgrade.py): a session start checks PyPI at most once a day per machine; a newer wheel is sha256-checked against PyPI, import-tested, swapped into .cosmos/vendor and committed, and the pip install is upgraded when pip allows; each version runs repair once per machine and repository (wrapper, repo and user hooks, slash commands, .agents/plugins/marketplace.json for Codex, a Desktop MCP entry named cosmos renamed to cosmos-<repo> with a backup). New repairs go in REPAIRS and must be idempotent and touch only what cosmos wrote. update.auto false turns it off. Reason: the owner cannot push fixes into every team's project.]]
- [[mem_55db62b9-recall-is-made-visible-with-the-hooks-systemmess|Recall is made visible with the hook's systemMessage: SessionStart, UserPromptSubmit and PreToolUse print JSON with a one-line cosm◎s notice for the person and the context in hookSpecificOutput.additionalContext (cosmos/hooks.py _say/notice). Codex (COSMOS_AGENT=codex) gets plain text; ui.notices false turns the line off. Claude Code's own 'Recalled a memory' chip has no documented way for a tool to contribute. Reason: the owner saw Claude's memory recalls but never cosmos's.]]
- [[mem_8e60778d-cosmos-pulse-measures-a-repository-from-its-own|cosmos pulse measures a repository from its own .cosmos records (inject.log tokens, dream records' recall_at_5/edit_hit/duration_ms, journal lines, flare lifecycle) plus --bench (the real hook command in a fresh process, median of 5); the first dream of a day saves one to .cosmos/ledger/metrics/<date>.json with --bench. Numbers shown on the site and README come from these reports only.]]
- [[mem_f044be42-the-gate-runs-security-checks-every-turn-on-ever|The Gate runs security checks every turn on every touched file (cosmos/security.py): high-precision credential patterns (placeholders, local or docker-compose URLs and 'cosmos: allow-secret' lines skipped), hidden Unicode (bidi overrides, tag characters, zero-width spaces; not emoji joiners, RTL marks or BOMs), and agent-steering text only in instruction files; a changed dependency manifest needs its audit; large changes add bandit or semgrep. Ledger notes that steer agents are withheld from briefings and recall until allowed with cosmos scan --allow. Reason: cosmos injects these files into every agent, so a poisoned one reaches every session.]]
- [[mem_5cfd6c9b-commit-note-by-biswajit-tripathy-autopilot-from|Commit note by Biswajit Tripathy: autopilot from parent folders, bugs recorded by hand, recall you can see, a briefing under the hook cap, updates that reach every project — - Sessions opened in a folder above the repository are captured and briefed; worktrees answer once. - Bugs found by hand: cosmos flares add (typed, or --from .txt/.csv/.tsv/.xlsx/.json/-) and Record bugs on the console's Flares page; an exported sheet edited and read back moves statuses without false regressions. - The journal no longer credits commits made in another folder. - Claude Desktop sessions are warned when an MCP entry named cosmos serves another repository. - Claude Code shows one line each time cosmos recall]]
- [[mem_6eb345df-horizon-entry-now-names-horizon-and-says-flares|Horizon entry: now names `/horizon` and says "flares" rather than "findings".]]
- [[mem_b2c4f781-text-a-regular-weight-soft-ivory-ddd9ce-instead|Text: a regular-weight soft ivory `#DDD9CE` instead of bold white, slightly larger, with a little more space between lines.]]
### Dependency
- [[mem_3c575764-tag-tag-v0-1-0-so-new-flares-on-main-get-the-pro|Tag: tag `v0.1.0`, so new flares on `main` get the PROD prefix.]]
- [[mem_06dacbf0-self-upgrade-at-most-once-a-day-per-machine-a-se|Self-upgrade: at most once a day per machine, a session start checks PyPI in the background (`maybe_background`, line 210).]]
- [[mem_0c3037f2-cosmos-upgrade-py-210-maybebackground-the-daily|`cosmos/upgrade.py:210` `maybe_background` — the daily background check, started from a session start.]]
- [[mem_10ab0e02-cosmos-upgrade-py-282-stepcodexlisting-writes-th|`cosmos/upgrade.py:282` `_step_codex_listing` — writes the Codex plugin listing.]]
- [[mem_27260566-cosmos-upgrade-py-325-repair-runs-every-repair-s|`cosmos/upgrade.py:325` `repair` — runs every repair step.]]
- [[mem_2dac10c6-cosmos-upgrade-cosmos-repair-now-on-the-site-and|`cosmos upgrade` / `cosmos repair`: now on the site, and an "Updates" section in `docs/hooks.md`.]]
- [[mem_38aab8b8-the-teams-own-entries-in-that-file-are-kept-rena|The team's own entries in that file are kept. renames a Claude Desktop entry pinned to one repo to `cosmos- `, after backing up the file (line 298).]]
- [[mem_5d62d678-prefix-keep-ret-waterfall-pinned|Prefix: keep `RET-WATERFALL` pinned.]]
- [[mem_857accb2-my-filter-was-wrong-cosmos-as-a-regex-also-match|My filter was wrong: `.cosmos/` as a regex also matched `cosmos/upgrade.py`.]]
- [[mem_97200a8f-cosmos-upgrade-py-298-stepdesktoppin-renames-the|`cosmos/upgrade.py:298` `_step_desktop_pin` — renames the pinned Desktop entry, with a backup.]]
- [[mem_af60cf4a-cosmos-upgrade-py-170-run-check-pypi-upgrade-the|`cosmos/upgrade.py:170` `run` — check PyPI, upgrade the bundled copy, repair, commit.]]
- [[mem_b36ad28f-new-command-cosmos-upgrade-check-reports-where-a|New command: `cosmos upgrade --check` reports where a repo stands; `cosmos repair` runs the fixes by hand.]]
- [[mem_c9b85981-exact-locations-of-todays-changes-cosmos-upgrade|Exact locations of today's changes: `cosmos/upgrade.py:72` `_get` — downloads with certificate checking kept on, falling back to `certifi` or the system bundle.]]
- [[mem_cabb8278-doctor-now-warns-about-a-pinned-entry-like-that|`doctor` now warns about a pinned entry like that.]]
- [[mem_d00a05c4-after-publishing-the-docs-can-go-back-to-pip-ins|After publishing, the docs can go back to `pip install cosmos-dev`, and tagging `v0.1.0` makes new flares on `main` get the PROD prefix.]]
- [[mem_dc8c6d5b-a-real-upgrade-from-pypi-the-tests-used-a-local|A real upgrade from PyPI: the tests used a local fake release.]]
- [[mem_f8c19d55-which-cosmos-it-uses-reten-runs-in-the-desktop-a|Which cosmos it uses: RETEN runs in the Desktop app, so its cosmos tools come from the `cosmos` entry in Claude Desktop's config, which is pinned to retent.]]
- [[mem_77e048a6-prod-fec6d4-open-low-a-dream-started-before-an-u|`PROD-fec6d4` (open, low): a dream started before an upgrade restores old slash-command text once.]] `stale-candidate`
### Finding
- [[mem_0448e271-the-watcher-started-a-dream-every-30-seconds-whi|The watcher started a dream every 30 seconds while model ranges waited and no model was available]]
- [[mem_07187b11-mcp-entries-cosmos-writes-start-python3-which-do|MCP entries cosmos writes start python3, which does not exist on Windows, so the cosmos tools never start there]]
- [[mem_0b83670f-a-session-in-a-project-without-cosmos-filed-its|A session in a project without cosmos filed its bug into retent's ledger through Claude Desktop's global cosmos MCP entry (RET-WATERFALL-cabf52, Odin LogMasker)]]
- [[mem_10ab2ec4-console-docs-said-horizon-notes-are-saved-in-cos|Console docs said Horizon notes are saved in .cosmos/ledger/intake/; they are saved in ledger/horizon/]]
- [[mem_1db8264f-a-claude-desktop-mcp-entry-named-cosmos-pinned-t|A Claude Desktop MCP entry named cosmos pinned to one repo sends every Desktop session's cosmos_remember/cosmos_flare to that repo's ledger]]
- [[mem_2229c98c-cosmoss-model-use-has-no-budget-in-7-days-its-dr|cosmos's model use has no budget: in 7 days its dreams made 57 model runs through the user's Claude login and read 6,290 session turns, likely exhausting the weekly limit]]
- [[mem_488b620a-every-hook-took-700-790-ms-on-retent-2-925-notes|Every hook took 700-790 ms on retent (2,925 notes) because Ledger.load re-parsed every markdown note on every call]]
- [[mem_498078e0-atlas-page-4-of-8-deep-pass-diagrams-failed-unde|Atlas page: 4 of 8 deep-pass diagrams failed under mermaid 10.9.1 (unquoted ( ) { } in labels, ; in sequence text) and only the first diagram of a document was drawn]]
- [[mem_5790a327-cosmos-connect-with-no-agent-argument-failed-arg|`cosmos connect` with no agent argument failed: argparse checked the default ['all'] against choices]]
- [[mem_5a1661f5-journal-credited-commits-made-in-another-folder|Journal credited commits made in another folder (cd /tmp/x && git commit) to this repository]]
- [[mem_5b583e8d-cosmosw-always-prefers-an-installed-cosmos-over|cosmosw always prefers an installed cosmos over the repo's vendored copy, even when the install is older]]
- [[mem_6fa48630-a-repository-whose-committed-hook-command-is-old|A repository whose committed hook command is older than the user-level one runs every hook twice (two Gates, two briefings)]]
- [[mem_76b6999b-without-a-model-capture-stores-sentence-fragment|Without a model, capture stores sentence fragments that make no sense out of context]]
- [[mem_93255725-cosmosremember-and-cosmosflare-took-40-48-s-on-r|cosmos_remember and cosmos_flare took 40-48 s on retent (2,975 notes), so agents' saves timed out]]
- [[mem_9391c461-atlas-reported-0-endpoints-for-apps-without-an-o|Atlas reported 0 endpoints for apps without an OpenAPI spec (routes in code were never read)]]
- [[mem_9aa3899c-python-orgs-macos-python-has-no-ca-bundle-until|python.org's macOS Python has no CA bundle until 'Install Certificates' is run, so every urllib HTTPS call from cosmos failed CERTIFICATE_VERIFY_FAILED]]
- [[mem_a0fa1f2d-several-auto-dreams-ran-at-once-in-one-repositor|Several auto-dreams ran at once in one repository (five in retent) and processed the same batch twice, pushing the machine's load average to 578]]
- [[mem_a199a451-the-daily-metrics-check-used-the-local-date-and|The daily metrics check used the local date and the file the UTC date, so near midnight every dream rewrote the day's report]]
- [[mem_ac19fa4c-a-whole-ledger-save-from-a-process-that-loaded-e|A whole-ledger save from a process that loaded earlier (a dream, the console, an MCP call) wrote every note back and reverted flare lifecycle changes made meanwhile]]
- [[mem_b058375a-a-pip-install-of-the-same-version-string-shadowe|A pip install of the same version string shadowed the repository's newer copy and silently turned off capture and briefings for every retent session for about 8 hours]]
- [[mem_b9641884-an-older-pip-install-shadowed-the-repos-cosmos-a|An older pip install shadowed the repo's cosmos and rendered retired names (`finding:`, `cosmos intake`) into the committed CLAUDE.md / AGENTS.md]]
- [[mem_b9901dfb-a-session-opened-in-a-subfolder-of-the-repositor|A session opened in a subfolder of the repository gets no briefing, facts or capture: load_config takes the folder it is given as the repository root]]
- [[mem_cb4bccc1-retents-session-briefing-13-326-chars-exceeded-c|Retent's session briefing (13,326 chars) exceeded Claude Code's 10,000-char hook cap, so sessions saw a 2,000-char preview: most of the Charter and none of the facts]]
- [[mem_d4c37ea1-slack-cards-and-the-slack-report-told-people-to|Slack cards and the Slack report told people to run `cosmos audit fix/list` instead of `cosmos flares`]]
- [[mem_dbc7ae4e-cosmos-connect-codex-write-user-pins-codexs-user|cosmos connect codex --write-user pins Codex's user-level cosmos MCP server to the first repository and never updates it]]
- [[mem_e522e056-console-rendered-every-fact-rule-and-flare-at-on|Console rendered every fact, rule and flare at once and rules sat in a narrow sidebar with unclamped text]]
- [[mem_f2ac4098-a-token-pasted-in-a-prompt-was-written-verbatim|A token pasted in a prompt was written verbatim into the journal (`ask`) and the live view, and committed with .cosmos]]
- [[mem_f3e993fb-the-briefings-team-rules-are-the-12-oldest-so-ow|The briefing's team rules are the 12 oldest, so owner rules added later never reach a session]]
- [[mem_f87f2319-claude-desktops-mcp-entry-named-cosmos-silently|Claude Desktop's MCP entry named cosmos silently sent cosmos_remember/cosmos_flare from every Desktop session to one repository]]
- [[mem_fcae919e-a-dream-that-started-before-cosmos-was-updated-r|A dream that started before cosmos was updated rewrites slash command files with its stale in-memory catalogue at the end (commands.refresh)]]
- [[mem_fcf6d908-new-slash-commands-reintroduced-names-retired-in|New slash commands reintroduced names retired in 5b289ba: /intake and cosmos_finding / cosmos_intake in command bodies]]
### Workflow
- [[mem_764f889d-never-modify-a-projects-cosmos-copy-cosmos-vendo|Never modify a project's cosmos copy (.cosmos/vendor, cosmosw) directly from the cosmos repository; changes reach projects only through a release and the auto-upgrade (cosmos upgrade, daily from a session start). Reason: the owner wants every project to get fixes the same way, without anyone pushing into each repository.]]
- [[mem_9fe4f5ce-horizon-notes-exist-only-when-someone-asks-for-o|Horizon notes exist only when someone asks for one (/horizon, cosmos horizon, cosmos_horizon, the console's Horizon page); nothing creates them by itself, so a repo that never ran one (retent on 2026-09-30) shows 0.]]

## Lane · docs
### Constraint
- [[mem_001211c1-rather-than-collecting-them-by-hand-ill-build-co|Rather than collecting them by hand, I'll build `cosmos pulse`, one command that measures a repo from its own records: health checks: the ones I ran by hand; usage, memory and flare metrics; retrieval quality: cosmos's existing evals; a hook speed benchmark: something cosmos has never measured.]]
- [[mem_62468362-cosmos-dev-is-not-published-on-pypi-404-on-2026|cosmos-dev is not published on PyPI (404 on 2026-09-29): install with `python3 -m pip install "git+https://github.com/BiswajitBiswa/cosmos"`. `/plugin` is a Claude Code CLI command only; the Claude desktop app uses its Plugins screen or `claude plugin marketplace add` / `claude plugin install` in a terminal.]] `forgotten`
### Decision
- [[mem_1ac630fe-commit-note-by-biswajit-tripathy-plugin-0-2-1-co|Commit note by Biswajit Tripathy: plugin 0.2.1: Codex installs cosmos from its Plugins screen, nothing else to run — The repository is already a marketplace Codex reads (.claude-plugin/marketplace.json). The plugin gains its own Codex manifest (plugin/.codex-plugin/plugin.json); Claude keeps reading plugin/.claude-plugin/. - Hooks (SessionStart, UserPromptSubmit) find the thread's repository and hand the event to its committed cosmos: the Charter and facts become the model's context, and the watcher that captures Codex sessions starts. No Stop hook: exit 2 would block a Codex thread. - One MCP server for every repository: Codex starts it in the plugin's folder, so it answers the handshake it]]

## Lane · general
### Architecture
- [[mem_df0fd996-cosmos-plain-py-works-out-with-no-model-a-short|cosmos/plain.py works out, with no model, a short title, one plain sentence and chips (date, step, label, author, phase, status) for every note; the stored text and ids never change, and lint() tells writers what would read plainer.]]
- [[mem_114605d7-cosmos-is-a-single-repo-memory-layer-for-ai-codi|cosmos is a single-repo memory layer for AI coding agents, written in Python 3.9+ with no runtime dependencies (the `anthropic` package is optional).]]
- [[mem_13a45e83-one-entry-point-hooks-handle-at-hooks-py-526-dis|One entry point, `hooks.handle()` at `hooks.py:526`, dispatches on `hook_event_name`.]]
### Constraint
- [[mem_2518367d-cosmos-is-on-pypi-as-cosmos-dev-0-1-0-published|cosmos is on PyPI as cosmos-dev (0.1.0 published 2026-09-29; the name cosmos is taken): install with python3 -m pip install cosmos-dev. The README is also the PyPI page, so its images and doc links must be absolute GitHub URLs. /plugin is a Claude Code CLI command only; the desktop app uses its Plugins screen or claude plugin marketplace add / install.]]
- [[mem_6381abbc-cosmos-is-stdlib-only-the-anthropic-sdk-is-an-op|cosmos is stdlib-only; the anthropic SDK is an optional extra and every feature must work without it.]]
- [[mem_19444a23-the-drawer-gets-data-open-but-its-transform-does|The drawer gets `data-open`, but its transform doesn't change, so a more specific CSS rule must be overriding it.]]
- [[mem_5571676e-caps-and-dedupe-the-per-dream-budgets-readbudget|Caps and dedupe: the per-dream budgets (`read_budget`, `verify_budget`), `read_min_importance`; dropped observations are never offered again (`:360`); `meta.curated` stops repeat re-curation; auto-memory notes are deduplicated by hash.]]
- [[mem_6a1ed254-automated-tests-15-api-tests-pass-covering-bad-t|Automated tests: 15 API tests pass, covering bad tokens, `https`-only addresses, a token never being returned, re-import without duplicates, existing files kept, a GitLab merge request, and isolation between organisations.]]
- [[mem_ace30804-agents-never-read-secret-values-or-commit-env-fi|Agents never read secret values or commit `.env` files.]]
- [[mem_e39be951-the-rule-is-added-to-charter-md-but-the-matching|The rule is added to `charter.md`, but the matching explicit memory is never saved and the action returns an error.]]
- [[mem_02d7b77a-multi-line-capability-though-json-strings-suppor|Multi-line capability (though JSON strings support `\n`, and the docs don't prohibit it)]]
- [[mem_3229804f-important-constraint-additionalcontext-must-be-n|Important constraint: `additionalContext` must be nested inside `hookSpecificOutput`, not at the top level (line 647-657 of hooks-guide): "For `UserPromptSubmit` hooks, use `hookSpecificOutput.additionalContext` instead to inject text into Claude's context.]]
### Convention
- [[mem_48d2c668-categories-extract-py-14-architecture-decision-c|Categories (`extract.py:14`): architecture, decision, convention, constraint, bug, dependency, workflow, domain, rejected, finding.]]
### Dependency
- [[mem_22509f44-cosmos-ledger-an-obsidian-vault-and-an-okf-v0-2|`.cosmos/ledger/` (an Obsidian vault and an OKF v0.2 bundle): ` /mem_<8hex>- .md` – one note per fact.]]
- [[mem_e306288f-setup-and-maintenance-init-status-hook-capture-m|Setup and maintenance: `init`, `status`, `hook`, `capture`, `mcp`, `connect`, `eval`, `sync`, `watch`, `hooks`, `doctor`, `uninstall`, `update`, `upgrade`, `repair`]]
- [[mem_ff5d5561-it-can-only-update-through-the-auto-upgrade-and|It can only update through the auto-upgrade, and that needs 0.1.7 on PyPI, which still shows 0.1.5.]]
### Workflow
- [[mem_ecd1af99-prod-98a897-without-the-model-capture-saves-sent|PROD-98a897: without the model, capture saves sentence fragments like "`all` is null only if…" that make no sense on their own.]]

## Lane · horizon
### Decision
- [[mem_5dfd6673-horizon-desktop-shyftlabs-horizon-built-in-the-h|Horizon (~/Desktop/shyftlabs/horizon, built in the HORIZON session from ~/Desktop/shyftlabs) is the owner's SDLC product built on cosmos: its API imports this repository's source as an editable path dependency, and scripts/mirror-cosmos.sh refreshes horizon/.cosmos/vendor from it on every pnpm dev. So a cosmos change reaches Horizon without a release, and Horizon is cosmos's feedback loop: HORIZON reports cosmos problems to the COSMOS session, which files and fixes them here; Horizon never patches cosmos (owner, 2026-10-07).]]
- [[mem_de5d8b26-the-next-open-source-cosmos-release-ships-once-h|The next open-source cosmos release ships once Horizon works end to end; until then every cosmos problem Horizon hits is fixed here first (owner, 2026-10-07).]]
### Finding
- [[mem_4bc7ab16-the-charter-check-reported-dot-prefixed-paths-an|The Charter check reported dot-prefixed paths and globs as missing]]
- [[mem_609f22dc-repairs-run-only-after-a-pypi-upgrade-so-a-machi|Repairs run only after a PyPI upgrade, so a machine whose pip copy is the newest release keeps old user hooks and sessions above a repository get no cosmos]]
- [[mem_e147b6a4-the-desktop-entry-rename-is-undone-by-claude-des|The Desktop entry rename is undone by Claude Desktop, which rewrites its config file from memory]]
### Workflow
- [[mem_973b95cb-this-ledger-records-horizon-as-the-product-built|This ledger records Horizon as the product built on cosmos: its feedback, the fixes it needs and release readiness, in lane horizon. Horizon's own ledger records the Horizon product, which Horizon builds inside itself (owner, 2026-10-07).]]

## Lane · plugin
### Constraint
- [[mem_97f2aa55-installed-plugins-update-only-when-the-version-c|Installed plugins update only when the version changes: bump plugin/.claude-plugin/plugin.json and .claude-plugin/marketplace.json together whenever plugin files (commands, skill, bin) change, or `claude plugin update` reports 'already at the latest version'. The plugin version (0.2.0) is independent of the PyPI package version.]]
### Finding
- [[mem_a41e3c70-plugin-changes-never-reached-installed-plugins-t|Plugin changes never reached installed plugins: the plugin version stayed 0.1.0, so `claude plugin update` saw nothing new]] `stale-candidate`

## Lane · tests
### Constraint
- [[mem_50500d71-git-c-doesnt-change-the-folder-for-later-command|`git -C ` doesn't change the folder for later commands, and `git -C x commit` never matched the commit pattern anyway.]]
- [[mem_51847365-the-bundled-copy-is-0-1-5-newer-than-pypis-0-1-4|The bundled copy is 0.1.5, newer than PyPI's 0.1.4, and the runner always picks the newer of the two.]]
- [[mem_c3d4438d-if-they-dont-appear-the-cosmos-tools-still-work|If they don't appear, the cosmos tools still work, and `flare: …` still works too.]]
