"""The model reads the session. Hooks only mark *what* to read; the dream reads it with a model that sees the
conversation in context, instead of regexes guessing from detached sentences.

Two inputs:
  * windows  - byte ranges of agent transcripts (Claude Code, Codex, Gemini) recorded by the hooks or by
               `cosmos capture`, kept machine-local in .cosmos/state. Transcripts are read in place, never copied.
  * auto memory - the notes Claude Code already writes for each developer (~/.claude/projects/<repo>/memory/).
               Offered to the model as candidates for the shared ledger; the model decides what is team knowledge.
Heuristics remain only as a fallback when no model has been available for days.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .config import Config, git_author
from .privacy import redact
from .store import Observations, State, now_iso
from .transcript import Turn, relativize

CATEGORIES = ("architecture", "decision", "convention", "constraint", "bug", "dependency", "workflow", "domain", "rejected")
_TYPE_TO_CATEGORY = {"feedback": "convention", "project": "decision", "reference": "dependency"}
_INTERESTING_CMD = re.compile(r"\b(git (commit|push|merge|rebase|checkout|revert)|pytest|vitest|jest|npm (test|run)|pnpm|yarn|make|docker|kubectl|alembic|terraform|cargo|go (test|build)|mvn|gradle)\b")


# ---------------------------------------------------------------- windows
def register_window(state: State, path: Path, sid: str, agent: str, start: int, end: int, since_days: Optional[int] = None) -> None:
    """Remember that transcript bytes [start, end) of `path` have not been read by the model yet."""
    if end <= start:
        return
    w = {"path": str(path), "sid": sid, "agent": agent, "from": start, "to": end, "ts": now_iso()}
    if since_days:
        w["since"] = (datetime.now(timezone.utc) - timedelta(days=since_days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    wins: List[Dict] = state.data.setdefault("windows", [])
    for x in wins:   # extend a contiguous window for the same transcript instead of adding a new one
        if x["path"] == w["path"] and x["to"] == start:
            x["to"] = end
            x["ts"] = w["ts"]
            return
    wins.append(w)


def windows_waiting(state: State) -> int:
    return len(state.data.get("windows", []))


def _turns_for(w: Dict) -> List[Turn]:
    from .adapters import read_session
    p = Path(w["path"])
    if not p.exists():
        return []
    turns, _ = read_session(p, w.get("agent", "claude"), int(w["from"]), until=int(w["to"]))
    since = w.get("since")
    if since:
        turns = [t for t in turns if not t.timestamp or t.timestamp >= since]
    return turns


def excerpt_chunks(turns: List[Turn], root: Path, max_chars: int = 9000, per_turn: int = 2500) -> List[Tuple[str, List[Turn]]]:
    """Render turns as a compact, redacted transcript excerpt and split it into model-sized chunks.
    Returns [(text, turns_in_chunk)]; the last turn of each chunk carries the byte offset to resume from."""
    chunks: List[Tuple[str, List[Turn]]] = []
    buf: List[str] = []
    members: List[Turn] = []
    size = 0
    for t in turns:
        text = " ".join(t.text.split())
        if len(text) > per_turn:
            text = text[:per_turn] + " …"
        text, _ = redact(text)
        who = "USER" if t.role == "user" else "AGENT"
        line = f"{who}: {text}" if text else ""
        extras = []
        files = [relativize(f, root) for f in (t.files or [])]
        files = [f for f in files if not f.startswith(("/", "external/"))]
        if files:
            extras.append("  edited: " + ", ".join(files[:8]))
        cmds = [c.splitlines()[0][:160] for c in (t.commands or []) if _INTERESTING_CMD.search(c)]
        if cmds:
            extras.append("  ran: " + " | ".join(dict.fromkeys(cmds).keys()))
        block = "\n".join([x for x in [line] + extras if x])
        if not block:
            continue
        if size + len(block) > max_chars and buf:
            chunks.append(("\n".join(buf), members))
            buf, members, size = [], [], 0
        buf.append(block)
        members.append(t)
        size += len(block) + 1
    if buf:
        chunks.append(("\n".join(buf), members))
    return chunks


@dataclass
class ReadReport:
    windows_read: int = 0
    chunks_read: int = 0
    turns_read: int = 0
    new: List[Dict] = field(default_factory=list)
    fallback: int = 0          # windows handled by heuristics because no model was available for too long


def _context(cfg: Config, mems: Dict) -> Dict[str, Any]:
    from .charter import rules as charter_rules
    lanes = sorted({m.lane for m in mems.values() if m.lane and m.lane != "general"})[:40]
    apps: List[str] = []
    aj = cfg.paths.ledger / "atlas" / "atlas.json"
    if aj.exists():
        try:
            apps = [a.get("name") for a in json.loads(aj.read_text()).get("apps", [])][:20]
        except Exception:
            pass
    try:
        rules = [m.text[:160] for m in charter_rules(mems)][:30]
    except Exception:
        rules = []
    known = sorted((m for m in mems.values() if m.status == "active" and m.source != "explicit"), key=lambda m: -m.importance)[:80]
    return {"repo": cfg.paths.root.name, "existing_lanes": lanes, "repo_apps": apps, "team_rules_already_known": rules,
            "already_known": [m.text[:140] for m in known]}


def _items_to_observations(items: List[Dict], turns: List[Turn], w: Dict, cfg: Config, author: str, excerpt: str) -> List[Dict]:
    root = cfg.paths.root
    out: List[Dict] = []
    seen_files = set()
    for t in turns:
        for f in t.files or []:
            r = relativize(f, root)
            if not r.startswith(("/", "external/")):
                seen_files.add(r)
    ts = next((t.timestamp for t in reversed(turns) if t.timestamp), "") or now_iso()
    for it in items[:6]:
        if not isinstance(it, dict):
            continue
        text = " ".join(str(it.get("text", "")).split())
        if not (12 <= len(text) <= 400):
            continue
        text, fired = redact(text)
        if fired:
            continue
        from .lanes import resolve_evidence
        files = []
        for f in it.get("files") or []:
            f = str(f).strip().lstrip("./")
            r = f if f in seen_files else resolve_evidence(root, f)
            if r and r not in files:
                files.append(r)
        cat = it.get("category") if it.get("category") in CATEGORIES else "domain"
        if it.get("kind") == "rejected":
            cat = "rejected"
        lane = re.sub(r"[^a-z0-9/._\-]+", "-", str(it.get("lane") or "").lower()).strip("-")[:40]
        imp = it.get("importance")
        score = min(1.0, max(0.3, float(imp))) if isinstance(imp, (int, float)) else 0.7
        if score < float(cfg.get("dream.read_min_importance", 0.5)) and it.get("kind") != "correction":
            continue
        oid = "obs_" + hashlib.sha1((text + w.get("sid", "") + ts).encode()).hexdigest()[:10]
        rec = {"id": oid, "text": text, "category": cat, "score": score, "source": "observed", "files": files[:6],
               "signals": ["model", str(it.get("kind") or "fact")], "turn_uuid": next((t.uuid for t in turns if t.uuid), ""),
               "ts": ts[:19] + "Z" if len(ts) >= 19 else ts, "author": author, "agent": w.get("agent", "claude"),
               "session": hashlib.sha1(w.get("sid", "").encode()).hexdigest()[:8] if w.get("sid") else "",
               "commit": "", "event": "read", "curated": True, "kind": "fact"}
        if lane:
            rec["lane"] = lane
        if it.get("kind") == "correction":
            rec["score"] = max(rec["score"], 0.85)
            rec["signals"].append("correction")
        out.append(rec)
    return out


def read_windows(cfg: Config, prov, mems: Dict, state: State, store: Observations, budget: int = 30, verbose: bool = False) -> ReadReport:
    """Let the model read every waiting window, oldest first, up to `budget` chunks per dream. Whatever is not
    reached stays queued (a partially read window is re-registered from the first unread turn)."""
    from .providers import READ_SCHEMA, READ_SYSTEM
    from .store import today
    rep = ReadReport()
    wins: List[Dict] = list(state.data.get("windows", []))
    if not wins:
        return rep
    author = git_author(cfg.paths.root) if cfg.get("privacy.author", "git") == "git" else "anonymous"
    ctx = _context(cfg, mems)
    remaining: List[Dict] = []
    used = 0
    for w in sorted(wins, key=lambda x: x.get("ts", "")):
        if used >= budget:
            remaining.append(w)
            continue
        turns = _turns_for(w)
        if not turns:
            continue                                   # transcript gone or nothing readable: drop the window
        chunks = excerpt_chunks(turns, cfg.paths.root)
        done_upto = int(w["from"])
        for text, members in chunks:
            if used >= budget:
                break
            payload = dict(ctx, excerpt=text)
            try:
                res = prov.complete(READ_SYSTEM.format(today=today()), json.dumps(payload, ensure_ascii=False), READ_SCHEMA)
            except Exception as e:
                if verbose:
                    print(f"  read failed on a chunk: {str(e)[:120]}")
                break
            used += 1
            rep.chunks_read += 1
            rep.turns_read += len(members)
            new = _items_to_observations((res or {}).get("items", []), members, w, cfg, author, text)
            if new:
                store.append(new)
                rep.new.extend(new)
            done_upto = max(done_upto, max((t.offset for t in members if t.offset), default=done_upto))
            if verbose:
                print(f"  read {len(members)} turns → {len(new)} facts")
        if done_upto < int(w["to"]) and done_upto > int(w["from"]):
            remaining.append(dict(w, **{"from": done_upto}))
        elif done_upto <= int(w["from"]):
            remaining.append(w)                        # nothing processed (budget hit before this window)
        else:
            rep.windows_read += 1
    state.data["windows"] = remaining
    return rep


def fallback_windows(cfg: Config, state: State, store: Observations, days: int = 3) -> ReadReport:
    """No model for `days`: keep the knowledge anyway with the old heuristics rather than lose it."""
    from .extract import extract
    rep = ReadReport()
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    remaining: List[Dict] = []
    author = git_author(cfg.paths.root) if cfg.get("privacy.author", "git") == "git" else "anonymous"
    for w in state.data.get("windows", []):
        if w.get("ts", "") > cutoff:
            remaining.append(w)
            continue
        turns = _turns_for(w)
        root = cfg.paths.root
        for t in turns:
            t.files = [r for r in (relativize(f, root) for f in t.files) if not r.startswith(("/", "external/"))]
        recs = []
        for o in extract(turns, float(cfg.get("capture.min_score", 0.5)), int(cfg.get("capture.max_per_batch", 40))):
            text, fired = redact(o.text)
            if fired and o.source != "explicit":
                continue
            rec = o.to_dict()
            rec.update({"id": "obs_" + hashlib.sha1((text + w.get("sid", "") + o.turn_uuid).encode()).hexdigest()[:10], "text": text,
                        "ts": now_iso(), "author": author, "agent": w.get("agent", "claude"), "session": hashlib.sha1(w.get("sid", "").encode()).hexdigest()[:8],
                        "commit": "", "event": "fallback"})
            recs.append(rec)
        if recs:
            store.append(recs)
            rep.new.extend(recs)
        rep.fallback += 1
    state.data["windows"] = remaining
    return rep


# ---------------------------------------------------------------- Claude Code auto memory
def auto_memory_dir(cfg: Config) -> Path:
    """Where Claude Code keeps this developer's own notes for this repo (honours `autoMemoryDirectory`)."""
    try:
        s = json.loads((Path.home() / ".claude" / "settings.json").read_text())
        if s.get("autoMemoryDirectory"):
            return Path(str(s["autoMemoryDirectory"])).expanduser()
    except Exception:
        pass
    slug = str(cfg.paths.root.resolve()).replace("/", "-")
    return Path.home() / ".claude" / "projects" / slug / "memory"


