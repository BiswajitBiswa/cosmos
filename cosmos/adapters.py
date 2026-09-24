"""Session-log adapters: turn any coding agent's transcript into cosmos Turns.

Claude Code (hooks + ~/.claude/projects), Codex CLI / Codex Desktop (~/.codex/sessions rollouts), Gemini CLI /
Antigravity (~/.gemini, best-effort JSON), and a generic role/content reader for anything else. The extractor,
privacy filter and ledger are shared - one memory, many agents.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Optional, Tuple

from .transcript import Turn, iter_turns

INJECTED_USER = re.compile(r"^\s*(# AGENTS\.md instructions|<INSTRUCTIONS>|<permissions instructions>|<environment_context>|<system-reminder>)", re.I)
PATCH_FILE = re.compile(r"^\*\*\* (?:Update|Add|Delete) File: (.+)$", re.M)


def _text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for b in content:
            if isinstance(b, dict):
                if b.get("type") in ("input_text", "output_text", "text") and b.get("text"):
                    parts.append(str(b["text"]))
                elif isinstance(b.get("text"), str):
                    parts.append(b["text"])
            elif isinstance(b, str):
                parts.append(b)
        return "\n".join(parts)
    if isinstance(content, dict):
        return _text(content.get("parts") or content.get("content") or content.get("text") or "")
    return ""


# ---------------------------------------------------------------- Codex
def codex_session_cwd(path: Path) -> str:
    try:
        with path.open() as fh:
            for _ in range(5):
                line = fh.readline()
                if not line:
                    break
                o = json.loads(line)
                if o.get("type") == "session_meta":
                    return str((o.get("payload") or {}).get("cwd", ""))
    except Exception:
        pass
    return ""


def iter_codex_turns(path: Path, offset: int = 0) -> Tuple[List[Turn], int]:
    """Codex rollout .jsonl → Turns. Reads from byte offset; never raises on bad lines."""
    turns: List[Turn] = []
    if not path.exists():
        return turns, offset
    pending_files: List[str] = []
    pending_cmds: List[str] = []
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
            if o.get("type") != "response_item":
                continue
            p = o.get("payload") or {}
            pt = p.get("type")
            ts = o.get("timestamp", "")
            if pt == "function_call" and p.get("name") in ("exec_command", "shell", "container.exec"):
                try:
                    args = json.loads(p.get("arguments") or "{}")
                    cmd = args.get("cmd") or args.get("command") or ""
                    if isinstance(cmd, list):
                        cmd = " ".join(cmd)
                    if cmd:
                        pending_cmds.append(str(cmd)[:200])
                except Exception:
                    pass
            elif pt == "custom_tool_call" and p.get("name") == "apply_patch":
                pending_files += PATCH_FILE.findall(str(p.get("input", "")))
            elif pt == "message":
                role = p.get("role")
                text = _text(p.get("content"))
                if role == "user":
                    if INJECTED_USER.match(text) or not text.strip():
                        continue
                    turns.append(Turn("user", text, [], [], ts, p.get("id", "") or ts))
                elif role == "assistant":
                    t = Turn("assistant", text, list(dict.fromkeys(pending_files)), pending_cmds[:], ts, p.get("id", "") or ts)
                    pending_files, pending_cmds = [], []
                    turns.append(t)
    return turns, offset


def find_codex_sessions(root: Path, home: Optional[Path] = None) -> List[Path]:
    base = (home or Path.home()) / ".codex" / "sessions"
    if not base.exists():
        return []
    rootp = str(root.resolve())
    out = []
    for p in sorted(base.rglob("rollout-*.jsonl")):
        cwd = codex_session_cwd(p)
        if not cwd:
            continue
        try:
            cwd = str(Path(cwd).resolve())
        except Exception:
            pass
        if cwd == rootp or cwd.startswith(rootp + "/"):
            out.append(p)
    return out


# ---------------------------------------------------------------- Gemini CLI / Antigravity (best-effort JSON)
USER_ROLES = {"user", "human"}
MODEL_ROLES = {"model", "gemini", "assistant", "ai"}


def _walk_messages(node: Any, out: List[Tuple[str, str]]) -> None:
    if isinstance(node, dict):
        role = str(node.get("role") or node.get("type") or node.get("author") or "").lower()
        text = _text(node.get("parts") or node.get("content") or node.get("text") or node.get("message") or "")
        if role in USER_ROLES | MODEL_ROLES and text.strip():
            out.append(("user" if role in USER_ROLES else "assistant", text))
            return
        for v in node.values():
            _walk_messages(v, out)
    elif isinstance(node, list):
        for v in node:
            _walk_messages(v, out)


def iter_generic_turns(path: Path) -> List[Turn]:
    """Any JSON / JSONL with role+content pairs (Gemini CLI chats, Antigravity conversations, exports)."""
    turns: List[Turn] = []
    try:
        raw = path.read_text(errors="ignore")
    except Exception:
        return turns
    docs: List[Any] = []
    if path.suffix == ".jsonl":
        for line in raw.splitlines():
            try:
                docs.append(json.loads(line))
            except Exception:
                continue
    else:
        try:
            docs.append(json.loads(raw))
        except Exception:
            return turns
    msgs: List[Tuple[str, str]] = []
    _walk_messages(docs, msgs)
    for i, (role, text) in enumerate(msgs):
        if role == "user" and INJECTED_USER.match(text):
            continue
        turns.append(Turn(role, text, [], [], "", f"{path.stem}-{i}"))
    return turns


def find_gemini_sessions(root: Path, home: Optional[Path] = None) -> List[Path]:
    base = (home or Path.home()) / ".gemini"
    if not base.exists():
        return []
    out = []
    name = root.name
    for pat in ("tmp/*/chats/*.json", "antigravity/conversations/**/*.json", "antigravity/conversations/**/*.jsonl"):
        for p in base.glob(pat):
            try:
                if name in p.read_text(errors="ignore")[:200000]:
                    out.append(p)
            except Exception:
                continue
    return sorted(set(out))


# ---------------------------------------------------------------- registry
AGENTS = {
    "claude": {"label": "Claude Code / Cowork", "instructions": ["CLAUDE.md"], "hooks": True},
    "codex": {"label": "Codex CLI / Codex Desktop", "instructions": ["AGENTS.md"], "hooks": False},
    "gemini": {"label": "Gemini CLI / Antigravity", "instructions": ["GEMINI.md", "AGENTS.md"], "hooks": False},
    "cursor": {"label": "Cursor", "instructions": [".cursor/rules/cosmos.mdc", "AGENTS.md"], "hooks": False},
    "copilot": {"label": "GitHub Copilot", "instructions": [".github/copilot-instructions.md", "AGENTS.md"], "hooks": False},
    "cline": {"label": "Cline / Roo", "instructions": [".clinerules", "AGENTS.md"], "hooks": False},
    "windsurf": {"label": "Windsurf", "instructions": [".windsurfrules", "AGENTS.md"], "hooks": False},
}


def find_claude_sessions(root: Path) -> List[Tuple[Path, str]]:
    """Every Claude Code transcript for this repo: main sessions and their subagents, in every worktree, plus Cowork
    sessions that were given this repo or a folder above it. Returns (path, session_id)."""
    from .transcript import worktrees
    out: List[Tuple[Path, str]] = []
    for base in worktrees(root):
        d = Path.home() / ".claude" / "projects" / str(base).replace("/", "-")
        if not d.exists():
            continue
        out += [(p, p.stem) for p in sorted(d.glob("*.jsonl"))]
        out += [(p, f"{p.parent.parent.name}/{p.stem}") for p in sorted(d.glob("*/subagents/*.jsonl"))]
    return out + find_cowork_sessions(root)


# ---------------------------------------------------------------- Cowork
# Cowork runs Claude Code in a sandbox with its own settings folder per session, so neither user nor repo hooks run
# there and its transcripts are not under ~/.claude. Each session keeps them in
#   <base>/<account>/<org>/local_<id>/.claude/projects/<slug>/<session>.jsonl
# beside a metadata file <base>/<account>/<org>/local_<id>.json that names the folders the person shared and the
# names they are mounted under inside the sandbox (/sessions/<vm>/mnt/<name>/…).
COWORK_BASE = Path.home() / "Library" / "Application Support" / "Claude" / "local-agent-mode-sessions"
_COWORK_META: Dict[str, Tuple[float, Dict[str, Any]]] = {}


def _cowork_meta_file(transcript: Path) -> Optional[Path]:
    parts = transcript.parts
    for i in range(len(parts) - 1):
        if parts[i].startswith("local_") and parts[i + 1] == ".claude":
            return Path(*parts[:i]) / (parts[i] + ".json")
    return None


def _cowork_meta(meta_file: Path) -> Dict[str, Any]:
    try:
        mt = meta_file.stat().st_mtime
        hit = _COWORK_META.get(str(meta_file))
        if hit and hit[0] == mt:
            return hit[1]
        data = json.loads(meta_file.read_text())
        _COWORK_META[str(meta_file)] = (mt, data)
        return data
    except Exception:
        return {}


def cowork_path_map(transcript: Path) -> Dict[str, str]:
    """Sandbox path prefix → the folder on this machine, for one Cowork transcript ({} for anything else)."""
    mf = _cowork_meta_file(transcript)
    m = _cowork_meta(mf) if mf else {}
    vm = m.get("vmProcessName") or m.get("processName")
    if not vm:
        return {}
    return {f"/sessions/{vm}/mnt/{name}": host for host, name in (m.get("folderMountNames") or {}).items()}


def find_cowork_sessions(root: Path) -> List[Tuple[Path, str]]:
    if not COWORK_BASE.exists():
        return []
    r = root.resolve()
    out: List[Tuple[Path, str]] = []
    for mf in COWORK_BASE.glob("*/*/local_*.json"):
        m = _cowork_meta(mf)
        if m.get("isArchived"):
            continue
        folders = [Path(f).resolve() for f in (m.get("userSelectedFolders") or []) if f]
        if not any(r == f or f in r.parents for f in folders):
            continue
        d = mf.with_suffix("") / ".claude" / "projects"
        out += [(p, p.stem) for p in sorted(d.glob("*/*.jsonl"))]
        out += [(p, f"{p.parent.parent.name}/{p.stem}") for p in sorted(d.glob("*/*/subagents/*.jsonl"))]
    return out


def _map_paths(turns: List[Turn], pm: Dict[str, str]) -> None:
    def fix(s: str) -> str:
        for vm_prefix, host in pm.items():
            if vm_prefix in s:
                s = s.replace(vm_prefix, host)
        return s
    for t in turns:
        t.files = [fix(f) for f in t.files]
        t.commands = [fix(c) for c in t.commands]
        t.cwd = fix(t.cwd)


def _scope_to_repo(turns: List[Turn], root: Path) -> List[Turn]:
    """A Cowork session shared a folder above the repo, so it may be about several projects. Keep the exchanges
    (a person's message and the agent's work after it) that touched this repo."""
    roots = {str(root), str(root.resolve())}             # /var/… and /private/var/… are the same folder on macOS
    keep: List[Turn] = []
    block: List[Turn] = []

    def touches(t: Turn) -> bool:
        return any(any(f.startswith(r + "/") for f in t.files) or any(r in c for c in t.commands) or t.cwd.startswith(r) for r in roots)

    def flush():
        if any(touches(t) for t in block):
            keep.extend(block)
    for t in turns:
        if t.role == "user" and block:
            flush()
            block = []
        block.append(t)
    flush()
    return keep


def read_session(path: Path, agent: str, offset: int = 0, until: Optional[int] = None, root: Optional[Path] = None) -> Tuple[List[Turn], int]:
    if agent == "claude":
        turns, off = iter_turns(path, offset, sidechain="subagents" in path.parts, until=until)
        pm = cowork_path_map(path)
        if pm:
            _map_paths(turns, pm)
            if root is not None:
                turns = _scope_to_repo(turns, root)
        return turns, off
    if agent == "codex":
        return iter_codex_turns(path, offset)
    size = path.stat().st_size if path.exists() else 0
    if offset >= size:          # generic logs are re-read whole; the size acts as the "already captured" marker
        return [], size
    return iter_generic_turns(path), size
