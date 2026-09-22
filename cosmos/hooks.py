"""Claude Code hook handler. Reads the event JSON on stdin, never blocks, never fails the developer."""
from __future__ import annotations

import hashlib
import json
import sys
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional

from .config import Config, git_author, git_head, load_config
from .extract import extract
from .privacy import path_ignored, redact
from .retrieve import format_for_agent, retrieve, top
from .store import Ledger, Observations, State, now_iso
from .transcript import iter_turns, relativize
from . import journal as _journal
from . import reader as _reader


def _log(cfg: Config, msg: str) -> None:
    try:
        cfg.paths.state.mkdir(parents=True, exist_ok=True)
        with cfg.paths.log.open("a") as fh:
            fh.write(f"{now_iso()} {msg}\n")
    except Exception:
        pass


def _log_inject(cfg: Config, event: str, text: str) -> None:
    """Context handed to an agent, measured: what cosmos costs a session in tokens is a number, not a feeling."""
    try:
        cfg.paths.state.mkdir(parents=True, exist_ok=True)
        with (cfg.paths.state / "inject.log").open("a") as fh:
            fh.write(f"{now_iso()} {event} {max(1, len(text) // 4)} {text.count(chr(10) + '- ')}\n")
    except Exception:
        pass


def _session_tag(session_id: str) -> str:
    return hashlib.sha1(session_id.encode()).hexdigest()[:8] if session_id else ""


def capture(cfg: Config, event: Dict[str, Any], agent: str = "claude") -> int:
    """Incrementally extract observations from a session transcript (Claude Code by default; see adapters.py)."""
    if not cfg.get("capture.enabled", True):
        return 0
    tp = event.get("transcript_path")
    sid = event.get("session_id", "")
    if not tp or not Path(tp).exists():
        return 0
    state = State(cfg.paths)
    from .adapters import read_session
    turns, new_off = read_session(Path(tp), agent, state.offset(f"{agent}:{sid}" if agent != "claude" else sid))
    if not turns:
        return 0
    root = cfg.paths.root
    for t in turns:
        t.files = [r for r in (relativize(f, root) for f in t.files) if not r.startswith(("/", "external/"))]
    from .watch import update_live
    update_live(cfg, turns, sid, agent)
    model_reads = capture_mode(cfg) == "model"
    if model_reads:
        # the model reads this range at dream time; here we keep only what must not wait: explicit rules and findings.
        # A live Claude Code turn that edited code is recorded by the agent itself at the Gate (it has the full context);
        # such ranges are not queued for a second reading.
        from .charter import gate_config
        gc = gate_config(cfg)
        reflected = (agent == "claude" and event.get("hook_event_name") in ("Stop", "SessionEnd") and gc.get("reflect", True)
                     and gc.get("enabled", True) and any(_code_file(f, gc) for t in turns for f in t.files))
        if not reflected:
            _reader.register_window(state, Path(tp), sid, agent, state.offset(f"{agent}:{sid}" if agent != "claude" else sid), new_off, event.get("since_days"))
        obs = [o for o in extract(turns, float(cfg.get("capture.min_score", 0.5)), 10_000) if o.source == "explicit"]
    else:
        obs = extract(turns, float(cfg.get("capture.min_score", 0.5)), int(cfg.get("capture.max_per_batch", 40)))
    author = git_author(root) if cfg.get("privacy.author", "git") == "git" else "anonymous"
    records: List[Dict[str, Any]] = []
    globs = cfg.ignore_globs
    for o in obs:
        files = [f for f in o.files if not path_ignored(f, globs)]
        if o.files and not files:          # every evidence file is in an ignored area
            continue
        text, fired = redact(o.text) if cfg.get("privacy.redact_secrets", True) else (o.text, [])
        if "[REDACTED" in text and o.source != "explicit":
            continue                       # a fact that needed redaction is not a fact worth keeping
        rec = o.to_dict()
        rec.update({"id": "obs_" + hashlib.sha1((text + sid + o.turn_uuid).encode()).hexdigest()[:10],
                    "text": text, "files": files, "ts": now_iso(), "author": author, "agent": agent,
                    "session": _session_tag(sid), "commit": git_head(root), "event": event.get("hook_event_name", "")})
        records.append(rec)
    if cfg.get("capture.journal", True):
        j = _journal.build(turns, root)
        if j:
            j["files"] = [f for f in j["files"] if not path_ignored(f, globs)]
            text, _ = redact(j["text"])
            j.update({"id": "obs_" + hashlib.sha1((text + sid + j["turn_uuid"] + (turns[0].timestamp or "")).encode()).hexdigest()[:10],
                      "text": text, "ts": now_iso(), "author": author, "agent": agent, "session": _session_tag(sid),
                      "commit": git_head(root), "event": event.get("hook_event_name", "")})
            records.append(j)
    if records:
        Observations(cfg.paths).append(records)
    state.set_offset(f"{agent}:{sid}" if agent != "claude" else sid, new_off)
    state.save()
    return len(records)


