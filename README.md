<p align="center"><img src="https://raw.githubusercontent.com/BiswajitBiswa/cosmos/main/docs/assets/wordmark.svg" alt="cosmos" width="300"></p>

<p align="center"><a href="https://pypi.org/project/cosmos-dev/"><img src="https://img.shields.io/pypi/v/cosmos-dev?label=pip%20install%20cosmos-dev" alt="PyPI"></a> <a href="https://github.com/BiswajitBiswa/cosmos"><img src="https://img.shields.io/github/stars/BiswajitBiswa/cosmos?style=social" alt="GitHub"></a></p>

<p align="center"><strong>The minimal operating layer for a team building software with AI.</strong><br>One committed folder · zero dependencies · git is the database</p>

<p align="center">
<a href="#the-problems">Problems</a> · <a href="#for-your-role">Roles</a> · <a href="#how-it-works">How it works</a> · <a href="#every-feature-explained">Features</a> · <a href="#every-agent--one-point-of-contact">Agents</a> · <a href="#getting-started">Get started</a> · <a href="#honest-assessment">Honest assessment</a>
</p>

<p class="md-hero"><img src="https://raw.githubusercontent.com/BiswajitBiswa/cosmos/main/docs/assets/hero.svg" alt="One system. Every agent. In sync." width="100%"></p>

cosmos brings your people, agents and context together: context that compounds, one coding style for every AI, an architecture map that cannot go stale, and a gate for the review checklist. Committed to git; nothing to run.

```bash
# first person on the repo · once · the only command
python3 -m pip install cosmos-dev && cosmos init

# everyone after that
git clone <repo> && claude
```

<table align="center">
<tr>
<td align="center" width="33%"><img src="https://raw.githubusercontent.com/BiswajitBiswa/cosmos/main/docs/assets/icon-ledger.svg" width="44" alt=""><br><strong>Ledger</strong><br><sub>Context that compounds</sub></td>
<td align="center" width="33%"><img src="https://raw.githubusercontent.com/BiswajitBiswa/cosmos/main/docs/assets/icon-charter.svg" width="44" alt=""><br><strong>Charter</strong><br><sub>One style for every AI</sub></td>
<td align="center" width="33%"><img src="https://raw.githubusercontent.com/BiswajitBiswa/cosmos/main/docs/assets/icon-atlas.svg" width="44" alt=""><br><strong>Atlas</strong><br><sub>Your living product map</sub></td>
</tr>
<tr>
<td align="center" width="33%"><img src="https://raw.githubusercontent.com/BiswajitBiswa/cosmos/main/docs/assets/icon-lanes.svg" width="44" alt=""><br><strong>Lanes</strong><br><sub>Focus and avoid overlap</sub></td>
<td align="center" width="33%"><img src="https://raw.githubusercontent.com/BiswajitBiswa/cosmos/main/docs/assets/icon-horizon.svg" width="44" alt=""><br><strong>Horizon</strong><br><sub>See a feature before it lands</sub></td>
<td align="center" width="33%"><img src="https://raw.githubusercontent.com/BiswajitBiswa/cosmos/main/docs/assets/icon-gate.svg" width="44" alt=""><br><strong>Gate</strong><br><sub>The checklist, kept by the machine</sub></td>
</tr>
<tr>
<td align="center" width="33%"><img src="https://raw.githubusercontent.com/BiswajitBiswa/cosmos/main/docs/assets/icon-flares.svg" width="44" alt=""><br><strong>Flares</strong><br><sub>QA that follows the code</sub></td>
<td align="center" width="33%"><img src="https://raw.githubusercontent.com/BiswajitBiswa/cosmos/main/docs/assets/icon-dream.svg" width="44" alt=""><br><strong>Dreams</strong><br><sub>From activity to direction</sub></td>
<td align="center" width="33%"><img src="https://raw.githubusercontent.com/BiswajitBiswa/cosmos/main/docs/assets/icon-verdicts.svg" width="44" alt=""><br><strong>Verdicts</strong><br><sub>The human gate</sub></td>
</tr>
</table>

---

## The problems

**Eight things every team building with AI says out loud, three months into a real project.** Each one is a symptom of the same cause: knowledge, rules and structure live in individual sessions instead of in the repository.

