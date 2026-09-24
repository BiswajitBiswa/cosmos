"""Where a branch was left: the last thing said on it, and what is open.

Two sources, one file per branch under ledger/journal/handoffs/ (on the cosmos branch, so teammates get it):
  * automatic - the agent's final message of a turn that edited code. It is already the summary; nobody writes a second one.
  * explicit  - cosmos_handoff(learned, open, next) when the agent stops mid-work.
The next session on that branch, on any machine, opens with it.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from .config import Config, git_author
from .privacy import redact
from .store import now_iso


def _dir(cfg: Config) -> Path:
    return cfg.paths.ledger / "journal" / "handoffs"


def _slug(branch: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]+", "-", branch).strip("-")[:80] or "detached"


def current_branch(cfg: Config, cwd: Optional[str] = None) -> str:
    import subprocess
    try:
        out = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=cwd or cfg.paths.root, capture_output=True, text=True, timeout=3)
        return out.stdout.strip()
    except Exception:
        return ""


def _write(cfg: Config, branch: str, body: str, kind: str, author: str) -> Path:
    d = _dir(cfg)
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"{_slug(branch)}.md"
    p.write_text(f"---\ntype: Handoff\nkind: handoff\nbranch: \"{branch}\"\nby: \"{author}\"\nat: \"{now_iso()}\"\nhow: {kind}\n---\n\n{body.strip()}\n")
    return p


def record_auto(cfg: Config, last_message: str, event: Dict[str, Any]) -> Optional[Path]:
    """The final assistant message of a turn, kept as the branch's handoff unless an explicit one is newer."""
    text = " ".join(redact(last_message)[0].split())
    if len(text) < 60:
        return None
    text = text[:700] + (" …" if len(text) > 700 else "")
    branch = current_branch(cfg, event.get("cwd"))
    if not branch or branch == "HEAD":
        return None
    p = _dir(cfg) / f"{_slug(branch)}.md"
    if p.exists():
        fm = _frontmatter(p.read_text())
        if fm.get("how") == "explicit":
            try:  # an explicit handoff stands for six hours; after that the newest message wins again
                at = datetime.strptime(fm.get("at", "")[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
                if (datetime.now(timezone.utc) - at).total_seconds() < 6 * 3600:
                    return None
            except Exception:
                pass
    author = git_author(cfg.paths.root) if cfg.get("privacy.author", "git") == "git" else "anonymous"
    return _write(cfg, branch, text, "auto", author)


def record_explicit(cfg: Config, learned: str, open_: str, next_: str, branch: str = "") -> Path:
    parts = []
    if learned.strip():
        parts.append(f"**Learned:** {' '.join(learned.split())}")
    if open_.strip():
        parts.append(f"**Open:** {' '.join(open_.split())}")
    if next_.strip():
        parts.append(f"**Next:** {' '.join(next_.split())}")
    body = redact("\n".join(parts))[0]
    author = git_author(cfg.paths.root) if cfg.get("privacy.author", "git") == "git" else "anonymous"
    return _write(cfg, branch or current_branch(cfg) or "detached", body, "explicit", author)


def _frontmatter(md: str) -> Dict[str, str]:
    if not md.startswith("---"):
        return {}
    end = md.find("\n---", 3)
    fm: Dict[str, str] = {}
    for line in md[3:end].splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip().strip('"')
    return fm


def latest(cfg: Config, branch: str = "", max_age_days: int = 14) -> str:
    """The handoff for this branch as one paragraph for the agent, or '' when there is none worth showing."""
    branch = branch or current_branch(cfg)
    if not branch:
        return ""
    p = _dir(cfg) / f"{_slug(branch)}.md"
    if not p.exists():
        return ""
    md = p.read_text()
    fm = _frontmatter(md)
    body = md[md.find("\n---", 3) + 4:].strip()
    try:
        at = datetime.strptime(fm.get("at", "")[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
        age = datetime.now(timezone.utc) - at
        if age.days > max_age_days:
            return ""
        when = f"{age.days}d ago" if age.days else (f"{age.seconds // 3600}h ago" if age.seconds >= 3600 else f"{max(1, age.seconds // 60)}m ago")
    except Exception:
        when = fm.get("at", "")[:10]
    who = fm.get("by", "someone")
    kind = "handoff" if fm.get("how") == "explicit" else "last turn"
    return f"cosm◎s · WHERE `{branch}` WAS LEFT ({kind} by {who}, {when}):\n{body}"
