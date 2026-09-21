"""Journal: one entry per agent turn - what was asked, which files changed, which commits landed.

Facts are what the team learned; the journal is what the team did. Heuristic fact extraction can find nothing
in a two-hour coding session that shipped five commits - the journal makes sure that work is still recorded,
per lane and per person, and the model can still turn commit messages into facts at dream time.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

from .transcript import Turn

_COMMIT_MSG = re.compile(
    r"""git\s+commit\b[^\n]*?(?:"""
    r"""-F\s+-\s*<<-?\s*['"]?(\w+)['"]?\s*\n([^\n]+)"""          # git commit -F - <<'MSG' ⏎ first line
    r"""|(?:-m|--message)[=\s]+"?\$\(cat\s+<<-?\s*['"]?\w+['"]?\s*\n([^\n]+)"""   # -m "$(cat <<'EOF' ⏎ first line
    r"""|(?:-[a-zA-Z]*m|--message)[=\s]+(?:"((?:[^"\\]|\\.)*)"|'([^']*)'|([^\n]+))"""      # -m "…" · -am '…' · --message=… · unterminated
    r""")""", re.S)
_TEST_CMD = re.compile(r"\b(pytest|vitest|jest|mocha|go test|cargo test|mvn test|gradle(w)? test|npm test|pnpm test|yarn test|rspec|phpunit|dotnet test|unittest|tox)\b")
_PUSH = re.compile(r"\bgit\s+push\b")
_PR = re.compile(r"\bgh\s+pr\s+create\b")


def commits_in(commands: List[str]) -> List[str]:
    """Commit messages (first line) from the shell commands a turn ran."""
    out: List[str] = []
    for c in commands:
        for m in _COMMIT_MSG.finditer(c):
            groups = [g for g in m.groups() if g]
            if m.group(1):                      # -F - heredoc: group 1 is the delimiter, group 2 the first line
                groups = [m.group(2)] if m.group(2) else []
            msg = (groups[0] if groups else "").strip().splitlines()
            first = msg[0].strip() if msg else ""
            first = re.split(r"\s+(?:&&|\|\||;)\s+", first)[0].strip().strip("\"'").strip()   # unterminated quote: stop at the next shell operator
            if first and first not in out:
                out.append(first[:120])
    return out


def git_branch(root: Path) -> str:
    try:
        out = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=root, capture_output=True, text=True, timeout=3)
        return out.stdout.strip()
    except Exception:
        return ""


def _ask(turns: List[Turn]) -> str:
    for t in turns:
        if t.role == "user":
            text = " ".join(t.text.split())
            if len(text) >= 4 and not text.startswith(("/", "<")):
                return text[:240]
    return ""


def build(turns: List[Turn], root: Path) -> Optional[Dict]:
    """One journal record for a batch of turns (normally: one agent turn, from the last Stop to this one).
    Returns None when nothing worth writing down happened (no ask, no files, no commits)."""
    if not turns:
        return None
    ask = _ask(turns)
    files: List[str] = []
    commands: List[str] = []
    for t in turns:
        for f in t.files:
            if f not in files:
                files.append(f)
        commands.extend(t.commands)
    commits = commits_in(commands)
    tests = any(_TEST_CMD.search(c) for c in commands)
    pushes = sum(1 for c in commands if _PUSH.search(c))
    prs = sum(1 for c in commands if _PR.search(c))
    if not (ask or files or commits):
        return None
    parts = []
    if ask:
        parts.append(f'asked: "{ask}"')
    if files:
        parts.append(f"edited {len(files)} file{'s' if len(files) != 1 else ''}")
    if commits:
        parts.append(f"{len(commits)} commit{'s' if len(commits) != 1 else ''}: " + " · ".join(f'"{c}"' for c in commits[:4]) + (" …" if len(commits) > 4 else ""))
    if tests:
        parts.append("tests ran")
    if pushes:
        parts.append("pushed")
    if prs:
        parts.append("PR opened")
    return {"kind": "journal", "category": "workflow", "source": "journal", "score": 1.0,
            "text": " · ".join(parts), "ask": ask, "files": files, "commits": commits, "tests": tests,
            "pushes": pushes, "prs": prs, "turns": len(turns),
            "branch": next((t.branch for t in reversed(turns) if t.branch), "") or git_branch(root),
            "turn_uuid": next((t.uuid for t in turns if t.uuid), ""), "signals": ["journal"]}


def _local_hhmm(ts: str) -> str:
    """UTC ISO timestamp → local HH:MM (the journal is read by people, in their own day)."""
    try:
        from datetime import datetime, timezone
        return datetime.strptime(ts[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc).astimezone().strftime("%H:%M")
    except Exception:
        return ts[11:16]


def persist(cfg, entries: List[Dict], mems: Optional[Dict] = None) -> int:
    """Append journal records to ledger/journal/<date>.md (one file per day, committed, Obsidian-readable).
    Idempotent: an entry already present (by observation id) is not written twice. Returns entries written."""
    from .lanes import infer_lane
    if not entries:
        return 0
    d = cfg.paths.ledger / "journal"
    d.mkdir(parents=True, exist_ok=True)
    lane_globs = cfg.get("lanes", {}) or None
    written = 0
    by_day: Dict[str, List[Dict]] = {}
    for e in entries:
        by_day.setdefault((e.get("ts") or "")[:10] or "undated", []).append(e)
    for day, items in sorted(by_day.items()):
        p = d / f"{day}.md"
        existing = p.read_text() if p.exists() else ""
        if not existing:
            existing = f"---\nkind: journal\ndate: \"{day}\"\n---\n\n# Journal · {day}\n\nWhat the team did, one line per agent turn. Facts live in the ledger; this is the work.\n\n"
        lines = []
        for e in sorted(items, key=lambda x: x.get("ts", "")):
            oid = e.get("id", "")
            if oid and f"<!-- {oid} -->" in existing:
                continue
            lane = infer_lane(e.get("files") or [], lane_globs) if e.get("files") else "general"
            when = _local_hhmm(e.get("ts") or "")
            who = e.get("author") or "someone"
            branch = f" · `{e['branch']}`" if e.get("branch") else ""
            files = e.get("files") or []
            ftxt = (" · " + ", ".join(f"`{f}`" for f in files[:3]) + (f" +{len(files)-3}" if len(files) > 3 else "")) if files else ""
            lines.append(f"- **{when}** {who} · *{lane}*{branch} — {e.get('text','')}{ftxt} <!-- {oid} -->")
            written += 1
        if lines:
            p.write_text(existing.rstrip("\n") + "\n" + "\n".join(lines) + "\n")
    return written


def read_recent(cfg, days: int = 14) -> List[str]:
    """The last N daily journal files, newest first (markdown bodies)."""
    d = cfg.paths.ledger / "journal"
    if not d.exists():
        return []
    files = sorted(d.glob("*.md"), reverse=True)[:days]
    return [p.read_text() for p in files]