def backfill_journal(cfg: Config, path: Path, sid: str, agent: str = "claude") -> int:
    """Re-read a whole transcript and write one journal record per agent turn (a window from one user message to the
    next). Facts are not re-extracted. Idempotent: records carry deterministic ids and existing ones are skipped."""
    from .adapters import read_session
    turns, _ = read_session(path, agent, 0)
    if not turns:
        return 0
    root = cfg.paths.root
    for t in turns:
        t.files = [r for r in (relativize(f, root) for f in t.files) if not r.startswith(("/", "external/"))]
    windows: List[List] = []
    for t in turns:
        if t.role == "user" or not windows:
            windows.append([t])
        else:
            windows[-1].append(t)
    store = Observations(cfg.paths)
    have = {o.get("id") for o in store.iter_all()}
    author = git_author(root) if cfg.get("privacy.author", "git") == "git" else "anonymous"
    globs = cfg.ignore_globs
    records: List[Dict[str, Any]] = []
    for w in windows:
        j = _journal.build(w, root)
        if not j or not (j["commits"] or j["files"]):
            continue                      # backfill keeps work, not every question ever asked
        j["files"] = [f for f in j["files"] if not path_ignored(f, globs)]
        text, _ = redact(j["text"])
        ts = next((t.timestamp for t in reversed(w) if t.timestamp), "") or now_iso()
        oid = "obs_" + hashlib.sha1((text + sid + j["turn_uuid"] + (w[0].timestamp or "")).encode()).hexdigest()[:10]
        if oid in have:
            continue
        have.add(oid)
        j.update({"id": oid, "text": text, "ts": ts[:19] + "Z" if len(ts) >= 19 else ts, "author": author, "agent": agent,
                  "session": _session_tag(sid), "commit": "", "event": "backfill"})
        records.append(j)
    if records:
        store.append(records)
    return len(records)


def _code_file(rel: str, gc: Dict[str, Any]) -> bool:
    from .gate import _matches
    return not _matches(rel, gc.get("skip_globs", [])) and _matches(rel, gc.get("code_globs", ["**/*"]))


def capture_mode(cfg: Config) -> str:
    """model: hooks mark transcript ranges and the model reads them at dream time (default whenever a provider is
    configured). heuristic: the old regex extraction inside the hook."""
    mode = str(cfg.get("capture.mode", "auto"))
    if mode in ("model", "heuristic"):
        return mode
    import os
    if os.environ.get("COSMOS_LLM_PROVIDER") == "none" or (cfg.get("llm.provider") == "none"):
        return "heuristic"
    if os.environ.get("ANTHROPIC_API_KEY") or (cfg.get("llm.provider") or "auto") not in ("auto", "claude-code"):
        return "model"
    import shutil
    return "model" if shutil.which("claude") else "heuristic"


def pending_count(cfg: Config) -> int:
    state = State(cfg.paths)
    return sum(1 for o in Observations(cfg.paths).iter_all() if o.get("id") and not state.is_dreamed(o["id"])) + _reader.windows_waiting(state)