<table>
<tr><td width="44"><img src="https://raw.githubusercontent.com/BiswajitBiswa/cosmos/main/docs/assets/icon-ledger.svg" width="36" alt=""></td><td><em>“Everyone rescans the codebase.”</em><br><strong>Ledger</strong> · What one person's AI learns is captured, checked and handed to the next person's session before they ask.</td></tr>
<tr><td><img src="https://raw.githubusercontent.com/BiswajitBiswa/cosmos/main/docs/assets/icon-charter.svg" width="36" alt=""></td><td><em>“Everyone tells the AI a different coding style.”</em><br><strong>Charter</strong> · One working agreement, committed and changed in pull requests, injected into every AI session on every machine.</td></tr>
<tr><td><img src="https://raw.githubusercontent.com/BiswajitBiswa/cosmos/main/docs/assets/icon-lanes.svg" width="36" alt=""></td><td><em>“People work across overlapping features.”</em><br><strong>Lanes</strong> · Facts, findings and diagrams are filed by feature lane; two people active in one lane this month is shown before it becomes a merge conflict.</td></tr>
<tr><td><img src="https://raw.githubusercontent.com/BiswajitBiswa/cosmos/main/docs/assets/icon-charter.svg" width="36" alt=""></td><td><em>“Everyone has different strengths and thinking.”</em><br><strong>Charter + Ledger</strong> · Strengths become team property: the person who knows Redis writes the constraint once; every AI inherits it. Thinking stays personal, decisions get a recorded reason.</td></tr>
<tr><td><img src="https://raw.githubusercontent.com/BiswajitBiswa/cosmos/main/docs/assets/icon-horizon.svg" width="36" alt=""></td><td><em>“Product keeps dumping features; the app gets confusing.”</em><br><strong>Horizon</strong> · A feature enters with its lanes, the decisions it collides with, the open findings in the way and the people already there, before code is written.</td></tr>
<tr><td><img src="https://raw.githubusercontent.com/BiswajitBiswa/cosmos/main/docs/assets/icon-atlas.svg" width="36" alt=""></td><td><em>“No architecture diagram. If there is one, it is out of date.”</em><br><strong>Atlas</strong> · Diagrams generated from the repository itself (manifests, compose, Kubernetes, Terraform, OpenAPI) and drift-checked every time those files change.</td></tr>
<tr><td><img src="https://raw.githubusercontent.com/BiswajitBiswa/cosmos/main/docs/assets/icon-lanes.svg" width="36" alt=""></td><td><em>“Memory is one flat list, not organised by feature.”</em><br><strong>Lanes</strong> · The ledger, the index and <code>CLAUDE.md</code> are grouped by lane, the way the team actually talks about the product.</td></tr>
<tr><td><img src="https://raw.githubusercontent.com/BiswajitBiswa/cosmos/main/docs/assets/icon-gate.svg" width="36" alt=""></td><td><em>“Every call: did you self-review, point precisely, run the tests?”</em><br><strong>Gate</strong> · A hook holds the AI's turn until the tests for touched files ran, each change cites <code>file:line</code>, open findings on those files are addressed, a large change got a dead-code scan (vulture, knip), and the diff is reviewed against the Charter.</td></tr>
</table>

## For your role

**The same folder, read from five seats.**

| | the complaint | what changes |
|---|---|---|
| **Product manager** | “I keep adding features and the app gets more confusing. Nobody tells me what a feature collides with until it is half built.” | **Horizon** answers before a line is written: lanes touched, decisions it collides with, open findings in the way, who owns the area. The **Atlas** shows the real shape of the product, always current. |
| **Project manager** | “Three people ended up in the same feature. Every call repeats the same three asks. I cannot see who knows what.” | **Lanes** show who is active where and flag overlap this month. The **Gate** asks the three questions so the call does not have to. Dreams and Verdicts give a weekly rhythm: consolidate, decide, commit. |
| **Developer** | “I re-learn the codebase every session. My AI writes in a different style from my teammate's. I did not know that constraint existed.” | The **Ledger** hands over what others learned, matched to the files you touch. The **Charter** makes every AI write the same way. `remember:` keeps what you found in ten seconds. |
| **QA** | “My findings live in a document nobody reopens. Fixed bugs come back. Nobody tells me when a finding is picked up.” | **Flares** have a lifecycle and a board. A fixed bug reported again is flagged *regressed*. An open finding on a file the AI edits is raised at the **Gate**. Cards go to Slack once, with reactions to claim or close. |
| **Tech lead** | “There is no diagram, or it is a month old. Decisions live in people's heads.” | The **Atlas** is generated from the repo and drift-checked. Every decision in the **Ledger** carries its reason, evidence and date; contradictions surface instead of silently coexisting. |

## How it works

**Five steps. The developer does only the first.** The gold step is where the model curates; a person decides only what evidence cannot settle.

<p class="md-wide"><img src="https://raw.githubusercontent.com/BiswajitBiswa/cosmos/main/docs/assets/pipeline.svg" alt="Work → Capture → Model curates → Ledger → Recall" width="100%"></p>

| | step | what happens |
|---|---|---|
| 1 | **Work** | Use your agent as usual. The Charter, top facts and Atlas status are already in context. |
| 2 | **Capture** | Hooks mark the session range for the model, keep explicit `remember:` lines at once, and write one journal line per turn: what was asked, which files changed, which commits landed. Transcripts are read in place, never copied. |
| 3 | **Dream** | Runs by itself when enough is waiting. The model reads the marked session ranges in context and this developer's own Claude Code auto memory notes, and writes down what the team should still know in six months (keep · rewrite · category · lane). Duplicates merge, contradictions are flagged, facts are filed by lane, the Atlas is drift-checked. A human settles what evidence cannot. |
| 4 | **Ledger** | One markdown note per fact, with evidence. Committed. Opens as an Obsidian vault. |
| 5 | **Gate & recall** | Before the agent edits a file it is told what the team knows about that file: open flares, constraints, rules. A turn that edits code is held once: tests, `file:line`, flares addressed, and *record what the team learned* via `cosmos_remember`. A commit message naming a flare closes it. Nothing is asked of the person. |

