"""Pulse: how cosmos is doing in this repository, measured from the repository's own records.

Two halves. Health: the checks that catch cosmos failing quietly (hooks silent while sessions are active, a briefing
over Claude Code's hook cap, the wrong copy of cosmos running, dreams in a loop, flares that name files this
repository does not have). Metrics: what cosmos did and what it cost (sessions and turns recorded, facts and flares,
retrieval quality from the dreams' evals, the context handed to agents, and, with --bench, how long each hook takes).

Every number comes from a file in .cosmos/ or from running the hook; nothing is estimated. `cosmos pulse --save`
appends the report to .cosmos/ledger/metrics/<date>.json (committed), so the history travels with the repository, and
a dream saves one a day by itself.
"""
from __future__ import annotations

import json
import os
import re
import statistics
import subprocess
import sys
import time
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from . import __version__
from .config import Config
from .store import Ledger, Memory

DAYS = 7


def _ts(s: str) -> Optional[datetime]:
    """2026-10-01T17:22:21Z (logs) or 20261001T172221Z (dream records)."""
    for fmt, n in (("%Y-%m-%dT%H:%M:%S", 19), ("%Y%m%dT%H%M%S", 15)):
        try:
            return datetime.strptime((s or "")[:n], fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def _median(xs: List[float]) -> Optional[float]:
    return round(statistics.median(xs), 1) if xs else None


def _p(xs: List[float], q: float) -> Optional[float]:
    if not xs:
        return None
    xs = sorted(xs)
    return round(xs[min(len(xs) - 1, int(round(q * (len(xs) - 1))))], 1)


# ---------------------------------------------------------------- what the records say
def injections(cfg: Config, days: int = DAYS) -> List[Dict[str, Any]]:
    """inject.log: one line per context hand-off — time, event, tokens (characters / 4), facts."""
    p = cfg.paths.state / "inject.log"
    since = datetime.now(timezone.utc) - timedelta(days=days)
    out = []
    for line in p.read_text(errors="ignore").splitlines() if p.exists() else []:
        parts = line.split()
        t = _ts(parts[0]) if parts else None
        if t and t >= since and len(parts) >= 4 and parts[2].isdigit():
            out.append({"at": t, "event": parts[1], "tokens": int(parts[2]), "facts": int(parts[3]) if parts[3].isdigit() else 0})
    return out


def dream_runs(cfg: Config, days: int = DAYS) -> List[Dict[str, Any]]:
    d = cfg.paths.state / "dreams"
    since = datetime.now(timezone.utc) - timedelta(days=days)
    runs = []
    for p in sorted(d.glob("*.json")) if d.exists() else []:
        try:
            r = json.loads(p.read_text())
        except (OSError, ValueError):
            continue
        t = _ts(str(r.get("at", "")))
        if t and t >= since:
            runs.append(r)
    return runs


def journal_lines(cfg: Config, days: int = DAYS) -> List[str]:
    d = cfg.paths.ledger / "journal"
    first = (date.today() - timedelta(days=days - 1)).isoformat()
    out = []
    for p in sorted(d.glob("*.md")) if d.exists() else []:
        if p.stem >= first:
            out += [l for l in p.read_text(errors="ignore").splitlines() if l.startswith("- **") and "<!-- obs_" in l]
    return list(dict.fromkeys(out))


# ---------------------------------------------------------------- metrics
def usage(cfg: Config) -> Dict[str, Any]:
    lines = journal_lines(cfg)
    people = Counter(m.group(1).strip() for l in lines for m in [re.match(r"- \*\*[\d:]+\*\* ([^·]+)·", l)] if m)
    return {"turns_recorded": len(lines), "people": len(people), "commits_recorded": sum(len(re.findall(r'\d+ commits?:', l)) for l in lines),
            "tests_ran_turns": sum("tests ran" in l for l in lines), "days": DAYS}


def memory(mems: Dict[str, Memory]) -> Dict[str, Any]:
    facts = [m for m in mems.values() if m.category != "finding"]
    active = [m for m in facts if m.status == "active"]
    since = (date.today() - timedelta(days=DAYS - 1)).isoformat()
    return {"active_facts": len(active), "rules": sum(m.source == "explicit" for m in active),
            "by_source": dict(Counter(m.source for m in active).most_common()),
            "new_last_7_days": sum(m.created >= since for m in facts),
            "waiting_on_a_human": sum(m.status in ("contradicted", "stale-candidate") for m in facts),
            "retired": sum(m.status in ("superseded", "forgotten") for m in facts)}


def flares(mems: Dict[str, Memory]) -> Dict[str, Any]:
    from .audit import CLOSED, NOTE, OPEN_LIKE
    fs = [m for m in mems.values() if m.category == "finding"]
    st = Counter(m.meta.get("finding_status", "open") for m in fs)
    days = []
    for m in fs:
        if m.meta.get("finding_status") == "fixed":
            done = m.meta.get("fixed_on") or (m.meta.get("status_at") or "")[:10] or m.updated
            try:
                days.append((date.fromisoformat(done[:10]) - date.fromisoformat(m.created[:10])).days)
            except ValueError:
                pass
    return {"total": len(fs), "open": sum(st[s] for s in OPEN_LIKE), "closed": sum(st[s] for s in CLOSED), "notes": st[NOTE],
            "fixed": st["fixed"], "regressions_caught": st["regressed"] + sum(1 for m in fs if "REGRESSION" in (m.reason or "")),
            "median_days_to_fix": _median([float(d) for d in days if d >= 0])}


def recall(cfg: Config) -> Dict[str, Any]:
    runs = [r for r in dream_runs(cfg, 90) if r.get("recall_at_5") is not None or r.get("edit_hit") is not None]
    if not runs:
        return {}
    last, first = runs[-1], runs[0]
    return {"recall_at_5": last.get("recall_at_5"), "before_edit_hit": last.get("edit_hit"), "measured_at": last.get("at"),
            "first_recall_at_5": first.get("recall_at_5"), "first_before_edit_hit": first.get("edit_hit"), "evals": len(runs)}


def context(cfg: Config) -> Dict[str, Any]:
    inj = injections(cfg)
    by = lambda e: [i["tokens"] for i in inj if i["event"] == e]
    prompts = [i for i in inj if i["event"] == "UserPromptSubmit"]
    return {"session_start_tokens_median": _median(by("SessionStart")), "prompt_tokens_median": _median(by("UserPromptSubmit")),
            "prompt_tokens_p90": _p(by("UserPromptSubmit"), 0.9), "before_edit_tokens_median": _median(by("PreToolUse")),
            "prompts_with_facts": sum(i["facts"] > 0 for i in prompts), "prompts": len(prompts), "handoffs": len(inj)}


def dreams(cfg: Config) -> Dict[str, Any]:
    runs = dream_runs(cfg)
    return {"runs": len(runs), "model_curated": sum(bool(r.get("llm_used")) for r in runs),
            "observations_processed": sum(int(r.get("observations_processed") or 0) for r in runs),
            "turns_read": sum(int(r.get("turns_read") or 0) for r in runs),
            "duration_s_median": _median([round((r.get("duration_ms") or 0) / 1000, 1) for r in runs if r.get("duration_ms")])}


# ---------------------------------------------------------------- health
def _running_copy(cfg: Config) -> Dict[str, str]:
    from .upgrade import vendored_version
    w = cfg.paths.cosmos / "cosmosw"
    code = (f"w = {str(w)!r}; src = open(w).read().split('from cosmos.cli import main')[0]; "
            "exec(src, {'__file__': w, '__name__': 'pulse'}); import cosmos; print(cosmos.__version__, cosmos.__file__)")
    try:   # started from .cosmos/, as the wrapper's own process is (its folder is first on sys.path)
        env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}   # what a hook sees, not this process's path
        out = subprocess.run([sys.executable, "-c", code], cwd=str(cfg.paths.cosmos), env=env, capture_output=True, text=True, timeout=30).stdout.split()
    except (OSError, subprocess.SubprocessError):
        out = []
    where = "" if len(out) < 2 else "repository copy" if "/.cosmos/vendor/" in out[1] else "pip install" if "-packages" in out[1] else "editable checkout"
    return {"vendored": vendored_version(cfg), "runs": out[0] if out else "", "from": where}


