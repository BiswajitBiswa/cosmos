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


def iter_turns(path: Path, offset: int = 0) -> Tuple[List[Turn], int]:
    """Parse turns from byte `offset`; return (turns, new_offset). Never raises on bad lines."""
    turns: List[Turn] = []
    if not path.exists():
        return turns, offset
    with path.open("rb") as fh:
        fh.seek(offset)
        while True:
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
            if o.get("isSidechain"):
                continue
            msg = o.get("message") or {}
            content = msg.get("content")
            turn = Turn(role=t, text=_text_of(content), timestamp=o.get("timestamp", ""), uuid=o.get("uuid", ""))
            if isinstance(content, list):
                for b in content:
                    if not isinstance(b, dict) or b.get("type") != "tool_use":
                        continue
                    name = b.get("name", "")
                    inp = b.get("input") or {}
                    if name in EDIT_TOOLS and isinstance(inp, dict) and inp.get("file_path"):
                        turn.files.append(str(inp["file_path"]))
                    elif name == "Bash" and isinstance(inp, dict) and inp.get("command"):
                        turn.commands.append(str(inp["command"])[:200])
            # tool_result-only user messages carry no prose; keep them out
            if turn.role == "user" and isinstance(content, list) and not turn.text.strip():
                continue
            turns.append(turn)
    return turns, offset


def relativize(path: str, root: Path) -> str:
    """Inside the repo → repo-relative. Outside (a sibling repo the session also touched) → ../<sibling>/… so it stays
    readable and never leaks the machine's home directory into the ledger."""
    try:
        p = Path(path).resolve()
        r = root.resolve()
        try:
            return str(p.relative_to(r))
        except ValueError:
            pass
        try:
            return "../" + str(p.relative_to(r.parent))
        except ValueError:
            return "external/" + "/".join(p.parts[-3:])
    except Exception:
        return path
