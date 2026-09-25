"""`cosmos watch`: follow every coding agent on this machine without depending on hooks.

Claude Code (CLI and desktop), Codex and Gemini all write their sessions to disk as they go. The watcher tails
those files for this repository - every worktree, every subagent - captures what is new (journal, explicit rules,
ranges for the model), keeps a live picture of who is doing what right now, and starts a dream when enough is
waiting. Web and cloud sessions have no local transcript: there the committed hooks and MCP tools do the work.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from .config import Config
from .store import State, now_iso

LIVE_MINUTES = 60
HISTORY_BYTES = 2_000_000          # an unseen transcript bigger than this is history, not a session that just began


def _live_path(cfg: Config) -> Path:
    return cfg.paths.state / "live.json"


def load_live(cfg: Config) -> Dict[str, Dict[str, Any]]:
    p = _live_path(cfg)
    try:
        return json.loads(p.read_text()) if p.exists() else {}
    except Exception:
        return {}


def _label(p: Path, agent: str) -> str:
    """What the live view calls the tool: Cowork transcripts are Claude Code transcripts in a different place."""
    from .adapters import cowork_path_map
    return "cowork" if agent == "claude" and cowork_path_map(p) else agent


def _summarise(turns, sid: str, agent: str, prev: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    from .journal import commits_in
    from .transcript import Turn
    import re as _re
    asks = [" ".join(_re.sub(r"\[Image: source: [^\]]*\]", " ", t.text).split())[:200] for t in turns if t.role == "user" and t.text.strip()
            and not t.text.lstrip().startswith(("<", "/", "Stop hook feedback", "[Request interrupted", "Hook "))]
    asks = [a for a in asks if len(a) >= 4]
    files = list(dict.fromkeys(f for t in turns for f in (t.files or [])))
    cmds = [c for t in turns for c in (t.commands or [])]
    last_ts = next((t.timestamp for t in reversed(turns) if t.timestamp), "") or now_iso()
    branch = next((t.branch for t in reversed(turns) if t.branch), "") or (prev or {}).get("branch", "")
    cwd = next((t.cwd for t in reversed(turns) if t.cwd), "") or (prev or {}).get("cwd", "")
    entry = dict(prev or {})
    entry.update({"sid": sid, "agent": agent, "last": last_ts[:19] + "Z" if len(last_ts) >= 19 else last_ts, "branch": branch, "cwd": cwd,
                  "ask": asks[-1] if asks else entry.get("ask", ""), "turns": entry.get("turns", 0) + len(turns)})
    entry["files"] = list(dict.fromkeys((entry.get("files") or []) + files))[-12:]
    entry["commits"] = ((entry.get("commits") or []) + commits_in(cmds))[-8:]
    return entry


def update_live(cfg: Config, turns, sid: str, agent: str) -> None:
    """Called by the hooks and by the watcher after reading new turns: refresh this session's live entry."""
    if not turns:
        return
    try:
        key = f"{agent}:{sid}" if agent != "claude" else sid
        live = load_live(cfg)
        live[key] = _summarise(turns, sid, agent, live.get(key))
        cfg.paths.state.mkdir(parents=True, exist_ok=True)
        _live_path(cfg).write_text(json.dumps(live, indent=1))
    except Exception:
        pass


def _recent_tail(cfg: Config, p: Path, sid: str, agent: str, live: Dict[str, Dict[str, Any]]) -> None:
    """A session that was active in the last hour but has no live entry (its turns were captured by a hook before
    the watcher ran): summarise its tail without capturing anything twice."""
    from .adapters import read_session
    from .transcript import relativize
    key = f"{agent}:{sid}" if agent != "claude" else sid
    try:
        if key in live or time.time() - p.stat().st_mtime > LIVE_MINUTES * 60:
            return
        start = max(0, p.stat().st_size - 300_000)
        turns, _ = read_session(p, agent, start, root=cfg.paths.root)
        turns = turns[-40:]
        if not turns:
            return
        root = cfg.paths.root
        for t in turns:
            t.files = [r for r in (relativize(f, root) for f in t.files) if not r.startswith(("/", "external/"))]
        live[key] = _summarise(turns, sid, _label(p, agent), None)
    except Exception:
        pass