def health(cfg: Config, mems: Dict[str, Memory]) -> List[Dict[str, str]]:
    from .audit import OPEN_LIKE
    from .hooks import HOOK_TEXT_CAP, session_start
    checks: List[Dict[str, str]] = []
    def check(name: str, ok: bool, detail: str) -> None:
        checks.append({"check": name, "ok": "yes" if ok else "no", "detail": detail})
    brief = len(session_start(cfg))
    check("briefing under the hook cap", brief < HOOK_TEXT_CAP, f"{brief:,} of {HOOK_TEXT_CAP:,} characters")
    run = _running_copy(cfg)
    from .upgrade import vtuple
    check("this repository's cosmos runs", run.get("from") != "pip install" or vtuple(run.get("runs", "")) > vtuple(run.get("vendored", "")),
          f"{run.get('runs') or '?'} from the {run.get('from') or '?'} (repository copy {run.get('vendored') or 'none'})")
    inj = injections(cfg, 2)
    last_inject = max((i["at"] for i in inj), default=None)
    from .adapters import find_claude_sessions
    try:
        newest = max((p.stat().st_mtime for p, _ in find_claude_sessions(cfg.paths.root)), default=0.0)
    except OSError:
        newest = 0.0
    active = newest and time.time() - newest < 3600
    silent = active and (last_inject is None or newest - last_inject.timestamp() > 1800)
    check("hooks answer active sessions", not silent,
          "last hand-off " + (last_inject.strftime("%Y-%m-%d %H:%MZ") if last_inject else "none in 2 days")
          + (" · a session was active " + datetime.fromtimestamp(newest, timezone.utc).strftime("%H:%MZ") if newest else ""))
    log = cfg.paths.state / "dream.log"
    hour = datetime.now(timezone.utc) - timedelta(hours=1)
    recent = [l for l in (log.read_text(errors="ignore").splitlines() if log.exists() else []) if "auto-dream" in l and (_ts(l) or hour) > hour]
    check("dreams keep their pace", len(recent) <= 3, f"{len(recent)} dream(s) in the last hour")
    foreign = [m.meta.get("audit_id", m.id) for m in mems.values() if m.category == "finding" and m.meta.get("finding_status", "open") in OPEN_LIKE
               and m.files and not any((cfg.paths.root / f).exists() for f in m.files)]
    from .security import is_instruction_file, scan_file, tracked, withheld
    bad = [f for rel in tracked(cfg.paths.root) if is_instruction_file(rel) and not rel.startswith(".cosmos/ledger/")
           for f in scan_file(cfg.paths.root, rel) if f["kind"] != "secret"]
    held = sum(1 for m in mems.values() if m.status == "active" and withheld(m.text, m.meta))
    check("instruction files and notes are clean", not bad and not held,
          f"{len(bad)} hidden or instruction-like line(s) in files agents read, {held} note(s) withheld" + (f": {bad[0]['file']}:{bad[0]['line']}" if bad else ""))
    check("open flares point at this repository", not foreign, f"{len(foreign)} name only files it lacks" + (f": {', '.join(foreign[:3])}" if foreign else ""))
    return checks


