"""Slash commands for every agent, from one catalogue.

Claude Code (.claude/commands/*.md), Gemini CLI (.gemini/commands/*.toml), Cursor (.cursor/commands/*.md), GitHub
Copilot in VS Code (.github/prompts/*.prompt.md), Windsurf (.windsurf/workflows/*.md) read project commands; Codex
reads only ~/.codex/prompts (user level, written on request, named cosmos-<name> there because it is shared by every
repository). The plugin ships the same files under plugin/commands for Cowork. Each command asks the agent to use the
cosmos MCP tools and falls back to the committed wrapper, so it works whether the tools are connected or not.

A file cosmos wrote carries MARKER and is rewritten on `cosmos connect`; a file without it is the team's own and is
left alone.
"""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

if TYPE_CHECKING:
    from .config import Config

MARKER = "written by cosmos"
PLAYBOOK_MARKER = MARKER + " for a playbook"
RETIRED = {"intake", "finding", "findings", "audit"}   # renamed to horizon and flares (5b289ba): never a command name again
CLI = "python3 .cosmos/cosmosw"

# name, description, argument hint, body ({ARGS} is what the person typed after the command)
CATALOGUE: List[Tuple[str, str, str, str]] = [
    ("cosmos", "cosmos here: is it working, what is open, what waits for a human", "",
     f"""Report the state of this repository's cosmos in under 15 lines.
1. Run `{CLI} doctor` and `{CLI} status`. Name anything marked ✗ and the one command that fixes it.
2. Open flares: `{CLI} flares list --status open` (count by severity, name the critical/high ones) and the prefix a new flare gets here (`{CLI} flares stage`).
3. Architecture drift: `{CLI} atlas --check`.
4. What waits for a human: `{CLI} review` (contradictions, stale facts) — the count and the top three.
End with the single next step you recommend. {{ARGS}}"""),
    ("recall", "What the team knows about files or a task, before you change them", "<files or task>",
     f"""Before changing anything, find what the team already knows about: {{ARGS}}
Call the `cosmos_recall` tool with the files (paths) and a few words about the task. Without the tools, run `{CLI} search {{ARGS}}` (add `-f <path>` per file).
Answer with the facts, rules and open flares that apply, each with its id and the file it is anchored to, rules first. Say plainly when nothing applies. Do not edit code."""),
    ("remember", "Keep a decision, constraint or rule for the whole team", "<what to remember>",
     f"""Record this for the team: {{ARGS}}
Call `cosmos_remember` with the text and the files it is about. Use kind `rule` only if the person stated it as a rule for the team; otherwise it is a fact (a decision with its reason, a constraint, a correction). Without the tools, run `{CLI} remember "<text>" -c <decision|constraint|convention|architecture> -f <file>`.
Reply with the id it was given, in one line."""),
    ("flare", "File a bug or risk as a flare with a lifecycle", "<what is wrong>",
     f"""File a flare for: {{ARGS}}
Find the code it is about first and cite it as `path:line`. Then call `cosmos_flare` with `title` (one line, what is wrong), `severity` (critical|high|medium|low), `locations` (`path:line · path:line`), `what`, `impact` and `fix`.
Without the tools: `{CLI} flares add "<severity>: <title> @ <path:line>" --what "…" --impact "…" --fix "…"`.
Several bugs at once (a list a person pasted, one per line, or a .csv / .xlsx / .txt path): one `cosmos_flare` per bug, or `{CLI} flares add --from <file>` (`-` reads stdin).
Do not choose a prefix: cosmos names the flare after the project's lifecycle stage (`{CLI} flares stage` shows it). Reply with the flare id."""),
    ("flares", "Open flares: list, show one, move it through its lifecycle", "[id | status | severity]",
     f"""Work with this repository's flares. Request: {{ARGS}}
- No request: `{CLI} flares list --status open`, grouped by severity, with what each one blocks.
- An id: `{CLI} flares show <id>`.
- A status change: `{CLI} flares <claim|pr-open|fix|needs-human|withdraw|wontfix|reopen> <id> "<note>"`. When the work lives in another worktree or branch, add `--commit <sha> --branch <name>`.
- A correction to what was filed: `{CLI} flares edit <id> --title … --severity … --locations …`.
Never change a flare's status without saying why in the note."""),
    ("qa", "Run a QA pass: protocol, open flares, tests, new flares", "[area or resume]",
     f"""Run a QA pass on this repository. Scope: {{ARGS}}
1. Read the Charter (`cosmos_charter`) and the team's QA protocol: `cosmos_recall` with the task "QA protocol" (rules in the qa lane). Follow it over this outline.
2. Resume, do not restart: list flares that are open, claimed or pr_open (`{CLI} flares list`); continue the claimed ones first.
3. Check the scope: read the code, run the tests that cover it, reproduce before you file.
4. File each new problem with `cosmos_flare` (title, severity, `path:line`, what, impact, fix). The prefix follows the lifecycle stage (`{CLI} flares stage`): never set one by hand.
5. For every flare you touched, set its status (`{CLI} flares claim|pr-open|fix <id> "<note>"`, with `--commit/--branch` when the fix lives in another worktree).
6. End with a table: flare id · severity · status · one line — and what you did NOT check."""),
    ("reconcile", "Bring the ledger back in line with the code: stale, moved and contradicting facts", "",
     f"""Reconcile the team memory with the code. {{ARGS}}
1. `{CLI} review` lists contradictions and stale facts.
2. For each stale fact: if its evidence file moved, find the new path (`git log --follow --name-status -- <old path>`) and confirm the fact still holds there; if it holds, `{CLI} verify <id>`; if it no longer holds, `{CLI} forget <id>`.
3. For each contradiction: read both facts and the code; keep the true one with `{CLI} verify <id> --resolve`.
4. Run `{CLI} dream` to consolidate, then `{CLI} health`.
Report counts: verified, forgotten, resolved, left for a human (and why)."""),
    ("lanes", "Feature lanes: facts, open flares and people per lane; overlap", "",
     f"""Show this repository's feature lanes. {{ARGS}}
Call `cosmos_lanes` (without the tools: `{CLI} lanes`). Summarise per lane: facts, open flares, who is active, and every overlap warning. If lanes look fragmented (several names for one area), propose a merged mapping with `{CLI} lanes --propose` and show it; do not write it without the person's yes."""),
    ("horizon", "Map a feature before coding: lanes, collisions, flares in the way", "<feature brief>",
     f"""Map this feature before any code is written: {{ARGS}}
Call `cosmos_horizon` with the brief as `text` and the folders or files it will touch as `files` (without the tools: `{CLI} horizon "<brief>" -f <path>`).
Report: lanes touched, team decisions it collides with, open flares in the way, people active there, and the order you would build it in. Do not write code yet."""),
    ("handoff", "Leave a handoff for whoever continues this branch", "[what is left]",
     f"""Leave a handoff for the next session on this branch. Notes from the person: {{ARGS}}
Call `cosmos_handoff` with `learned` (what this session found out), `open` (what is unfinished or broken) and `next` (the first thing to do). Be concrete: files, commands, flare ids. Without the tools, write the same three parts into your final message; cosmos keeps it."""),
]
# /atlas is the Atlas prompt itself (cosmos/atlas.py COMMAND_MD), kept under its own name
AGENT_DIRS: Dict[str, Tuple[str, str]] = {
    "claude": (".claude/commands", "{name}.md"),
    "gemini": (".gemini/commands", "{name}.toml"),
    "cursor": (".cursor/commands", "{name}.md"),
    "copilot": (".github/prompts", "{name}.prompt.md"),
    "windsurf": (".windsurf/workflows", "{name}.md"),
    "codex": (".agents/skills", "{name}/SKILL.md"),          # Codex's project skills (it reads no project commands)
}
ARGS = {"claude": "$ARGUMENTS", "codex": "$ARGUMENTS", "gemini": "{{args}}"}   # others pass the text after the command as context
PLAIN_ARGS = "(the text the person typed after the command)"