> **Git is the database, in your branch.** `.cosmos/` is ordinary committed files in the branch where you ran `cosmos init`, so every branch made from it carries the team memory and merging a branch shares it. cosmos commits `.cosmos/` to the current branch every 10 minutes while you work and after each dream, in its own commit that holds nothing else (amended while unpushed, so a session leaves one). It never pushes: the memory goes out with your branch. Append-only files (journal, log, observations) merge by union, so two branches do not conflict there. No server, no account, no cloud, and nothing beyond the repository itself and the open-source cosmos. (Prefer the ledger on a separate branch? `cosmos init --branch`.)

## Every feature, explained

**What it is, what you do, what you get, and the command.** Nothing here needs a server or an account.

### <img src="https://raw.githubusercontent.com/BiswajitBiswa/cosmos/main/docs/assets/icon-ledger.svg" width="28" alt=""> Ledger · what the team knows

| | |
|---|---|
| **what** | One markdown note per fact the team has learned (architecture, decisions and their reasons, conventions, constraints, bug root causes, dependency limits, workflows, domain rules), each with the files that prove it, the dates it was seen, how many times, and by whom. |
| **you do** | Nothing. Work in your AI tool; facts are captured when a turn ends. Type `remember: …` when something must be kept for sure. |
| **you get** | Your next session, and every teammate's, starts knowing what the last one learned, one line per fact with its id; the full note with evidence and history is one call away (`cosmos_why`). Every fact carries when it became true and when it stopped. |
| **command** | `cosmos capture` · `cosmos why` · `cosmos search` · `cosmos remember` |

### <img src="https://raw.githubusercontent.com/BiswajitBiswa/cosmos/main/docs/assets/icon-charter.svg" width="28" alt=""> Charter · one style for every AI

| | |
|---|---|
| **what** | A short file, `.cosmos/charter.md`: how we write code, how we test, how we point at things, how we review our own work, our architecture rules. Owned by the team, changed in pull requests. |
| **you do** | Agree it once. Add a rule when a decision is made, from the UI, the CLI, or by typing `remember:` in a session. Text pasted above the settings header is moved into the body when the editor closes. |
| **you get** | Every AI session on every machine reads it first. Personal preferences stop leaking into the codebase. Explicit rules outrank anything the AI inferred. |
| **command** | `cosmos charter` · `cosmos charter add "…"` · `cosmos charter edit` |

### <img src="https://raw.githubusercontent.com/BiswajitBiswa/cosmos/main/docs/assets/icon-atlas.svg" width="28" alt=""> Atlas · architecture that stays true

| | |
|---|---|
| **what** | Inventory, container, deployment and API diagrams generated from what the repository already declares: package manifests, docker-compose, Kubernetes, Terraform, OpenAPI, `.env.example`, README. Every source file is fingerprinted. |
| **you do** | Nothing. `cosmos init` builds the inventory; the next dream lets the model follow the Atlas prompt and write system context, containers, data flow, deployment, a dependency index and proposed lanes. It runs again when the code the Atlas read moves. `/atlas` in Claude Code does the same interactively. |
| **you get** | A diagram that cannot quietly go stale: when compose or manifests change and the picture does not, everyone is told at the start of their session and on the Atlas page. |
| **command** | `cosmos atlas` · `cosmos atlas --deep` · `cosmos atlas --check` · `/atlas` |

### <img src="https://raw.githubusercontent.com/BiswajitBiswa/cosmos/main/docs/assets/icon-lanes.svg" width="28" alt=""> Lanes · memory by feature

| | |
|---|---|
| **what** | Every fact, finding and diagram is filed under the feature or module it belongs to: proposed by the model, refined from the files it points at, or configured by you. |
| **you do** | Optionally name your lanes in `config.json`, or let `cosmos lanes --propose --write` do it. Otherwise nothing. |
| **you get** | A ledger organised the way the team talks about the product; per lane, who has been active in the last 30 days and where two people overlap, before it becomes a merge conflict. Each lane is an OKF concept page under `ledger/lanes/` that links its facts, flares, horizon notes and services, so the graph of the product is a folder anyone can open. |
| **command** | `cosmos lanes` · `cosmos lanes --propose --write` |

### <img src="https://raw.githubusercontent.com/BiswajitBiswa/cosmos/main/docs/assets/icon-horizon.svg" width="28" alt=""> Horizon · features arrive with a map

| | |
|---|---|
| **what** | A one-sentence feature request turned into an impact note: lanes touched, recorded decisions it collides with, open findings in the way, people who have been working there, a suggested owner. Takes files, folders and attachments for context. |
| **you do** | `cosmos horizon "bulk invite with partial success" -f src/invites`, or type it on the Horizon page and drop files in. |
| **you get** | The conversation about a feature happens before the code, with facts. The note is saved next to the code the feature will change and travels with the pull request. |
| **command** | `cosmos horizon "…" [-f file-or-folder] [--attach file] [--brief file]` |

### <img src="https://raw.githubusercontent.com/BiswajitBiswa/cosmos/main/docs/assets/icon-gate.svg" width="28" alt=""> Gate · the review checklist, applied by the machine

| | |
|---|---|
| **what** | A check that runs when the AI says it is done. If the turn changed code but ran no tests, gave no `file:line` references, or ignored an open finding on a file it touched, the AI is handed the exact list and keeps going. |
| **you do** | Nothing. Tune the rules in the Charter if you want. |
| **you get** | “Did you test? Point precisely. Review your own change.” stops being something a person says on every call, and the agent writes down what it learned while it still has the full context. Proportional: a change under 400 characters in one file is held only for its `file:line` and open flares. A turn is held at most once; documentation edits are never held. Bugs found are filed as flares without asking. |
| **command** | `cosmos gate` · `cosmos gate --transcript FILE` |

