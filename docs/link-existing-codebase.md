# Link an existing codebase and its past sessions

cosmos is usually added to a project that already has months of history: AI sessions on several machines, an audit document, branches nobody has drawn. These steps bring all of it into one `.cosmos/` folder. Works the same for Claude Code, Codex, Cursor, Gemini CLI, Copilot, Cline or Cowork.

## 1. Initialise in the repository
```bash
cd <your-repo> && cosmos init   # also reads past sessions, writes the journal, starts the first dream and the watcher
```

## 2. Link past sessions
```bash
cosmos capture --agent claude --transcript <path-to-session>.jsonl -v   # one session
cosmos capture --agent codex  --transcript <path-to-rollout>.jsonl -v   # a Codex session
# (optional) force it by hand:
cosmos capture --agent all -v
cosmos capture --agent claude --rebuild-journal
```

## 3. Bring in an existing audit
```bash
cosmos flares import <findings.json> --prefix <ID-PREFIX> --source <report-name>
cosmos flares slack --seed-state <legacy .slack-posted.json> --prefix <ID-PREFIX> --status
```

## 4. Consolidate and look
```bash
cosmos ui                          # dreams run by themselves; force one with: cosmos dream
```

## 5. Architecture
```bash
cosmos atlas                       # the inventory (init already ran it)
cosmos atlas --deep                # optional: the model's deep pass now; otherwise the next dream starts it
```

## 6. Agree the Charter, commit on a branch off your base branch
```bash
cosmos charter edit
git checkout -b cosmos/init origin/<base-branch>
git add .claude/settings.json .claude/commands .mcp.json CLAUDE.md AGENTS.md GEMINI.md .gitignore   # never .cosmos: it is the cosmos branch
git commit -m "cosmos: charter, ledger, atlas, findings" && git push -u origin cosmos/init
```

## 7. Sessions that were already open
Nothing to restart in Claude Code: the user-level hooks pick the repository up on the next turn, and the next prompt
carries the briefing the session missed. In Cowork, install the cosmos plugin once (this repository is its marketplace);
the tools appear with the next message. MCP servers added to `.mcp.json` are read when a session starts, so agents that
only use MCP (Codex, Gemini CLI) see the tools in their next session.

## 8. Teammates
```bash
git pull   # then open your agent
```

Transcripts live in `~/.claude/projects/<repo path, slashes → dashes>/` (Claude Code), in each Cowork session's own folder under Claude Desktop's application data (Cowork), `~/.codex/sessions/` (Codex) and `~/.gemini/` (Gemini). They are read, never stored; secrets are redacted. `.claude/settings.local.json` is personal and untouched; `.cosmos/state/` is gitignored.
