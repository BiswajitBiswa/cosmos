"""Read Claude Code session transcripts (.jsonl) incrementally."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator, List, Optional, Tuple

EDIT_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}


@dataclass
class Turn:
    role: str                       # user | assistant
    text: str                       # concatenated text blocks
    files: List[str] = field(default_factory=list)   # files touched via edit tools
    commands: List[str] = field(default_factory=list)
    timestamp: str = ""
    uuid: str = ""
    branch: str = ""              # git branch the agent was on (Claude Code records it per entry)
    cwd: str = ""                 # working directory recorded on the entry
    edit_chars: int = 0             # size of the edits in this entry (old + new text), a proxy for change size
    offset: int = 0                 # byte offset just after this entry in the transcript file


_INJECTED = re.compile(r"<(system-reminder|local-command-caveat|command-name|command-message|command-args|local-command-stdout|task-notification|ci-monitor-event)[^>]*>.*?</\1>", re.S)
_TAGS = re.compile(r"</?[a-z][a-z0-9_\-]*[^>]*>")


def _strip_injected(text: str) -> str:
    """Drop harness-injected blocks (system reminders, slash-command echoes) - they are not the developer talking."""
    text = _INJECTED.sub(" ", text)
    return _TAGS.sub(" ", text) if "<" in text else text


def _text_of(content) -> str:
    if isinstance(content, str):
        return _strip_injected(content)
    if isinstance(content, list):
        parts = []
        for b in content:
            if isinstance(b, dict) and b.get("type") == "text":
                parts.append(_strip_injected(b.get("text", "")))
        return "\n".join(parts)
    return ""


def iter_turns(path: Path, offset: int = 0, sidechain: bool = False, until: Optional[int] = None) -> Tuple[List[Turn], int]:
    """Parse turns from byte `offset`; return (turns, new_offset). Never raises on bad lines.
    `sidechain=True` reads a subagent transcript (<session>/subagents/*.jsonl), whose entries are all side-chain."""
    turns: List[Turn] = []
    if not path.exists():
        return turns, offset
    with path.open("rb") as fh:
        fh.seek(offset)
        while True:
            if until is not None and fh.tell() >= until:
                break
            line = fh.readline()
            if not line:
                break
            offset = fh.tell()
            try:
                o = json.loads(line)
            except Exception:
                continue
            t = o.get("type")
            if t not in ("user", "assistant"):
                continue
            if o.get("isSidechain") and not sidechain:
                continue
            msg = o.get("message") or {}
            content = msg.get("content")
            turn = Turn(role=t, text=_text_of(content), timestamp=o.get("timestamp", ""), uuid=o.get("uuid", ""), branch=str(o.get("gitBranch") or ""), cwd=str(o.get("cwd") or ""))
            if isinstance(content, list):
                for b in content:
                    if not isinstance(b, dict) or b.get("type") != "tool_use":
                        continue
                    name = b.get("name", "")
                    inp = b.get("input") or {}
                    if name in EDIT_TOOLS and isinstance(inp, dict) and (inp.get("file_path") or inp.get("notebook_path")):
                        turn.files.append(str(inp.get("file_path") or inp.get("notebook_path")))
                        if name == "Write":
                            turn.edit_chars += len(str(inp.get("content", "")))
                        elif name == "MultiEdit":
                            turn.edit_chars += sum(len(str(e.get("old_string", ""))) + len(str(e.get("new_string", ""))) for e in (inp.get("edits") or []) if isinstance(e, dict))
                        else:
                            turn.edit_chars += len(str(inp.get("old_string", ""))) + len(str(inp.get("new_string", "")))
                    elif name == "Bash" and isinstance(inp, dict) and inp.get("command"):
                        turn.commands.append(str(inp["command"])[:4000])
            # tool_result-only user messages carry no prose; keep them out
            if turn.role == "user" and isinstance(content, list) and not turn.text.strip():
                continue
            turn.offset = offset
            turns.append(turn)
    return turns, offset


_WORKTREES: dict = {}


def worktrees(root: Path) -> List[Path]:
    """Every checkout of this repository (git worktrees), main one first. Cached per process."""
    key = str(root)
    if key in _WORKTREES:
        return _WORKTREES[key]
    out: List[Path] = [root.resolve()]
    try:
        import subprocess
        res = subprocess.run(["git", "worktree", "list", "--porcelain"], cwd=root, capture_output=True, text=True, timeout=3)
        for line in res.stdout.splitlines():
            if line.startswith("worktree "):
                p = Path(line[9:].strip()).resolve()
                if p not in out:
                    out.append(p)
    except Exception:
        pass
    _WORKTREES[key] = out
    return out


def relativize(path: str, root: Path) -> str:
    """Inside the repo (any of its worktrees) → repo-relative. Outside (a sibling repo the session also touched) →
    ../<sibling>/… so it stays readable and never leaks the machine's home directory into the ledger."""
    try:
        p = Path(path).resolve()
        r = root.resolve()
        for base in worktrees(root):
            try:
                return str(p.relative_to(base))
            except ValueError:
                continue
        try:
            return "../" + str(p.relative_to(r.parent))
        except ValueError:
            return "external/" + "/".join(p.parts[-3:])
    except Exception:
        return path