def tick(cfg: Config, agents: Optional[List[str]] = None, verbose: bool = False) -> Dict[str, Any]:
    """One pass: capture what is new from every session of this repo; refresh the live picture; maybe dream."""
    from .adapters import find_claude_sessions, find_codex_sessions, find_gemini_sessions, read_session
    from .hooks import auto_dream, capture, pending_count, should_auto_dream
    from .transcript import relativize
    agents = agents or ["claude", "codex", "gemini"]
    jobs = []
    if "claude" in agents:
        jobs += [(p, "claude", sid) for p, sid in find_claude_sessions(cfg.paths.root)]
    if "codex" in agents:
        jobs += [(p, "codex", p.stem) for p in find_codex_sessions(cfg.paths.root)]
    if "gemini" in agents:
        jobs += [(p, "gemini", p.stem) for p in find_gemini_sessions(cfg.paths.root)]
    state = State(cfg.paths)
    live = load_live(cfg)
    captured = 0
    root = cfg.paths.root
    for p, agent, sid in jobs:
        key = f"{agent}:{sid}" if agent != "claude" else sid
        before = state.offset(key)
        try:
            size = p.stat().st_size
        except OSError:
            continue
        if size <= before:
            _recent_tail(cfg, p, sid, agent, live)
            continue
        if before == 0 and agent == "claude" and size > HISTORY_BYTES:
            # a session first seen with a long history (a Cowork session, a new worktree): treat it like `cosmos init`
            # does - journal for all of it, only the last days queued for the model, then follow it from the end
            from .hooks import backfill_journal
            backfill_journal(cfg, p, sid)
            captured += capture(cfg, {"transcript_path": str(p), "session_id": sid, "hook_event_name": "manual", "cwd": str(root), "since_days": 14})
            state = State(cfg.paths)
            _recent_tail(cfg, p, sid, agent, live)
            continue
        turns, _ = read_session(p, agent, before, root=cfg.paths.root)
        if turns:
            for t in turns:
                t.files = [r for r in (relativize(f, root) for f in t.files) if not r.startswith(("/", "external/"))]
            live[key] = _summarise(turns, sid, _label(p, agent), live.get(key))
        else:
            _recent_tail(cfg, p, sid, agent, live)   # only system lines were appended (hook summaries): still live
        captured += capture(cfg, {"transcript_path": str(p), "session_id": sid, "hook_event_name": "watch", "cwd": str(root)}, agent)
        state = State(cfg.paths)          # capture saved offsets; reload before the next job
    # forget sessions silent for an hour
    cutoff = time.time() - LIVE_MINUTES * 60
    def _ts(s: str) -> float:
        try:
            return time.mktime(time.strptime(s[:19], "%Y-%m-%dT%H:%M:%S")) - time.timezone
        except Exception:
            return 0.0
    live = {k: v for k, v in live.items() if _ts(v.get("last", "")) >= cutoff}
    cfg.paths.state.mkdir(parents=True, exist_ok=True)
    _live_path(cfg).write_text(json.dumps(live, indent=1))
    try:   # the ledger branch stays committed and pushed while people work
        from .sync import is_branch_mode, sync_background
        if time.time() - float(state.data.get("last_sync", 0)) > 600:   # every 10 minutes: commit (and, on the cosmos branch, push)
            sync_background(cfg, "cosmos: journal and observations")
            state.data["last_sync"] = time.time(); state.save()
    except Exception:
        pass
    dreamed = False
    pend = pending_count(cfg)
    if should_auto_dream(cfg, pend) and auto_dream(cfg):
        dreamed = True
    if verbose:
        print(f"{now_iso()} watch: {len(jobs)} sessions · {captured} new observation(s) · {len(live)} live · {pend} waiting" + (" · dream started" if dreamed else ""), flush=True)
    return {"sessions": len(jobs), "captured": captured, "live": live, "pending": pend, "dream_started": dreamed}


def run(cfg: Config, interval: int = 30, once: bool = False, agents: Optional[List[str]] = None, verbose: bool = True,
        daemon: bool = False, idle_minutes: int = 120) -> int:
    """Foreground loop, or (daemon=True) a background watcher that holds state/watch.lock and exits after
    `idle_minutes` without any session activity, so nothing lingers on the machine."""
    import os
    lock = cfg.paths.state / "watch.lock"
    if daemon:
        cfg.paths.state.mkdir(parents=True, exist_ok=True)
        lock.write_text(f"{os.getpid()} {now_iso()}")
    last_activity = time.time()
    from . import code_stamp, restart_process
    stamp = code_stamp()
    try:
        while True:
            if not once and code_stamp() != stamp:
                if verbose:
                    print(f"{now_iso()} watch: cosmos was updated, restarting", flush=True)
                restart_process()                        # same pid, so the lock stays valid
            try:
                res = tick(cfg, agents, verbose)
                if res.get("captured") or res.get("live"):
                    last_activity = time.time()
            except KeyboardInterrupt:
                return 0
            except Exception as e:      # the watcher never dies on one bad file
                if verbose:
                    print(f"{now_iso()} watch: error {str(e)[:160]}", flush=True)
            if once:
                return 0
            if daemon and time.time() - last_activity > idle_minutes * 60:
                if verbose:
                    print(f"{now_iso()} watch: idle for {idle_minutes} min, exiting", flush=True)
                return 0
            try:
                time.sleep(max(5, interval))
            except KeyboardInterrupt:
                return 0
    finally:
        if daemon:
            try:
                lock.unlink()
            except Exception:
                pass