def catalogue(cfg: Optional["Config"] = None) -> List[Tuple[str, str, str, str]]:
    """The fixed commands; with a repository's config, /qa follows its QA playbook and each playbook is a command."""
    from .atlas import COMMAND_MD
    head, body = COMMAND_MD.split("---", 2)[1:]
    desc = next((l.split(":", 1)[1].strip() for l in head.splitlines() if l.startswith("description:")), "Build or refresh the Atlas")
    out = CATALOGUE + [("atlas", desc, "", body.strip())]
    if cfg is None:
        return out
    from .playbooks import command_body, detect, qa_playbook
    qa = qa_playbook(cfg)
    if qa:
        out = [(n, d, h, (f"The team's QA playbook is `{qa['path']}` ({qa['title']}): read it top to bottom first and follow it "
                          f"over the outline below wherever they differ.\n" + b) if n == "qa" else b) for n, d, h, b in out]
    fixed = {n for n, *_ in out}
    return out + [(pb["name"], f"Playbook: {pb['title']}"[:100], "[scope or notes]", command_body(pb)) for pb in detect(cfg) if pb["name"] not in fixed]


def _body(body: str, agent: str) -> str:
    return body.replace("{ARGS}", ARGS.get(agent, PLAIN_ARGS)).rstrip() + "\n"


def render(agent: str, name: str, desc: str, hint: str, body: str, playbook: bool = False) -> str:
    text = _body(body, agent)
    note = f"{PLAYBOOK_MARKER if playbook else MARKER} (`cosmos connect` rewrites it; delete this line to keep your own version)"
    if agent == "gemini":
        return f'# {note}\ndescription = {_toml_str(desc)}\nprompt = """\n{_toml_body(text)}"""\n'
    if agent == "cursor":
        return f"<!-- {note} -->\n# /{name}: {desc}\n\n{text}"
    if agent == "codex-skill":
        return "---\n" + f"name: {name}\ndescription: {_yaml_str(desc)}\n---\n<!-- {note} -->\n{text}"
    front = [f"description: {_yaml_str(desc)}"]
    if hint and agent in ("claude", "codex"):
        front.append(f"argument-hint: {_yaml_str(hint)}")
    return "---\n" + "\n".join(front) + f"\n---\n<!-- {note} -->\n{text}"