# ---------------------------------------------------------------- hook speed
EVENTS = {"SessionStart": {}, "UserPromptSubmit": {"prompt": "what do we know about the files I am about to change"},
          "PreToolUse": {"tool_name": "Edit", "tool_input": {"file_path": "README.md", "old_string": "a", "new_string": "b"}}}


def bench(cfg: Config, runs: int = 5) -> Dict[str, Any]:
    """Wall time of the hook command as Claude Code runs it (a fresh process each time), per event, in milliseconds."""
    w = cfg.paths.cosmos / "cosmosw"
    env = dict(os.environ, COSMOS_NO_BACKGROUND="1", COSMOS_BENCH="1", CLAUDE_PROJECT_DIR=str(cfg.paths.root), CLAUDE_CODE_ENTRYPOINT="cli")
    out: Dict[str, Any] = {}
    for event, extra in EVENTS.items():
        times = []
        for i in range(runs):
            ev = json.dumps(dict(extra, hook_event_name=event, session_id="pulse-bench", cwd=str(cfg.paths.root)))
            t0 = time.perf_counter()
            subprocess.run([sys.executable, str(w), "hook"], input=ev, cwd=str(cfg.paths.root), env=env, capture_output=True, text=True, timeout=60)
            times.append((time.perf_counter() - t0) * 1000)
        out[event] = {"median_ms": _median(times), "max_ms": round(max(times), 1)}
    out["runs"] = runs
    return out


