"""Playbooks: a team's long-form prompts (a master QA protocol, a release checklist, a review playbook) as commands.

Found by themselves: markdown files whose name says protocol / playbook / runbook / master prompt / operating
instruction, or whose first heading does (under docs/, prompts/, qa/ …), and that are written for an agent (they
mention an agent, a session, cosmos …; a meeting playbook for people is not one), plus every file in .cosmos/playbooks/ (the
committed home for playbooks brought in from another project). Each one becomes a slash command for every agent
(/master-qa-protocol …) that tells the agent to read the file and follow it, so the command never goes stale against
the file. A QA playbook is also what /qa follows.

Sharing: `cosmos playbooks add <path>` copies a playbook from another project into .cosmos/playbooks/;
`cosmos playbooks add qa` starts one from the generic QA protocol below. `playbooks.ignore` in config.json drops a
false positive; `playbooks.paths` adds a file the patterns do not catch.
"""
from __future__ import annotations

import fnmatch
import re
from pathlib import Path
from typing import Dict, List, Optional

from .config import Config

NAME_WORDS = re.compile(r"(protocol|playbook|runbook|master[-_ ]?prompt|operating[-_ ]instruction|master[-_ ]?(qa|test|audit))", re.I)
HEADING_WORDS = re.compile(r"^#\s+.*\b(protocol|playbook|runbook|master prompt|operating instruction)\b", re.I | re.M)
AGENT_WORDS = re.compile(r"\b(agent|claude|codex|gemini|cursor|copilot|session|tool call|subagent|cosmos|you are|your task)\b", re.I)   # written for an agent, not a meeting
QA_WORDS = re.compile(r"\b(qa|quality|test(ing)?|audit|sdet)\b", re.I)
SKIP = {"node_modules", ".git", ".venv", "venv", "dist", "build", ".next", "vendor", "legacy", "site-packages"}
CONTENT_DIRS = ("docs/", "doc/", "prompts/", "playbooks/", ".github/", "qa/")   # a heading match counts only here


def slug(path: str) -> str:
    stem = Path(path).name
    for ext in (".prompt.md", ".md", ".markdown", ".txt"):
        if stem.lower().endswith(ext):
            stem = stem[: -len(ext)]
            break
    return re.sub(r"[^a-z0-9]+", "-", stem.lower()).strip("-")[:48] or "playbook"


def _title(text: str) -> str:
    m = re.search(r"^#\s+(.+)$", text, re.M)
    return re.sub(r"[*_`]", "", m.group(1)).strip()[:120] if m else ""


def _candidates(root: Path) -> List[str]:
    from .atlas import _repo_files
    files = _repo_files(root)
    if files is None:
        files = [str(p.relative_to(root)) for p in root.rglob("*.md")]
    return [f for f in files if f.lower().endswith((".md", ".markdown")) and not any(part in SKIP for part in f.split("/"))
            and not f.startswith((".cosmos/", ".claude/commands/", ".gemini/commands/", ".cursor/", ".windsurf/", ".github/prompts/", "plugin/commands/"))]


def detect(cfg: Config) -> List[Dict[str, str]]:
    """Every playbook in the repository: [{name, path, title, kind}] with kind "qa" or "general", sorted by name."""
    root = cfg.paths.root
    ignore = [str(x) for x in (cfg.get("playbooks.ignore") or [])]
    found: Dict[str, str] = {}
    for rel in _candidates(root):
        if NAME_WORDS.search(Path(rel).name):
            found[rel] = ""
        elif rel.lower().startswith(CONTENT_DIRS):
            try:
                head = (root / rel).read_text(errors="ignore")[:1500]
            except OSError:
                continue
            if HEADING_WORDS.search(head):
                found[rel] = ""
    own = cfg.paths.cosmos / "playbooks"
    for p in sorted(own.glob("*.md")) if own.exists() else []:
        found[str(p.relative_to(root))] = ""
    for extra in cfg.get("playbooks.paths") or []:
        if (root / str(extra)).is_file():
            found[str(extra)] = ""
    out: Dict[str, Dict[str, str]] = {}
    for rel in sorted(found):
        if any(fnmatch.fnmatch(rel, g) or rel == g for g in ignore):
            continue
        try:
            text = (root / rel).read_text(errors="ignore")[:4000]
        except OSError:
            continue
        if not rel.startswith(".cosmos/playbooks/") and rel not in (cfg.get("playbooks.paths") or []) and not AGENT_WORDS.search(text):
            continue
        name = slug(rel)
        if name in out:
            name = slug(str(Path(rel).parent).replace("/", "-") + "-" + name)
        title = _title(text) or Path(rel).stem
        kind = "qa" if QA_WORDS.search(Path(rel).name + " " + title) else "general"
        out[name] = {"name": name, "path": rel, "title": title, "kind": kind}
    return [out[k] for k in sorted(out)]


def qa_playbook(cfg: Config) -> Optional[Dict[str, str]]:
    """The playbook /qa follows: the QA one in .cosmos/playbooks/ first, else the first QA one found."""
    qa = [p for p in detect(cfg) if p["kind"] == "qa"]
    return next((p for p in qa if p["path"].startswith(".cosmos/playbooks/")), qa[0] if qa else None)