def _frontmatter(md: str) -> Tuple[Dict[str, str], str]:
    if not md.startswith("---"):
        return {}, md
    end = md.find("\n---", 3)
    if end < 0:
        return {}, md
    fm: Dict[str, str] = {}
    for line in md[3:end].splitlines():
        if ":" in line and not line.startswith(" "):
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip().strip('"')
    return fm, md[end + 4:].strip()


def auto_memory_candidates(cfg: Config, state: State) -> List[Dict]:
    """New or changed auto memory notes, as candidates for the team ledger. Personal notes (type: user) are skipped.
    Unchanged notes are not offered twice (content hash kept in state)."""
    if not cfg.get("dream.auto_memory", True):
        return []
    d = auto_memory_dir(cfg)
    if not d.exists():
        return []
    seen: Dict[str, str] = state.data.setdefault("auto_memory", {})
    author = git_author(cfg.paths.root) if cfg.get("privacy.author", "git") == "git" else "anonymous"
    out: List[Dict] = []
    for p in sorted(d.glob("*.md")):
        if p.name == "MEMORY.md":
            continue
        try:
            md = p.read_text()
        except Exception:
            continue
        h = hashlib.sha1(md.encode()).hexdigest()[:12]
        if seen.get(p.name) == h:
            continue
        fm, body = _frontmatter(md)
        typ = (fm.get("type") or "").split()[0] if fm.get("type") else ""
        if typ == "user":
            seen[p.name] = h
            continue
        body = " ".join(body.split())[:1500]
        body, fired = redact(body)
        if len(body) < 20 or fired:
            seen[p.name] = h
            continue
        out.append({"id": "obs_" + hashlib.sha1(("am:" + p.name + h).encode()).hexdigest()[:10], "text": body,
                    "category": _TYPE_TO_CATEGORY.get(typ, "domain"), "score": 0.75, "source": "auto-memory", "files": [],
                    "signals": ["auto-memory", typ or "note"], "turn_uuid": "", "ts": now_iso(), "author": author, "agent": "claude",
                    "session": "", "commit": "", "event": "auto-memory", "kind": "auto-memory", "note": p.name})
        seen[p.name] = h
    return out