# ---------------------------------------------------------------- the report
def run(cfg: Config, with_bench: bool = False) -> Dict[str, Any]:
    mems = Ledger(cfg.paths).load()
    rep: Dict[str, Any] = {"repo": cfg.paths.root.name, "at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "cosmos": __version__,
                           "health": health(cfg, mems), "usage": usage(cfg), "memory": memory(mems), "flares": flares(mems),
                           "recall": recall(cfg), "context": context(cfg), "dreams": dreams(cfg)}
    if with_bench:
        rep["hook_ms"] = bench(cfg)
    return rep


def save(cfg: Config, rep: Dict[str, Any]) -> Path:
    d = cfg.paths.ledger / "metrics"
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"{rep['at'][:10]}.json"
    p.write_text(json.dumps(rep, indent=1, ensure_ascii=False) + "\n")
    return p


def due(cfg: Config) -> bool:
    d = cfg.paths.ledger / "metrics"
    return not (d / f"{datetime.now(timezone.utc).date().isoformat()}.json").exists()   # the date save() names the file by


def text(rep: Dict[str, Any]) -> str:
    u, m, f, r, c, d = rep["usage"], rep["memory"], rep["flares"], rep["recall"], rep["context"], rep["dreams"]
    lines = [f"cosm◎s pulse · {rep['repo']} · {rep['at']} · cosmos {rep['cosmos']}", "", "health"]
    lines += [f"  {'✓' if h['ok'] == 'yes' else '✗'} {h['check']}: {h['detail']}" for h in rep["health"]]
    lines += ["", f"last {u['days']} days",
              f"  {u['turns_recorded']} agent turns recorded by {u['people']} people · {u['commits_recorded']} turns with commits · tests ran in {u['tests_ran_turns']}",
              f"  {m['active_facts']} active facts ({m['rules']} rules) · {m['new_last_7_days']} new · {m['waiting_on_a_human']} waiting on a human · {m['retired']} retired",
              f"  {f['total']} flares: {f['open']} open, {f['fixed']} fixed" + (f" (median {f['median_days_to_fix']:g} days)" if f["median_days_to_fix"] is not None else "") + f", {f['regressions_caught']} regressions caught",
              f"  {d['runs']} dreams ({d['model_curated']} model-curated) · {d['turns_read']:,} session turns read · median {d['duration_s_median'] or 0:g} s"]
    if r:
        lines.append(f"  recall@5 {r['recall_at_5']} · before an edit {r['before_edit_hit']} (first measured: {r['first_recall_at_5']} · {r['first_before_edit_hit']}, {r['evals']} evals)")
    lines.append(f"  context: session start {c['session_start_tokens_median'] or 0:g} tokens · a prompt {c['prompt_tokens_median'] or 0:g} (p90 {c['prompt_tokens_p90'] or 0:g}) · "
                 f"before an edit {c['before_edit_tokens_median'] or 0:g} · facts brought to {c['prompts_with_facts']} of {c['prompts']} prompts")
    if rep.get("hook_ms"):
        h = rep["hook_ms"]
        lines.append("  hook time (fresh process, median of %d): " % h["runs"] + " · ".join(f"{e} {v['median_ms']:g} ms" for e, v in h.items() if e != "runs"))
    return "\n".join(lines)