### <img src="https://raw.githubusercontent.com/BiswajitBiswa/cosmos/main/docs/assets/icon-flares.svg" width="28" alt=""> Flares · QA that follows the code

| | |
|---|---|
| **what** | Audit findings as memory with a lifecycle: open → claimed → PR open → fixed, or needs a human, won't fix, withdrawn. A fixed bug reported again is flagged *regressed*. |
| **you do** | Import the audit JSON, type `flare: …` in a session, or record bugs found by hand: **＋ Record bugs** on the Flares page, `cosmos flares add "…"`, or a list (`--from bugs.csv`, `.xlsx`, `.txt`). Move cards on the board or with one command. |
| **you get** | Flares show up when someone touches the affected file. Slack cards post once, with reactions to claim or close. A report can be regenerated any time. |
| **command** | `cosmos flares add\|import\|list\|fix\|withdraw\|slack\|report` |

**Security for code written by agents.** Every turn the Gate reads the files it touched for credentials, hidden Unicode (Trojan Source, invisible prompt text) and text that steers an agent inside the files agents read as instructions, and holds the turn until a changed dependency manifest has been audited; large changes also run bandit or semgrep. A ledger note that reads like instructions to an agent is withheld from every agent until a person looks. `cosmos scan [--tools]` checks the whole repository ([guide](https://github.com/BiswajitBiswa/cosmos/blob/main/docs/charter-and-gate.md#security-on-every-turn)).

### <img src="https://raw.githubusercontent.com/BiswajitBiswa/cosmos/main/docs/assets/icon-charter.svg" width="28" alt=""> Playbooks · the team's own prompts, in every agent

| | |
|---|---|
| **what** | A team's long-form prompt (a master QA protocol, a release runbook, an SEO playbook) becomes a slash command for every agent. The command reads the file and follows it, so editing the file changes what every agent does. |
| **you do** | Keep the file in the repository (named *protocol* / *playbook* / *runbook* / *master prompt*, or anywhere in `.cosmos/playbooks/`), or bring one in with `cosmos playbooks add <file>`. |
| **you get** | `/<name>` in Claude Code (also in its skill list), Gemini CLI, Cursor, Copilot and Windsurf; Codex as a project skill (`.agents/skills/`); every other agent finds it listed in `AGENTS.md`. `/qa` follows the QA one. |
| **command** | `cosmos playbooks [add <file\|qa>]` · [guide](https://github.com/BiswajitBiswa/cosmos/blob/main/docs/playbooks.md) |

### <img src="https://raw.githubusercontent.com/BiswajitBiswa/cosmos/main/docs/assets/icon-dream.svg" width="28" alt=""> Dream & Verdicts · keeping it true

| | |
|---|---|
| **what** | The model reads every new observation and decides what is worth keeping, rewrites it crisply, names its category and its feature lane. Then duplicates merge, contradictions are flagged, old facts are marked for review, the Atlas is drift-checked. Anything evidence cannot settle waits for a person on the Verdicts page. |
| **you do** | Run a dream now and then (or nightly in CI), glance at Verdicts, commit. |
| **you get** | A ledger that stays small and right. Every human decision (keep, both valid, still true, forget) is recorded with who and when. |
| **command** | `cosmos dream` · `cosmos review` · the Verdicts page |

**Also in the box**

| | |
|---|---|
| **Handoff** | The last thing said on a branch is kept as its handoff, automatically; `cosmos_handoff(learned, open, next)` when stopping mid-work. The next session on that branch, on any machine, opens with it. |
| **Team sources** | Git history and pull-request review comments feed the ledger without anyone installing anything: every commit by anyone becomes a journal line; commit bodies and review remarks are offered to the model as candidate rules and facts. Reviews need the GitHub CLI logged in; on by default when it is. |
| **Open Knowledge Format** | The ledger is a conformant OKF v0.2 bundle, Google's open spec for knowledge as markdown with YAML frontmatter, so nothing about the format is invented here. Every note carries `type`, `title`, `description`, `generated`, `verified`, `status`, `stale_after` and `links`; `index.md` and `log.md` sit at the root. Relationships are OKF links: each **lane** is a concept page linking its facts, open flares, horizon notes, the **services** whose code it touches (one concept per app, service and store the Atlas found, with `resource` pointing at the code) and the people active there; each fact links back to its lane and to what it supersedes, contradicts or relates to. Any OKF consumer or graph viewer can read and traverse it; the console, Obsidian and `okf_search`-style tools all see the same graph. Retrieval is BM25 with an evidence-path boost, no vectors. |
| **Recall, measured** | Every dream that changed the memory measures two things on the repository's own facts and code: how often the fact about the code being edited is shown before the edit, and recall@5 for questions and file lookups (only files with five facts or fewer, where one fact can rank first). A fall of five points or more is named on the Dreams page and in `cosmos doctor`; numbers are only compared with runs measured the same way. On two real repositories, choosing pre-edit facts by the edit raised the first number from 39% to 81% and from 52% to 85%. `cosmos eval` runs both now. |
| **Watch** | `cosmos watch` is one local process that tails every agent's own session files for this repository, all worktrees and subagents included, captures what is new, shows who is working on what right now in the console, and starts dreams when enough is waiting. It needs no hooks, so it also covers sessions opened before cosmos existed and agents without a hook system. |
| **Recall at the edit** | The moment the agent opens a file to change it, it sees the open flares on that file, its explicit rules, and the facts that match the code being changed: a file can carry a hundred facts, and the one about the function being edited is the one that matters. Each fact is shown once per session, so a later edit elsewhere in the file brings what is relevant there. Knowledge arrives at the decision, not in a report afterwards. |
| **Journal** | What the team did, not only what it learned: one line per agent turn with the ask, the files, the commits and the branch, filed by lane and person under `ledger/journal/`. A session that ships five commits and teaches no new fact is still on record. |
| **Atlas page** | Every `cosmos atlas` also writes `.cosmos/ledger/atlas/atlas.html`: all diagrams and documents on one page in cosmos's look, with a sidebar that follows you, and diagrams you drag, zoom, fit and open full screen. `--format md` writes Markdown only. |
| **Lane aliases & moved evidence** | `lane_aliases` in `.cosmos/config.json` folds near-duplicate lanes (`deploy-config` → `deploy`) in every view; `cosmos lanes --propose` suggests them. `cosmos review --repoint` follows git's renames for stale facts and reports repointed · still stale · ambiguous. |
| **Private words** | Any word in `~/.config/cosmos/private_terms.txt` (one per line: names, companies, anything) is redacted from every capture in every repository, like a key or a token. The list lives in your home folder, so it is never committed. |
| **Control room** | `cosmos ui`: overview, ledger, lanes, atlas, charter, horizon, flares, dreams, verdicts, activity, docs. Localhost only; picks a free port. It keeps cosmos's near-black and gold over a slowly drifting night-storm sky seen through glass panels (every text colour measured at 4.5:1 or better over the brightest cloud); `ui.background` in `.cosmos/config.json` swaps the sky for your own image or video, served only from your machine. Buttons, fields and chips share one size and focus ring, and every page fits a phone. The sidebar folds to an icon rail (the arrow at its top right; remembered per browser; always the rail on a phone). A fact or flare opens in a dialog above the page. Status changes ask in the console's own dialog — Cancel, Escape or a click outside changes nothing, and Withdraw / Won't fix need a reason. Long lists page in the browser (50 facts, 10 rules, 30 flares per column) and long texts fold to three lines, so a ledger of thousands needs no server; `cosmos ui --static` is the same page as one file. **⬇ Excel** (or `cosmos export`) downloads flares, facts, rules, lanes, endpoints and playbooks as one workbook. |
| **The model** | Uses your existing Claude Code login by default (`claude -p`), or `ANTHROPIC_API_KEY`, or any OpenAI-compatible endpoint. `COSMOS_LLM_PROVIDER=none` runs heuristics only, and says so. |
| **Privacy first** | API keys, tokens, passwords, private keys and credentials in URLs are redacted before anything is written. Sensitive folders can be excluded. Transcripts are read, never stored. |
| **Never in the way** | Hooks finish in milliseconds and exit clean. The Gate is the one deliberate hold, and it explains itself. |

## Every agent · one point of contact

**Claude Code, Codex, Gemini, Cursor, Copilot, Cline, Cowork: one store.** Teams do not use one AI tool. cosmos meets each of them three ways, and everything lives in the repository, so sharing it is a `git push`.

<table>
<tr>
<td width="33%" valign="top"><img src="https://raw.githubusercontent.com/BiswajitBiswa/cosmos/main/docs/assets/icon-charter.svg" width="36" alt=""><br><strong>They read the same rules</strong><br>The Charter and the key facts are written to every tool's own instruction file, kept in sync automatically.<br><br><code>CLAUDE.md</code> — Claude Code, Cowork<br><code>AGENTS.md</code> — Codex, Cursor, Copilot CLI, Gemini<br><code>GEMINI.md</code>, <code>.cursor/rules/</code>, <code>.github/copilot-instructions.md</code>, <code>.clinerules</code>, <code>.windsurfrules</code></td>
<td width="33%" valign="top"><img src="https://raw.githubusercontent.com/BiswajitBiswa/cosmos/main/docs/assets/icon-agents.svg" width="36" alt=""><br><strong>They call the same tools</strong><br><code>cosmos mcp</code> is a Model Context Protocol server every one of these agents can connect to. <code>cosmos init</code> writes the configs.<br><br><code>cosmos_recall</code> — facts and findings for the files you are about to touch<br><code>cosmos_remember</code>, <code>cosmos_flare</code> — write back from any tool<br><code>cosmos_charter</code>, <code>cosmos_atlas</code>, <code>cosmos_lanes</code>, <code>cosmos_horizon</code>, <code>cosmos_why</code></td>
<td width="33%" valign="top"><img src="https://raw.githubusercontent.com/BiswajitBiswa/cosmos/main/docs/assets/icon-session.svg" width="36" alt=""><br><strong>They feed the same memory</strong><br>Claude Code captures through hooks, in every worktree. <code>cosmos watch</code> follows Claude Code, Codex and Gemini session files on the machine whether hooks fired or not, and keeps a live picture of who is doing what. Web and cloud sessions are covered by the committed hooks and MCP tools. Anything else writes through MCP.<br><br>hooks in the repo and for your user, written by <code>cosmos init</code><br>the watcher starts with the first session and stops after two idle hours<br><code>git push</code>: every teammate on every tool has it<br><br><sub>Nothing to run after <code>cosmos init</code>. <code>cosmos connect all</code>, <code>cosmos watch</code> and <code>cosmos hooks --user</code> repair a setup or add a tool you install later.</sub></td>
</tr>
</table>

<p align="center"><sub>Claude Code · Cowork · Codex CLI · Codex Desktop · Gemini CLI · Antigravity · Firebase Studio · Cursor · GitHub Copilot · Cline · Windsurf · Obsidian</sub></p>

### Cowork, and sessions that were already open

**Cowork** runs Claude Code in a sandbox with its own settings, so a project's hooks and a local MCP server in Claude Desktop's config never reach it. The cosmos plugin does. This repository is also a plugin marketplace: in Cowork, add it as a marketplace (its GitHub `owner/cosmos` path) and install **cosmos**. The plugin finds every shared folder that has `.cosmos/`, one level down included (a workspace folder of several projects), and serves that repository's own copy of cosmos over MCP, so no install is needed inside the sandbox. Cowork starts a fresh process for each message, so the tools appear with your next message, in the session you already have open. The same plugin works in Claude Code: in a terminal, `claude plugin marketplace add owner/cosmos` then `claude plugin install cosmos@cosmos` (inside the Claude Code CLI the same as `/plugin …`; the Claude desktop app has no `/plugin` command, use its Plugins screen). With the plugin, the commands are also `/cosmos:recall`, `/cosmos:flare` …. **Codex** installs the same plugin from its Plugins screen (add the marketplace `BiswajitBiswa/cosmos`, install **cosmos**): its hooks brief each thread and start the watcher, and one MCP server serves whichever repository the thread is in, so a Codex teammate runs no command at all ([plugin guide](https://github.com/BiswajitBiswa/cosmos/blob/main/docs/plugin.md#codex)). Capture from Cowork needs no plugin: the watcher reads Cowork transcripts on the machine and maps the sandbox paths back.

**You see what it recalled.** Each time cosmos puts something in front of the agent, Claude Code shows one line: `cosm◎s · loaded the Charter, 10 facts and rules` at the start, `cosm◎s · recalled 3: …` for a prompt, `cosm◎s · 1 open flare and 2 notes on <file>` before an edit. The briefing stays under Claude Code's 10,000-character hook limit, so the model reads all of it rather than a preview.

**Sessions opened in a folder above the repository** (a workspace folder holding several projects) work too. The user-level hook hands each event to every repository one level down. Each one adds a single line saying where its team memory is, and the facts when a prompt names it. Its watcher captures only the turns that touched it. A repository's worktrees answer once, and the Gate ignores files that belong to a sibling repository.

**Firebase Studio** (formerly Project IDX; no new workspaces since 2026-06-22, shut down 2027-03-22) reads `GEMINI.md` and `AGENTS.md`, which cosmos writes. In a workspace with `.idx/`, cosmos adds its MCP server to `.idx/mcp.json` and its block to the team's `.idx/airules.md`, which Gemini there reads first. **Icons:** Codex shows the cosmos mark on the plugin; Claude Code has no icon field for plugins, commands or skills.

**A session in another project never writes here.** A global MCP entry (Claude Desktop's config) offers one repository's cosmos to every session. cosmos asks the client which folders the session works in, and in any other project its tools answer "not this project" and record nothing. Each write names the repository it went to.

**Sessions older than cosmos.** The user-level hooks run in every repository and check for `.cosmos/` on each event, so a Claude Code session that was open before `cosmos init` starts capturing on its next turn, and its next prompt carries the briefing it missed at start (Charter, key facts, handoff, Atlas). Nothing to restart.

## Measured on a live repository

`cosmos pulse --bench` on one live product repository, 2026-10-01: two people, seven days, Claude Code, Codex and Cowork. Every number is read from that repository's `.cosmos/` records or from running its hooks.

| | |
|---|---|
| agent turns recorded | 723 (tests ran in 146) |
| active team facts | 2,085 (82 rules a person stated) |
| recall@5 · before an edit | 0.81 · 0.65 (45 evals) |
| context per prompt | 329 tokens median; facts reached 35 of 43 prompts |
| session-start briefing | 8,452 characters, under Claude Code's 10,000 hook limit |
| time per hook | 285–398 ms median in a fresh process (700–790 ms before the parsed-ledger cache) |
| flares | 175: 50 fixed, 114 open |
| dreams | 37, 31 curated by the model, 8,158 session turns read |

## Getting started

**One person runs one command once. Everyone else clones.** Nothing else is a step: capture, reading, dreams, the watcher and the hook refresh happen by themselves.

**1 · `cosmos init`, once.** Creates `.cosmos/` with the Charter, the Ledger, the first Atlas and the slash commands (`/cosmos` `/recall` `/remember` `/flare` `/flares` `/qa` `/reconcile` `/lanes` `/horizon` `/handoff` `/atlas`) for Claude Code, Gemini CLI, Cursor, Copilot and Windsurf, plus one per playbook the repository already has (a master QA protocol, a runbook: found by themselves, and `/qa` follows the QA one; `cosmos playbooks add qa` starts a generic one, `cosmos playbooks add <file>` brings one from another project); wires hooks at repo and user level, so every worktree is covered; writes MCP configs and the instruction files of every agent; reads the sessions this repo already had, writes their journal, marks the recent ones for the model, and starts the first dream and the watcher in the background.

```bash
python3 -m pip install cosmos-dev   # `python3 -m pip` keeps the `cosmos` command and its Python together
cd <your-repo>
cosmos init
cosmos flares import <findings.json>   # only if you have an audit document; ids follow the lifecycle stage
```

**2 · Agree the Charter, then commit.** Edit `.cosmos/charter.md` in a pull request; that is the team agreeing on one style. Commit and the memory becomes the team's.

```bash
cosmos charter edit
git push   # cosmos init already committed .cosmos/ and the agent wiring to this branch
```

**3 · Everyone else clones and opens their agent.** No install, no setup. Claude Code, Codex, Cursor, Gemini CLI, Copilot, Cline or Cowork all read the same Charter, facts and tools; a committed wrapper runs cosmos from the repository. Sessions that were already open pick cosmos up on their next turn; Cowork gets the tools from the cosmos plugin.

```bash
git clone <repo> && cd <repo>
# open your agent: claude · codex · cursor . · gemini · …
```

**4 · Look, now and then.** `cosmos ui` shows the live sessions, the ledger, the lanes, the flares and what waits for a human on Verdicts. Dreams run by themselves; commit `.cosmos` with your normal work and everyone gets it on the next `git pull`. Map a feature before coding with `cosmos horizon "<feature in one sentence>"` or on the Horizon page.

**It updates itself.** Once a day a session start checks PyPI in the background. A newer release is downloaded, checked against PyPI's sha256, tested to import, and swapped into the repository's committed copy (`.cosmos/vendor`); cosmos commits it, so every teammate runs it after their next `git pull`, with or without a pip install. A pip install on the machine is upgraded too when pip allows it. Each new version then repairs, once per machine, what older versions wrote: hook commands, slash commands, the Codex plugin listing (`.agents/plugins/marketplace.json`, so Codex users install cosmos from the Plugins screen with one click) and a Claude Desktop MCP entry that sent every session's facts to one repository. `cosmos upgrade --check` says where a repository stands, `cosmos repair` runs the repairs now; `"update": {"auto": false}` in `.cosmos/config.json` turns it off.

> **Want a fact or rule kept for certain?** Type `remember: never modify production schemas by hand` or `flare: /transitions has no role gate` in any agent, or call `cosmos_remember` over MCP. Explicit rules always outrank inferred ones.

## Already have a codebase?

**Link an existing project and its past sessions.** Most projects already have months of history: AI sessions on several machines, an audit document, branches nobody has drawn. `cosmos init` brings the sessions in by itself; the rest is agreeing the Charter and committing. Full guide: [docs/link-existing-codebase.md](https://github.com/BiswajitBiswa/cosmos/blob/main/docs/link-existing-codebase.md).

| | step | command |
|---|---|---|
| 1 | Initialise. This also reads every past session (all worktrees, subagents), writes their journal, marks recent history for the model, starts the first dream and the watcher | `cd <your-repo> && cosmos init` |
| 2 | Bring in an existing audit, if there is one. If the file does not exist yet, cosmos asks before creating an empty one to fill in (`--yes` creates it without asking). A list of bugs the team kept by hand (a sheet, a CSV, notes) comes in with `add`. | `cosmos flares import <findings.json> --source <report-name>` · `cosmos flares add --from bugs.xlsx` |
| 3 | Look while the first dream finishes in the background | `cosmos ui` |
| 4 | Agree the Charter and push | `cosmos charter edit` · `git push`. `cosmos init` committed `.cosmos/` and the agent wiring to the branch you ran it on; run it on a branch off your base branch if you want it reviewed in a pull request. |
| 5 | Sessions that were already open | nothing to restart: the next prompt carries the briefing; in Cowork, install the cosmos plugin once ([plugin](https://github.com/BiswajitBiswa/cosmos/blob/main/docs/plugin.md)) |
| 6 | Teammates | `git pull`, then open their agent |

Transcripts live in `~/.claude/projects/<repo path, slashes → dashes>/` (Claude Code), `~/.codex/sessions/` (Codex), `~/.gemini/` (Gemini). They are read, never stored; secrets are redacted. `.claude/settings.local.json` is personal and untouched; `.cosmos/state/` is gitignored.

## What we learned from others

**We took the ideas that need no infrastructure.** Several tools solve pieces of this well. We kept every strength that works with nothing more than git and a command line, and left out what needs an engine.

| tool | its strength | in cosmos |
|---|---|---|
| Letta Context Repositories | Memory is versioned in git; conflicts are settled in pull requests. | The Ledger and Charter are markdown in the repo. Every change is a diff; contradictions go through review. |
| ai-memory | Local-first, driven by editor lifecycle hooks. | Hooks capture in milliseconds; the model does the thinking later, at dream time. |
| MemContext | Facts cite their source; the system learns from human corrections. | Every fact carries evidence files, dates and observers. Verify, keep and forget decisions are recorded as memory. |
| ZeroShot | One memory shared across Claude Code, Cursor and Copilot. | Charter and facts are written to every agent's instruction file and served over MCP. |
| ContextOps practice | A hierarchical `CLAUDE.md` / `AGENTS.md`: what, how, why. | Generated and kept current: the Charter is the *how*, the Ledger the *why*, the Atlas the *what*. |
| Architecture-diagram prompts | “Inventory first, then diagrams” gives good Mermaid from a repo. | Built in: `cosmos atlas` does the inventory from files git tracks; dreams run the prompt as a deep pass through the model; drift triggers the next one. |
| Augment Code | Maps dependencies across 400k-file codebases. | Deliberately not taken. That needs an indexing engine. cosmos stays a few thousand lines of standard-library Python. |

## Honest assessment

| Why it is a good fit | Where it falls short today |
|---|---|
| Nothing to run. No database, no server, no account, and no API key: the model is your existing Claude Code login. | Hooks do not extract anything themselves: they mark the session range and write the journal, and the model reads the conversation at dream time. Reading costs model calls (about one per 9k characters of session), so a busy team's dream takes minutes, in the background. With no model available for three days, the old heuristics keep what they can, and the dream says so. |
| Zero effort for developers after the first setup; the second person just clones. | The Atlas reads manifests and specs, not a code graph: no call chains, no dependency analysis inside the code. |
| One place for rules, facts and structure, inspectable as plain files, diffs and Obsidian notes. | The Gate checks that tests *ran*, not that they were the right tests or that they passed. |
| Wrong facts cannot hide: evidence and age on every one. Stale diagrams cannot hide: drift is reported. | Capture and Gate hooks exist for Claude Code only; Codex and Gemini are read from their logs; other agents write through MCP. |
| The review checklist stops being a person's job. | Memory is per repository; cross-repo recall inside the hooks does not exist yet. |
| Privacy by construction: local-first, secrets redacted, transcripts never stored. | Verdicts are trust-based; the audit trail is git history, not roles. No Jira integration. |

## Checked by something that is not Claude

cosmos is built with Claude. It should not be graded by Claude. `validation/` asks an independent decision-only model (TypeSafe's Jev) a fixed set of closed questions about what cosmos produced in your repository, compares the answers with what cosmos decided, and writes one report with aggregates only: does the evidence support each fact, should each observation have been kept, is each doubtful fact really outdated, is each retrieved fact relevant, does the code implement each documented claim. New features are reported separately from existing ones. One command, a key from typesafe.ai or Cloudflare Workers AI, about half a cent per repository. See [validation/README.md](validation/README.md).

## Why use this

**The cost you pay today is invisible.** Nobody files a ticket for “rediscovered the same constraint as last week”, “the AI used a different style again”, or “the diagram was wrong”. It shows up as slower onboarding, repeated mistakes, review calls that repeat themselves, and a quiet erosion of trust in the AI tools. cosmos makes the knowledge, rules and structure that already exist in your team stay put, for the price of one `init`.

And it is safe to try. It writes one folder and a few lines into files you already have. Remove the hooks with one command (`cosmos uninstall`) and nothing else changes.

## Why we made this

**Three months in, eight complaints, one cause.** We were building a product across several repositories with Claude Code. People overlapped on features, each told the AI a different style, product added features faster than the picture could hold, there was no architecture diagram anyone trusted, and every call repeated the same asks. A QA audit produced twenty-nine findings that lived in a document nobody reopened.

The tools we looked at either wanted a hosted service or solved one slice. We wanted the minimal whole: memory, rules, structure and a gate, versioned with the code, with nothing to operate.

> The killer feature is not that the AI remembers. It is that the team stops repeating itself.

## Layout

```
.cosmos/              committed in your branch; cosmos commits it, you push it with the branch (state/ stays local)
  charter.md          the team's working agreement (injected first)
  ledger/             one markdown note per fact · finding/ (flares) · horizon/
  atlas/              inventory + Mermaid diagrams, fingerprints
  config.json         lanes, LLM provider, excludes
  cosmosw             zero-install wrapper (runs the vendored copy)
  state/              gitignored: pending observations, dream runs
```

Guides: [playbooks](https://github.com/BiswajitBiswa/cosmos/blob/main/docs/playbooks.md) · [plugin (Cowork, Claude Code, Codex)](https://github.com/BiswajitBiswa/cosmos/blob/main/docs/plugin.md) · [memory model](https://github.com/BiswajitBiswa/cosmos/blob/main/docs/memory-model.md) · [charter and gate](https://github.com/BiswajitBiswa/cosmos/blob/main/docs/charter-and-gate.md) · [lanes and horizon](https://github.com/BiswajitBiswa/cosmos/blob/main/docs/lanes-and-horizon.md) · [atlas](https://github.com/BiswajitBiswa/cosmos/blob/main/docs/atlas.md) · [audit and findings](https://github.com/BiswajitBiswa/cosmos/blob/main/docs/flares.md) · [hooks](https://github.com/BiswajitBiswa/cosmos/blob/main/docs/hooks.md) · [Obsidian](https://github.com/BiswajitBiswa/cosmos/blob/main/docs/obsidian.md) · [link an existing codebase](https://github.com/BiswajitBiswa/cosmos/blob/main/docs/link-existing-codebase.md)

<p align="center"><sub>cosmos · MIT licence · Python 3.9+, standard library only · <code>cosmos doctor</code> checks a setup · <code>cosmos ui</code> opens the control room</sub></p>