def should_auto_dream(cfg: Config, pending: int, now: Optional[float] = None) -> bool:
    """Dream by itself when enough is waiting, or when something is waiting and the last dream is old."""
    import time
    if not cfg.get("dream.auto", True) or pending <= 0:
        return False
    if pending >= int(cfg.get("dream.auto_after", 25)):
        return True
    d = cfg.paths.state / "dreams"
    last = max((p.stat().st_mtime for p in d.glob("*.json")), default=0.0) if d.exists() else 0.0
    age = (now or time.time()) - last
    if _reader.windows_waiting(State(cfg.paths)) and age >= float(cfg.get("dream.backlog_hours", 1)) * 3600:
        return True      # the model still has session ranges to read: keep draining, one run an hour
    return age >= float(cfg.get("dream.auto_hours", 6)) * 3600


def auto_dream(cfg: Config) -> bool:
    """Start `cosmos dream --auto` detached so the hook returns in milliseconds. One at a time (lock file)."""
    import os, subprocess, time
    if os.environ.get("COSMOS_NO_BACKGROUND"):
        return False
    lock = cfg.paths.state / "dream.lock"
    try:
        if lock.exists() and time.time() - lock.stat().st_mtime < 1800:
            return False
        cfg.paths.state.mkdir(parents=True, exist_ok=True)
        lock.write_text(str(os.getpid()))
        wrapper = cfg.paths.cosmos / "cosmosw"
        cmd = [sys.executable, str(wrapper), "dream", "--auto"] if wrapper.exists() else [sys.executable, "-m", "cosmos", "dream", "--auto"]
        log = (cfg.paths.state / "dream.log").open("a")
        subprocess.Popen(cmd, cwd=str(cfg.paths.root), stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                         start_new_session=True, env={**os.environ, "COSMOS_AUTO_DREAM": "1"})
        return True
    except Exception:
        try:
            lock.unlink()
        except Exception:
            pass
        return False


def session_start(cfg: Config) -> str:
    from .charter import summary
    from .atlas import check
    mems = Ledger(cfg.paths).load()
    k = int(cfg.get("retrieval.session_start_max", 10))
    parts = []
    ch = summary(cfg, mems)
    if ch:
        parts.append("cosm◎s · CHARTER (the team's working agreement — follow it over personal style):\n" + ch)
    facts = format_for_agent(top(mems, k), "cosm◎s · LEDGER (highest-signal team facts, grouped by lane in .cosmos/ledger/_index.md):")
    if facts:
        parts.append(facts)
    from .handoff import latest as latest_handoff
    h = latest_handoff(cfg)
    if h:
        parts.append(h)
    at = check(cfg)
    if at.get("exists"):
        drift = f" ⚠ {len(at['drift'])+len(at['missing'])} source file(s) changed since — run `cosmos atlas`" if (at["drift"] or at["missing"]) else ""
        parts.append(f"cosm◎s · ATLAS: architecture diagrams in .cosmos/ledger/atlas/ (generated {at['generated']} at {at['commit']}){drift}. Consult containers.md before structural changes.")
    return "\n\n".join(parts)


def prompt_context(cfg: Config, event: Dict[str, Any]) -> str:
    prompt = str(event.get("prompt", ""))
    if not prompt.strip():
        return ""
    for pfx in cfg.get("capture.explicit_prefixes", []):
        if prompt.lower().startswith(pfx):
            return ""   # explicit memory instruction; capture handles it on Stop
    mems = Ledger(cfg.paths).load()
    hits = retrieve(mems, prompt, k=int(cfg.get("retrieval.prompt_max", 6)))
    return format_for_agent(hits, "cosm◎s · what the team knows about this request:")


def _pid_alive(pid: int) -> bool:
    import os
    try:
        os.kill(pid, 0)
        return True
    except Exception:
        return False


def watcher_running(cfg: Config) -> bool:
    lock = cfg.paths.state / "watch.lock"
    try:
        return lock.exists() and _pid_alive(int(lock.read_text().split()[0]))
    except Exception:
        return False


