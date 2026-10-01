# Playbooks: the team's own long-form prompts, as commands

A team writes long prompts it wants every agent to follow the same way: a master QA protocol, a release runbook, an
SEO + GEO playbook. cosmos finds them, and each one becomes a slash command in every agent that reads project commands.
The command does not copy the prompt. It tells the agent to read the file and follow it, so editing the file is all it
takes to change what every agent does.

## What counts as a playbook

- **Found by itself:** a markdown file whose name says *protocol*, *playbook*, *runbook*, *master prompt* or
  *operating instruction*, or whose first heading does when the file is under `docs/`, `doc/`, `prompts/`,
  `playbooks/`, `.github/` or `qa/`. It must be written for an agent: it mentions an agent, a session, cosmos or
  "you are …". A meeting playbook for people is left alone.
- **Kept in `.cosmos/playbooks/`:** every file there counts, with no naming rule. This is the committed home for a
  playbook brought in from another project, or one an agent writes for the team.
- **Named in config:** `playbooks.paths` in `.cosmos/config.json` adds a file the rules miss; `playbooks.ignore` drops
  a false positive.

The command's name is the file's name: `.cosmos/playbooks/seo-geo-master.md` becomes `/seo-geo-master`. A playbook
whose name or title says QA, test or audit is also what `/qa` follows.

## Where it shows up

| agent | how it gets the playbook |
|---|---|
| Claude Code | `.claude/commands/<name>.md`; Claude Code lists project commands with its skills, so `seo-geo-master` appears in a session's skill list |
| Gemini CLI | `.gemini/commands/<name>.toml` |
| Cursor | `.cursor/commands/<name>.md` |
| GitHub Copilot | `.github/prompts/<name>.prompt.md` |
| Windsurf | `.windsurf/workflows/<name>.md` |
| Codex | `.agents/skills/<name>/SKILL.md`, a project skill (Codex reads skills from `.agents/skills/`, not project commands); written by `cosmos connect codex`, and by the repairs in a repository that has `AGENTS.md` |
| any other agent | the block cosmos keeps in `AGENTS.md` and `CLAUDE.md` lists every playbook: name, title and file. Asked for one, the agent reads the file and follows it |

The command files carry "written by cosmos" and are rewritten as playbooks come and go. A command file the team wrote
itself, with the same name, is never overwritten.

## When the command appears

- `cosmos playbooks add <file>` or `cosmos playbooks add qa`: at once. The file is copied into `.cosmos/playbooks/`
  and the commands are written in the same step.
- `cosmos playbooks`: lists what was found and brings the commands up to date.
- A playbook added any other way (an agent writes one, a teammate commits one): with the next dream, which also
  removes the command of a playbook that was deleted.

Commit the playbook and its command files like code; teammates get both on their next `git pull`.

## Sharing one

```bash
cosmos playbooks add ../other-project/docs/qa/MASTER_QA_PROTOCOL.md   # copied into .cosmos/playbooks/ to adapt
cosmos playbooks add qa                                               # the generic QA protocol shipped with cosmos
cosmos playbooks                                                      # what this repository has, and /qa's choice
```

A copied playbook starts with a comment naming where it came from. Adapt its project-specific parts (names, paths,
keys, test commands) before committing it.

`cosmos export` writes the playbooks as one sheet of the Excel workbook (command, file, title, kind).
