# Link an existing codebase and its past sessions

cosmos is usually added to a project that already has months of history: AI sessions on several machines, an audit document, branches nobody has drawn. These steps bring all of it into one `.cosmos/` folder. Works the same for Claude Code, Codex, Cursor, Gemini CLI, Copilot, Cline or Cowork.

## 1. Initialise in the repository
```bash
cd <your-repo> && cosmos init && cosmos connect all
```

## 2. Link past sessions
```bash
cosmos capture --agent claude --transcript <path-to-session>.jsonl -v   # one session
cosmos capture --agent codex  --transcript <path-to-rollout>.jsonl -v   # a Codex session
cosmos capture --agent all -v                    # every session, subagents included
cosmos capture --agent claude --rebuild-journal  # work log from before cosmos: asks, files, commits, per day
```

## 3. Bring in an existing audit
```bash
cosmos flares import <findings.json> --prefix <ID-PREFIX> --source <report-name>
cosmos flares slack --seed-state <legacy .slack-posted.json> --prefix <ID-PREFIX> --status
```

## 4. Consolidate and look
```bash
cosmos dream && cosmos review && cosmos lanes && cosmos ui
```

## 5. Architecture
```bash
cosmos atlas                       # deterministic pass
# deep pass: /atlas in Claude Code, or paste .claude/commands/atlas.md into any agent
```

## 6. Agree the Charter, commit on a branch off your base branch
```bash
cosmos charter edit
git checkout -b cosmos/init origin/<base-branch>
git add .cosmos .claude/settings.json .claude/commands .mcp.json CLAUDE.md AGENTS.md GEMINI.md .gitignore
git commit -m "cosmos: charter, ledger, atlas, findings" && git push -u origin cosmos/init
```

## 7. Restart sessions that were already open
```bash
# hooks and MCP servers are read when a session starts — restart or resume the session in your agent
```

## 8. Teammates
```bash
git pull   # then open your agent
```

Transcripts live in `~/.claude/projects/<repo path, slashes → dashes>/` (Claude Code), `~/.codex/sessions/` (Codex), `~/.gemini/` (Gemini). They are read, never stored; secrets are redacted. `.claude/settings.local.json` is personal and untouched; `.cosmos/state/` is gitignored.