def command_body(pb: Dict[str, str]) -> str:
    return (f"Read `{pb['path']}` ({pb['title']}) top to bottom before the first tool call, then follow it: it is the team's "
            f"playbook and it outranks your own habits (the Charter and the owner's rules still outrank it). "
            f"If it keeps a state file, resume from it instead of starting over. Scope or notes from the person: {{ARGS}}")


def add(cfg: Config, source: str, name: Optional[str] = None) -> Path:
    """Copy a playbook into .cosmos/playbooks/ (committed). `qa` is the generic QA protocol shipped with cosmos."""
    dst_dir = cfg.paths.cosmos / "playbooks"
    dst_dir.mkdir(parents=True, exist_ok=True)
    if source in BUILTIN:
        text, base = BUILTIN[source].replace("{PROJECT}", cfg.paths.root.name), f"{source}-protocol"
    else:
        src = Path(source).expanduser()
        if not src.is_file():
            raise SystemExit(f"no such playbook file: {source} (or a built-in: {', '.join(BUILTIN)})")
        text, base = src.read_text(errors="ignore"), slug(src.name)
        text = f"<!-- playbook from {src.resolve()} · adapt the project-specific parts (names, paths, keys, test commands) -->\n" + text
    dst = dst_dir / f"{slug(name or base)}.md"
    if dst.exists():
        raise SystemExit(f"{dst.relative_to(cfg.paths.root)} exists: edit it, or pass --name for a second one")
    dst.write_text(text)
    return dst


BUILTIN: Dict[str, str] = {"qa": """# {PROJECT} — QA playbook (operating instruction for an agent)

Generic starting point shipped with cosmos (`cosmos playbooks add qa`). Replace every **ADAPT** line with this project's
facts, commit it, and `/qa` (every agent) follows it. Optimise for finding what can break the product, not for a
clean-looking report.

## 0. Safety rules (outrank everything below)
| # | Rule |
|---|------|
| S1 | Never use billed or live keys (LLM, cloud, messaging, payments) in tests or scripts. **ADAPT:** name them and where they live (`.env`). |
| S2 | Test with mocks, stubs and unit tests. A live or billed run happens only when the owner approves that exact run. Report any you made. |
| S3 | Never `git push`. Fix on a local branch in a separate worktree; record it with `cosmos flares pr-open <id> --commit <sha> --branch <name>`. Run cosmos CLI with `COSMOS_NO_PUSH=1`. |
| S4 | Never read or print secret values; checking that a key name is set is fine. |
| S5 | Other sessions' uncommitted work is theirs: never stage, stash or revert it. |

## 1. Discovery (every session, before the first change)
1. `git status --short && git log --oneline -5` — what is uncommitted and whose it is.
2. Cosmos: `cosmos_charter` once; `cosmos_recall` before touching files you did not write; `cosmos_lanes`; `cosmos_atlas status`. CLI fallback: `python3 .cosmos/cosmosw <command>`.
3. Test harnesses. **ADAPT:** the exact commands (`pytest -q`, `npm test`, build), and which are safe offline.
4. Audit state: read `docs/qa/STATE.json` if it exists and **continue** from `next`; do not restart.

## 2. The loop
1. Pick the next area from §5 (or the scope you were given). Claim open flares in it first: `cosmos flares claim <id>`.
2. Read the code and its tests; list what can break (inputs, auth, money, data loss, concurrency, limits, migrations).
3. Reproduce before you file: a failing test, a script, or exact steps. No reproduction → severity `note` or `needs-human`.
4. File each problem with `cosmos_flare` (title, severity, `path:line`, what, impact, fix). The id prefix follows the project's lifecycle (`cosmos flares stage`); never set one.
5. Fix only what is safe and small; everything else stays a flare with its fix written down.
6. Update `docs/qa/STATE.json`: `{"done": [...areas], "next": "<area>", "flares": [...ids], "at": "<date>"}`.
7. Record what the team should keep: `cosmos_remember` (a decision, a constraint, a correction), in the area's lane.

## 3. Stop rules
Stop when every area in §5 is done, or when the next step needs the owner (a billed run, an intent question, a push). Leave `cosmos_handoff(learned, open, next)` and the state file current.

## 4. Severity
- **critical** — data loss, security breach, money moved wrongly, the product is down.
- **high** — a core flow is broken for some users, or a cost/abuse risk with no guard.
- **medium** — wrong result with a workaround; missing validation.
- **low** — polish, copy, logs. **note** — a measurement or a verification, no lifecycle.

## 5. Areas
**ADAPT:** one row per area, and the lane each belongs to (`cosmos lanes`). Example: auth · data import · billing · messaging · dashboards · infra/cost · docs.

## 6. Every finding pass asks
Who can call this? What if the input is empty, huge, duplicated, malformed, or someone else's? What happens on retry, on timeout, when a dependency is down? What does it cost when it runs a million times? Is the failure visible to anyone?

## 7. Done when
Every area is done or explicitly deferred with a reason; every flare has a status; the report (`cosmos flares report -o docs/qa/report.md`) is regenerated; the state file says what is next.
"""}