def _yaml_str(s: str) -> str:
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _toml_str(s: str) -> str:
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _toml_body(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"""', '\\"\\"\\"')


def _ours(path: Path, new: str) -> bool:
    """A file cosmos may rewrite: missing, marked, or the unmarked /atlas command older versions wrote."""
    if not path.exists():
        return True
    try:
        old = path.read_text()
    except OSError:
        return False
    if MARKER in old:
        return True
    from .atlas import COMMAND_MD
    return path.name == "atlas.md" and old.strip() == COMMAND_MD.strip()


def _write(path: Path, text: str) -> Optional[bool]:
    """True written, False already current, None left alone (the team's own file)."""
    if not _ours(path, text):
        return None
    if path.exists() and path.read_text() == text:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return True


def write_commands(root: Path, agents: List[str], cfg: Optional["Config"] = None) -> Tuple[List[str], List[str]]:
    """Write the catalogue (and, with cfg, the repository's playbooks) for each agent that reads project commands.
    Returns (written or removed, kept as the team's own)."""
    fixed = {n for n, *_ in catalogue()}
    entries = catalogue(cfg)
    written, kept = [], []
    for agent in agents:
        if agent not in AGENT_DIRS:
            continue
        folder, pattern = AGENT_DIRS[agent]
        for name, desc, hint, body in entries:
            p = root / folder / pattern.format(name=name)
            r = _write(p, render("codex-skill" if agent == "codex" else agent, name, desc, hint, body, playbook=name not in fixed))
            if r:
                written.append(str(p.relative_to(root)))
            elif r is None:
                kept.append(str(p.relative_to(root)))
        written += _remove_gone(root / folder, pattern, {n for n, *_ in entries}, root)
    return written, kept


def _remove_gone(folder: Path, pattern: str, current: set, root: Path) -> List[str]:
    suffix = pattern.replace("{name}", "")
    gone = []
    nested = suffix.startswith("/")                    # one folder per command: <name>/SKILL.md
    for p in sorted(folder.glob("*" + suffix)) if folder.exists() else []:
        name = p.parent.name if nested else p.name[: -len(suffix)]
        try:
            if name not in current and MARKER in p.read_text()[:400]:      # a playbook gone, or a command renamed
                p.unlink()
                if nested and not any(p.parent.iterdir()):
                    p.parent.rmdir()
                gone.append(str(p.relative_to(root)))
        except OSError:
            continue
    return gone


def refresh(cfg: "Config", add: Tuple[str, ...] = ()) -> List[str]:
    """Keep playbook commands in step with the files, for the agents this repository already has commands for
    (and `add`: agents a repair brings in)."""
    agents = [a for a, (folder, pattern) in AGENT_DIRS.items() if a in add or (cfg.paths.root / folder / pattern.format(name="recall")).exists()]
    return write_commands(cfg.paths.root, agents, cfg)[0] if agents else []


def write_codex_prompts(home: Optional[Path] = None) -> List[Path]:
    """Codex reads custom prompts only from ~/.codex/prompts, shared by every repository: /prompts:cosmos-<name>."""
    base = (home or Path.home()) / ".codex" / "prompts"
    out = []
    for name, desc, hint, body in catalogue():
        p = base / f"cosmos-{name}.md"
        if _write(p, render("codex", name, desc, hint, body)):
            out.append(p)
    return out


def write_plugin_commands(plugin_dir: Path) -> List[str]:
    """The plugin's copy (Cowork, and Claude Code with the plugin): /cosmos:<name>."""
    entries = catalogue()
    done = [n for n, d, h, b in entries if _write(plugin_dir / "commands" / f"{n}.md", render("claude", n, d, h, b))]
    return done + _remove_gone(plugin_dir / "commands", "{name}.md", {n for n, *_ in entries}, plugin_dir)


def status(root: Path) -> str:
    """Which agents have the commands in this repository, in one line."""
    names = [n for n, *_ in catalogue()]
    have = []
    for agent, (folder, pattern) in AGENT_DIRS.items():
        n = sum((root / folder / pattern.format(name=x)).exists() for x in names)
        if n:
            have.append(f"{agent} {n}/{len(names)}")
    codex = sum((Path.home() / ".codex" / "prompts" / f"cosmos-{x}.md").exists() for x in names)
    if codex:
        have.append(f"codex {codex}/{len(names)} (user level)")
    return (" · ".join(have) if have else "none written yet") + " — `cosmos connect` writes them"