def ensure_watcher(cfg: Config) -> bool:
    """Start the repo's watcher in the background if none is running. It exits by itself after two idle hours,
    so nothing is left behind; the next session start brings it back."""
    import os, subprocess
    if os.environ.get("COSMOS_NO_BACKGROUND") or not cfg.get("watch.auto", True) or watcher_running(cfg):
        return False
    try:
        cfg.paths.state.mkdir(parents=True, exist_ok=True)
        wrapper = cfg.paths.cosmos / "cosmosw"
        cmd = [sys.executable, str(wrapper), "watch", "--daemon"] if wrapper.exists() else [sys.executable, "-m", "cosmos", "watch", "--daemon"]
        log = (cfg.paths.state / "watch.log").open("a")
        subprocess.Popen(cmd, cwd=str(cfg.paths.root), stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True,
                         env={**os.environ, "COSMOS_WATCH_DAEMON": "1"})
        return True
    except Exception:
        return False


def _vendored_fingerprint(pkg_dir: Path) -> str:
    h = hashlib.sha1()
    for name in ("__init__.py", "hooks.py", "dream.py", "ui.py", "reader.py", "watch.py", "gate.py"):
        p = pkg_dir / name
        if p.exists():
            h.update(p.read_bytes())
    return h.hexdigest()[:12]


def auto_refresh(cfg: Config) -> bool:
    """When this machine runs a newer cosmos than the copy committed in .cosmos/vendor, refresh the vendored copy and
    the hook entries, so teammates and worktrees get the new behaviour on the next pull. Never touches a repo whose
    installed copy IS the vendored one."""
    try:
        here = Path(__file__).resolve().parent
        vend = cfg.paths.cosmos / "vendor" / "cosmos"
        if not vend.exists() or here == vend.resolve() or ".cosmos" in here.parts:
            return False
        if _vendored_fingerprint(here) == _vendored_fingerprint(vend):
            return False
        from .wrapper import vendor, write_wrapper
        write_wrapper(cfg.paths.cosmos)
        vendor(cfg.paths.cosmos)
        install_hooks(cfg.paths.claude_settings)
        _log(cfg, "vendored copy and hooks refreshed from the installed cosmos")
        return True
    except Exception:
        return False


def file_context(cfg: Config, event: Dict[str, Any]) -> str:
    """What the team knows about the file the agent is about to change: open flares, facts, rules anchored to it.
    Shown once per file per session so it informs without nagging."""
    inp = event.get("tool_input") or {}
    fp = inp.get("file_path") or inp.get("notebook_path")
    if not fp:
        return ""
    rel = relativize(str(fp), cfg.paths.root)
    if rel.startswith(("/", "external/")):
        return ""
    state = State(cfg.paths)
    sid = event.get("session_id", "")
    shown = state.data.setdefault("shown", {}).setdefault(sid or "-", [])
    if rel in shown:
        return ""
    mems = Ledger(cfg.paths).load()
    from .audit import OPEN_LIKE
    flares = [m for m in mems.values() if m.category == "finding" and m.meta.get("finding_status", "open") in OPEN_LIKE
              and any(rel.endswith(f) or f.endswith(rel) for f in m.files)]
    facts = [m for m in retrieve(mems, rel.rsplit("/", 1)[-1], paths=[rel], k=int(cfg.get("retrieval.file_max", 4)))
             if m.category != "finding" and m.status == "active" and any(rel.endswith(f) or f.endswith(rel) for f in m.files)]
    if not flares and not facts:
        return ""
    shown.append(rel)
    if len(shown) > 400:
        del shown[:200]
    state.save()
    lines = [f"cosm◎s · before you change `{rel}`:"]
    lines += [f"- open flare {m.meta.get('audit_id')} [{m.meta.get('severity')}]: {m.text}" for m in flares[:3]]
    lines += [f"- {m.category}: {m.text}" for m in facts[:4]]
    if flares:
        lines.append("Address or explicitly defer each open flare; a bug you fix here is filed fixed via cosmos_flare, without asking.")
    return "\n".join(lines)


def handle(stdin_text: str) -> int:
    try:
        event = json.loads(stdin_text) if stdin_text.strip() else {}
    except Exception:
        return 0
    try:
        import os
        cwd = Path(os.environ.get("CLAUDE_PROJECT_DIR") or event.get("cwd") or Path.cwd())
        cfg = load_config(cwd)
        if not cfg.paths.config.exists():
            return 0
        name = event.get("hook_event_name", "")
        if name == "SessionStart":
            out = session_start(cfg)
            if out:
                print(out)
                _log_inject(cfg, name, out)
            auto_refresh(cfg)
            if ensure_watcher(cfg):
                _log(cfg, "watcher started")
        elif name == "UserPromptSubmit":
            out = prompt_context(cfg, event)
            if out:
                print(out)
                _log_inject(cfg, name, out)
        elif name == "PreToolUse":
            out = file_context(cfg, event)
            if out:
                print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": out}}))
                _log_inject(cfg, name, out)
        elif name in ("Stop", "SessionEnd", "PreCompact", "PostToolUse", "SubagentStop"):
            n = capture(cfg, event)
            if n:
                _log(cfg, f"{name}: captured {n} observation(s)")
            if name == "Stop" and event.get("last_assistant_message"):
                from .handoff import record_auto
                record_auto(cfg, str(event.get("last_assistant_message")), event)
            if name in ("Stop", "SessionEnd") and event.get("hook_event_name") != "manual":
                pend = pending_count(cfg)
                if should_auto_dream(cfg, pend) and auto_dream(cfg):
                    _log(cfg, f"auto-dream started ({pend} observations waiting)")
            if name == "Stop":
                from .gate import evaluate, message
                res = evaluate(cfg, event)
                if res["block"]:
                    _log(cfg, f"Gate held the turn: {len(res['reasons'])-1} issue(s) on {len(res['edited'])} file(s)")
                    print(message(res), file=sys.stderr)
                    return 2   # the one deliberate block: Claude continues with the checklist
        return 0
    except Exception:
        try:
            cfg = load_config()
            _log(cfg, "hook error: " + traceback.format_exc().replace("\n", " | "))
        except Exception:
            pass
        return 0   # never break the developer's session


from .wrapper import HOOK_CMD as HOOK_COMMAND


def hook_entries(command: str = HOOK_COMMAND) -> Dict[str, Any]:
    h = lambda timeout: [{"type": "command", "command": command, "timeout": timeout}]
    return {
        "SessionStart": [{"hooks": h(10)}],
        "UserPromptSubmit": [{"hooks": h(10)}],
        "PreToolUse": [{"matcher": "Edit|Write|MultiEdit|NotebookEdit", "hooks": h(10)}],
        "Stop": [{"hooks": h(20)}],
        "PreCompact": [{"hooks": h(20)}],
        "SessionEnd": [{"hooks": h(20)}],
    }


def install_hooks(settings_path: Path, command: str = HOOK_COMMAND) -> bool:
    """Merge cosmos hooks into .claude/settings.json without touching other hooks. Returns True if changed."""
    settings: Dict[str, Any] = {}
    if settings_path.exists():
        try:
            settings = json.loads(settings_path.read_text() or "{}")
        except Exception:
            raise SystemExit(f"{settings_path} is not valid JSON; fix it or remove it and re-run.")
    hooks = settings.setdefault("hooks", {})
    changed = False
    for ev, entries in hook_entries(command).items():
        existing = hooks.setdefault(ev, [])
        ours = [e for e in existing if any("cosmos" in h.get("command", "") and "hook" in h.get("command", "") for h in e.get("hooks", []))]
        if not ours:
            existing.extend(entries)
            changed = True
        else:   # migrate an older cosmos command in place (e.g. the relative-path one)
            for e in ours:
                for h in e.get("hooks", []):
                    if "cosmos" in h.get("command", "") and h["command"] != command:
                        h["command"] = command
                        changed = True
    if changed:
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        settings_path.write_text(json.dumps(settings, indent=2) + "\n")
    return changed


def uninstall_hooks(settings_path: Path, command: str = HOOK_COMMAND) -> bool:
    if not settings_path.exists():
        return False
    settings = json.loads(settings_path.read_text() or "{}")
    hooks = settings.get("hooks", {})
    changed = False
    for ev in list(hooks):
        kept = [e for e in hooks[ev] if not any("cosmos" in h.get("command", "") and "hook" in h.get("command", "") for h in e.get("hooks", []))]
        if len(kept) != len(hooks[ev]):
            changed = True
        if kept:
            hooks[ev] = kept
        else:
            del hooks[ev]
    if changed:
        settings_path.write_text(json.dumps(settings, indent=2) + "\n")
    return changed
