"""cosmos CLI. Fast paths (status/hook) touch no LLM and finish in tens of milliseconds."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import webbrowser
from datetime import date
from pathlib import Path
from typing import List, Optional

from . import __version__
from .config import Config, find_repo_root, is_initialized, load_config
from .store import Ledger, Memory, Observations, State, make_id, today

C = {"g": "\033[32m", "y": "\033[33m", "r": "\033[31m", "b": "\033[34m", "d": "\033[2m", "x": "\033[0m", "B": "\033[1m"}


def col(s: str, c: str) -> str:
    return f"{C[c]}{s}{C['x']}" if sys.stdout.isatty() else s


def _require(cfg: Config) -> None:
    if not cfg.paths.config.exists():
        raise SystemExit(col("cosmos is not initialized here. Run: cosmos init", "y"))


def _find(mems, key: str) -> Optional[Memory]:
    if key in mems:
        return mems[key]
    for m in mems.values():
        if m.id.startswith(key) or m.id.endswith(key):
            return m
    k = key.lower()
    hits = [m for m in mems.values() if k in m.text.lower()]
    return hits[0] if len(hits) == 1 else (min(hits, key=lambda m: len(m.text)) if hits else None)


def _finish(cfg: Config, mems) -> None:
    from .render import render_all
    Ledger(cfg.paths).save_all(mems.values())
    render_all(cfg, mems)


# ---------------------------------------------------------------- commands
def cmd_init(a) -> int:
    from .hooks import install_hooks
    from .obsidian import prepare_vault
    from .render import render_all
    root = find_repo_root(Path(a.path) if a.path else None)
    from . import sync as _sync
    branch_note = ""
    if not a.no_branch and (root / ".git").exists():
        if (root / ".cosmos").exists() and not _sync.is_branch_mode(load_config(root)):
            ok, msg = _sync.migrate(root)
            branch_note = f"ledger moved to the `cosmos` branch (.cosmos/ is a worktree of it; its removal from this branch is staged — commit it with your next change)" if ok else f"could not move the ledger to its own branch: {msg}"
        else:
            ok, msg = _sync.attach(root)
            branch_note = "ledger lives on the `cosmos` branch (.cosmos/ is a worktree of it, ignored by your branches)" if ok else f"could not attach the ledger branch: {msg}"
        _sync.ensure_ignored(root)
    cfg = load_config(root)
    fresh = not cfg.paths.config.exists()
    cfg.paths.ensure()
    if fresh:
        cfg.save()
    if not _sync.is_branch_mode(cfg):
        gi = root / ".gitignore"
        txt = gi.read_text() if gi.exists() else ""
        if ".cosmos/state/" not in txt and ".cosmos/" not in txt:
            gi.write_text(txt.rstrip("\n") + ("\n" if txt else "") + ".cosmos/state/\n")
    from .wrapper import hook_command, vendor, write_wrapper
    write_wrapper(cfg.paths.cosmos)
    if not a.no_vendor:
        vendor(cfg.paths.cosmos)
    command = a.command or hook_command(root)
    hooks_changed = install_hooks(cfg.paths.claude_settings, command)
    prepare_vault(cfg)
    from .charter import ensure as ensure_charter
    from .atlas import COMMAND_MD, build as build_atlas
    ensure_charter(cfg)
    cmd_dir = root / ".claude" / "commands"; cmd_dir.mkdir(parents=True, exist_ok=True)
    (cmd_dir / "atlas.md").write_text(COMMAND_MD)
    inv = build_atlas(cfg)
    from .adapters import AGENTS
    from .connect import connect as _connect
    _connect(cfg, list(AGENTS))                       # every agent's instruction file + MCP config, not only Claude's
    render_all(cfg, Ledger(cfg.paths).load())
    # user-level hooks: any checkout or worktree of any cosmos repo on this machine is covered, whatever the branch has
    import os
    user_hooks = False if (a.no_user_hooks or os.environ.get("COSMOS_NO_BACKGROUND")) else install_hooks(Path.home() / ".claude" / "settings.json", command)
    # seed from what already exists: the journal of past work, and the recent history marked for the model
    seeded = ""
    if not a.no_seed:
        from .adapters import find_claude_sessions
        from .hooks import auto_dream, backfill_journal, capture, ensure_watcher
        sessions = find_claude_sessions(root)
        j = sum(backfill_journal(cfg, p, sid) for p, sid in sessions)
        n = sum(capture(cfg, {"transcript_path": str(p), "session_id": sid, "hook_event_name": "manual", "cwd": str(root), "since_days": 14}) for p, sid in sessions)
        if sessions:
            seeded = f"{len(sessions)} past session(s) found · {j} journal entries · recent history marked for the model"
            auto_dream(cfg)                            # first dream starts now, in the background
        ensure_watcher(cfg)
    if _sync.is_branch_mode(cfg):
        _sync.commit(root, "cosmos: init")
        _sync.sync_background(cfg, "cosmos: init")
    print(col("✓", "g"), "cosmos", "initialized" if fresh else "already initialized", "in", root)
    if branch_note:
        print(col("✓", "g"), branch_note)
    print(col("✓", "g"), f".cosmos/charter.md (team working agreement + Gate rules) · /atlas command for Claude Code")
    print(col("✓", "g"), f"atlas built: {len(inv['apps'])} apps · {len(inv['services'])} services · {len(inv['stores'])} stores · {len(inv['k8s'])} k8s objects · {sum(len(a['endpoints']) for a in inv['api'])} endpoints")
    print(col("✓", "g"), ".cosmos/  (config.json, ledger/, observations/, state/)" + (" · on branch `cosmos`, pushed by itself" if _sync.is_branch_mode(cfg) else ""))
    print(col("✓", "g"), f".claude/settings.json hooks {'installed' if hooks_changed else 'present'} → `{command}`")
    print(col("✓", "g"), ".cosmos/cosmosw wrapper" + ("" if a.no_vendor else " + vendored copy → teammates need no install: git clone && claude"))
    print(col("✓", "g"), "instruction files for every agent (CLAUDE.md, AGENTS.md, GEMINI.md, Cursor, Copilot, Cline, Windsurf) · MCP configs → `cosmos mcp`")
    print(col("✓", "g"), f"user-level hooks {'installed' if user_hooks else 'present'} in ~/.claude/settings.json → every worktree and checkout is covered")
    if seeded:
        print(col("✓", "g"), seeded + " · first dream running in the background")
    print(col("✓", "g"), "watcher running in the background: follows Claude Code, Codex and Gemini sessions here; dreams start themselves")
    print()
    print("That is all. Work with your agent. Look at it with:  cosmos ui")
    return 0


def cmd_status(a) -> int:
    cfg = load_config(); _require(cfg)
    mems = Ledger(cfg.paths).load()
    state = State(cfg.paths)
    pending = sum(1 for o in Observations(cfg.paths).iter_all() if o.get("id") and not state.is_dreamed(o["id"]))
    by_status = {}
    for m in mems.values():
        by_status[m.status] = by_status.get(m.status, 0) + 1
    if a.json:
        print(json.dumps({"root": str(cfg.paths.root), "memories": len(mems), "by_status": by_status, "pending_observations": pending}))
        return 0
    print(col(f"cosmos {__version__}", "B"), col(str(cfg.paths.root), "d"))
    print(f"  memories            {len(mems)}   " + " ".join(f"{k}={v}" for k, v in sorted(by_status.items())))
    print(f"  pending observations {pending}" + (col("   → run `cosmos dream`", "y") if pending else ""))
    hooks = cfg.paths.claude_settings.exists() and "cosmos" in cfg.paths.claude_settings.read_text()
    print(f"  hooks               {'installed' if hooks else col('missing (cosmos init)', 'y')}")
    return 0


def cmd_hook(a) -> int:
    from .hooks import handle
    return handle(sys.stdin.read())


def cmd_capture(a) -> int:
    """Capture from session logs of any agent: Claude Code (default), Codex, Gemini/Antigravity, or a file."""
    from .adapters import find_claude_sessions, find_codex_sessions, find_gemini_sessions
    from .hooks import capture
    cfg = load_config(); _require(cfg)
    jobs: List[tuple] = []
    if a.transcript:
        jobs = [(Path(a.transcript), a.agent if a.agent != "all" else "claude", Path(a.transcript).stem)]
    else:
        agents = ["claude", "codex", "gemini"] if a.agent == "all" else [a.agent]
        if "claude" in agents:
            jobs += [(p, "claude", sid) for p, sid in find_claude_sessions(cfg.paths.root)]   # main sessions + subagents
        if "codex" in agents:
            jobs += [(p, "codex", p.stem) for p in find_codex_sessions(cfg.paths.root)]
        if "gemini" in agents:
            jobs += [(p, "gemini", p.stem) for p in find_gemini_sessions(cfg.paths.root)]
        if not jobs:
            print(col(f"no {a.agent} sessions found for {cfg.paths.root}", "y")); return 1
    total = 0; per: Dict[str, int] = {}
    if getattr(a, "rebuild_journal", False):
        from .hooks import backfill_journal
        for p, agent, sid in jobs:
            n = backfill_journal(cfg, p, sid, agent); total += n
            if a.verbose and n:
                print(f"  [{agent}] {p.name}: {n} journal entr{'y' if n == 1 else 'ies'}")
        print(col("✓", "g"), f"journal rebuilt: {total} entr{'y' if total == 1 else 'ies'} from {len(jobs)} session(s) — cosmos dream writes them to .cosmos/ledger/journal/")
        return 0
    if getattr(a, "reread", False):
        from .store import State
        st = State(cfg.paths)
        for p, agent, sid in jobs:
            st.set_offset(f"{agent}:{sid}" if agent != "claude" else sid, 0)
        st.save()
    for p, agent, sid in jobs:
        n = capture(cfg, {"transcript_path": str(p), "session_id": sid, "hook_event_name": "manual", "cwd": str(cfg.paths.root), "since_days": a.days}, agent)
        total += n; per[agent] = per.get(agent, 0) + n
        if a.verbose:
            print(f"  [{agent}] {p.name}: {n}")
    print(col("✓", "g"), f"captured {total} observation(s) from {len(jobs)} session(s) — " + ", ".join(f"{k} {v}" for k, v in per.items()))
    from .hooks import capture_mode, pending_count
    from .reader import windows_waiting
    from .store import State
    w = windows_waiting(State(cfg.paths))
    if capture_mode(cfg) == "model":
        print(col("  next", "d"), f"{w} session range(s) marked for the model, {pending_count(cfg) - w} explicit items → cosmos dream reads them")
    else:
        print(col("  next", "d"), f"{pending_count(cfg)} waiting for a dream → cosmos dream")
    return 0


def cmd_sync(a) -> int:
    """Commit and publish the ledger branch (normally done for you by dreams and the watcher)."""
    from . import sync as _sync
    cfg = load_config(); _require(cfg)
    if not _sync.is_branch_mode(cfg):
        print(col("·", "d"), ".cosmos is tracked in this branch, not on its own branch (run `cosmos init` to move it)"); return 0
    c = _sync.commit(cfg.paths.root, a.message or "cosmos: sync")
    if a.push:
        ok, out = _sync.push(cfg.paths.root)
        print(col("✓", "g") if ok else col("✗", "r"), f"cosmos branch {'pushed' if ok else 'not pushed: ' + out}" + (" (new commit)" if c else ""))
    else:
        print(col("✓", "g"), "committed" if c else "nothing to commit")
    return 0


def cmd_watch(a) -> int:
    """Follow every agent's sessions for this repo (all worktrees, subagents; Claude Code, Codex, Gemini) without hooks."""
    from .watch import run
    cfg = load_config(); _require(cfg)
    agents = ["claude", "codex", "gemini"] if a.agent == "all" else [a.agent]
    if not a.once and not a.daemon:
        print(col("cosmos watch", "B"), f"· {cfg.paths.root.name} · every {a.interval}s · Ctrl-C to stop", flush=True)
    return run(cfg, interval=a.interval, once=a.once, agents=agents, verbose=True, daemon=a.daemon, idle_minutes=a.idle)


def cmd_hooks(a) -> int:
    """Install the Claude Code hooks at user level so every checkout and worktree of every cosmos repo is covered."""
    from .hooks import install_hooks
    p = Path.home() / ".claude" / "settings.json"
    changed = install_hooks(p)
    print(col("✓", "g"), f"user-level hooks {'installed' if changed else 'already present'} in {p} — they run only where a repo has .cosmos, and exit silently elsewhere")
    return 0


def cmd_mcp(a) -> int:
    from .mcp import serve
    cfg = load_config(); _require(cfg)
    serve(cfg); return 0


def cmd_connect(a) -> int:
    from .adapters import AGENTS
    from .connect import codex_snippet, connect, write_codex_user_config
    from .render import render_all
    cfg = load_config(); _require(cfg)
    agents = list(AGENTS) if "all" in a.agents else a.agents
    # instruction files per agent
    extra = []
    for ag in agents:
        for f in AGENTS[ag]["instructions"]:
            if f not in ("CLAUDE.md", "AGENTS.md") and f not in extra:
                extra.append(f)
    cfg.data.setdefault("render", {})["targets"] = sorted(set((cfg.get("render.targets", ["GEMINI.md"]) or []) + extra)); cfg.save()
    changed = render_all(cfg, Ledger(cfg.paths).load())
    done = connect(cfg, agents)
    print(col("✓", "g"), "instruction files:", ", ".join(f for f in changed if f != str(cfg.paths.ledger / "_index.md")) or "(already current)")
    print(col("✓", "g"), "MCP configs:", ", ".join(done) or "(already current)")
    if "codex" in agents:
        if a.write_user:
            p = write_codex_user_config(cfg.paths.root); print(col("✓", "g"), f"Codex: added [mcp_servers.cosmos] to {p}")
        else:
            print(col("  Codex", "B"), "reads MCP servers from ~/.codex/config.toml — add (or run `cosmos connect codex --write-user`):\n" + "\n".join("    " + l for l in codex_snippet(cfg.paths.root).splitlines()))
    print(col("  Cowork / Claude Desktop", "B"), "reads CLAUDE.md in the project; add the same MCP entry under Settings → Connectors (command python3, args .cosmos/cosmosw mcp).")
    print(col("  capture", "d"), "Claude Code: automatic via hooks · Codex / Gemini: `cosmos capture --agent all` reads their session logs · everyone: cosmos_remember / cosmos_flare tools via MCP")
    return 0


def cmd_dream(a) -> int:
    from .dream import dream
    from .render import render_all
    cfg = load_config(); _require(cfg)
    if getattr(a, "auto", False):   # started by a hook in the background: quiet, one at a time, logged
        from .store import now_iso
        lock = cfg.paths.state / "dream.lock"
        try:
            rep = dream(cfg, verbose=False)
            render_all(cfg, Ledger(cfg.paths).load())
            print(f"{now_iso()} auto-dream: {rep.summary()}", flush=True)
        finally:
            try:
                lock.unlink()
            except Exception:
                pass
        return 0
    rep = dream(cfg, use_llm=(True if a.llm else (False if a.no_llm else None)), verbose=True, recurate_all=bool(getattr(a, "recurate", False)))
    render_all(cfg, Ledger(cfg.paths).load())
    print(col("💤 dream complete:", "B"), rep.summary())
    for m in rep.new[:15]:
        print(col("  +", "g"), f"[{m.category}] {m.text}")
    if len(rep.new) > 15:
        print(col(f"  … {len(rep.new)-15} more", "d"))
    for a_, b_ in rep.contradictions:
        print(col("  ⚡ contradiction", "r"), a_, "↔", b_, col("   cosmos review", "d"))
    for a_, b_ in rep.superseded:
        print(col("  ↷ superseded", "y"), a_, "→", b_)
    for s in rep.stale:
        print(col("  ⏳ stale", "y"), s)
    return 0


def cmd_ledger(a) -> int:
    """`cosmos ledger` / `cosmos ui`: the control room. Serves on localhost so verdicts and dreams can act."""
    from .ui import serve, snapshot, write_html
    cfg = load_config(); _require(cfg)
    if a.obsidian:
        return cmd_obsidian(argparse.Namespace(open=True, vault=None))
    if a.static:
        # self-contained snapshot (read-only) - handy to attach to a PR or send around
        html = write_html(cfg).read_text().replace("load();\n</script>", "window.__SNAPSHOT__=" + json.dumps(snapshot(cfg), ensure_ascii=False, default=str) + ";load();\n</script>")
        out = cfg.paths.state / "ledger.html"; out.write_text(html)
        print(col("✓", "g"), out)
        if not a.no_open:
            webbrowser.open(out.as_uri())
        return 0
    serve(cfg, a.port, not a.no_open, strict_port=a.strict_port)
    return 0


def cmd_obsidian(a) -> int:
    from .obsidian import link_into_vault, open_in_obsidian, prepare_vault
    cfg = load_config(); _require(cfg)
    vault = prepare_vault(cfg)
    print(col("✓", "g"), "vault ready:", vault)
    if getattr(a, "vault", None):
        t = link_into_vault(cfg, Path(a.vault))
        print(col("✓", "g"), "linked into your vault:", t)
        vault = t
    if getattr(a, "open", False):
        uri = open_in_obsidian(vault)
        print(col("✓", "g"), "opening", uri or "(could not launch; open the folder as a vault in Obsidian)")
    else:
        print(col("  hint:", "d"), "cosmos obsidian --open   |   cosmos obsidian --vault ~/Obsidian/Team")
    return 0


def cmd_remember(a) -> int:
    cfg = load_config(); _require(cfg)
    from .config import git_author
    from .privacy import redact
    text = " ".join(" ".join(a.text).split())
    text, fired = redact(text)
    if fired:
        print(col(f"redacted {', '.join(fired)} before storing", "y"))
    mems = Ledger(cfg.paths).load()
    mid = make_id(text)
    m = mems.get(mid) or Memory(id=mid, text=text, category=a.category, source="explicit", confidence=0.95, importance=0.95,
                                authors=[git_author(cfg.paths.root)], files=list(a.file or []))
    m.status, m.updated, m.last_verified = "active", today(), today()
    mems[mid] = m
    _finish(cfg, mems)
    print(col("✓", "g"), f"remembered {mid} [{m.category}] {text}")
    return 0


def cmd_forget(a) -> int:
    cfg = load_config(); _require(cfg)
    mems = Ledger(cfg.paths).load()
    m = _find(mems, a.id)
    if not m:
        print(col("no such memory", "r")); return 1
    if a.hard:
        Ledger(cfg.paths).delete(m.id); del mems[m.id]
    else:
        m.status, m.updated, m.reason = "forgotten", today(), f"Forgotten by developer on {today()}"
    _finish(cfg, mems)
    print(col("✓", "g"), f"{'deleted' if a.hard else 'forgot'} {m.id}: {m.text}")
    return 0


def cmd_verify(a) -> int:
    cfg = load_config(); _require(cfg)
    mems = Ledger(cfg.paths).load()
    m = _find(mems, a.id)
    if not m:
        print(col("no such memory", "r")); return 1
    m.status, m.last_verified, m.updated = "active", today(), today()
    m.confidence = min(0.99, m.confidence + 0.1)
    m.reason = f"Verified by developer on {today()}"
    for c in m.contradicts:
        if c in mems and a.resolve:
            o = mems[c]; o.status, o.superseded_by, o.updated = "superseded", m.id, today()
            o.reason = f"Superseded on {today()}: developer verified [[{m.id}]]"; m.supersedes = c
    if a.resolve:
        m.contradicts = []
    _finish(cfg, mems)
    print(col("✓", "g"), f"verified {m.id}: {m.text}")
    return 0


def cmd_why(a) -> int:
    cfg = load_config(); _require(cfg)
    mems = Ledger(cfg.paths).load()
    m = _find(mems, " ".join(a.query))
    if not m:
        print(col("no memory matches", "y")); return 1
    print(col(m.text, "B"))
    print(f"  id          {m.id}")
    print(f"  category    {m.category}      status {m.status}      source {m.source}")
    print(f"  confidence  {int(m.confidence*100)}%   ({m.evidence_count} observation{'s' if m.evidence_count!=1 else ''})")
    print(f"  timeline    created {m.created} · updated {m.updated} · verified {m.last_verified}")
    for f in m.files:
        print(f"  evidence    {f}")
    if m.authors:
        print(f"  seen by     {', '.join(m.authors)}")
    if m.reason:
        print(f"  note        {m.reason}")
    if m.supersedes:
        print(f"  supersedes  {m.supersedes}: {mems[m.supersedes].text if m.supersedes in mems else ''}")
    if m.superseded_by:
        print(col(f"  superseded  by {m.superseded_by}: {mems[m.superseded_by].text if m.superseded_by in mems else ''}", "y"))
    for c in m.contradicts:
        print(col(f"  contradicts {c}: {mems[c].text if c in mems else ''}", "r"))
    return 0


def cmd_search(a) -> int:
    from .retrieve import retrieve
    cfg = load_config(); _require(cfg)
    mems = Ledger(cfg.paths).load()
    hits = retrieve(mems, " ".join(a.query), paths=a.file, k=a.k)
    if a.json:
        print(json.dumps([m.__dict__ for m in hits], default=str)); return 0
    for m in hits:
        print(f"{col(m.id,'d')} [{m.category}] {m.text}" + (col(f"  ({m.status})", "y") if m.status != "active" else ""))
    if not hits:
        print(col("no matches", "d"))
    return 0


def cmd_review(a) -> int:
    cfg = load_config(); _require(cfg)
    mems = Ledger(cfg.paths).load()
    issues = [m for m in mems.values() if m.status in ("contradicted", "stale-candidate")]
    if not issues:
        print(col("✓ nothing to review", "g")); return 0
    print(col(f"{len(issues)} item(s) need a human:", "B"))
    for m in issues:
        print(f"\n{col(m.status.upper(), 'r' if m.status=='contradicted' else 'y')}  {m.id}  [{m.category}]")
        print(f"  {m.text}")
        for c in m.contradicts:
            if c in mems:
                print(f"  ↔ {c}: {mems[c].text}")
        if m.reason:
            print(col(f"  {m.reason}", "d"))
        print(col(f"  cosmos verify {m.id} --resolve   |   cosmos forget {m.id}", "d"))
    return 0


def cmd_health(a) -> int:
    cfg = load_config(); _require(cfg)
    mems = Ledger(cfg.paths).load()
    n = len(mems) or 1
    active = [m for m in mems.values() if m.status == "active"]
    with_ev = sum(1 for m in active if m.files)
    fresh = sum(1 for m in active if (date.today() - date.fromisoformat(m.last_verified)).days <= 90)
    print(col("MEMORY HEALTH", "B"), col(str(cfg.paths.root.name), "d"))
    print(f"  memories              {len(mems)}")
    print(f"  active                {len(active)}")
    print(f"  with file evidence    {int(100*with_ev/max(1,len(active)))}%")
    print(f"  verified ≤90d         {int(100*fresh/max(1,len(active)))}%")
    print(f"  contradictions        {sum(1 for m in mems.values() if m.status=='contradicted')}")
    print(f"  stale candidates      {sum(1 for m in mems.values() if m.status=='stale-candidate')}")
    print(f"  superseded (history)  {sum(1 for m in mems.values() if m.status=='superseded')}")
    print(f"  explicit rules        {sum(1 for m in mems.values() if m.source=='explicit')}")
    cats = {}
    for m in active:
        cats[m.category] = cats.get(m.category, 0) + 1
    print("  by category           " + ", ".join(f"{k} {v}" for k, v in sorted(cats.items(), key=lambda x: -x[1])))
    return 0


def cmd_render(a) -> int:
    from .render import render_all
    cfg = load_config(); _require(cfg)
    changed = render_all(cfg, Ledger(cfg.paths).load())
    print(col("✓", "g"), "rendered:", ", ".join(changed))
    return 0


def cmd_doctor(a) -> int:
    cfg = load_config()
    ok = True
    def line(good, msg):
        nonlocal ok
        ok = ok and good
        print(col("✓", "g") if good else col("✗", "r"), msg)
    line(cfg.paths.config.exists(), f"config {cfg.paths.config}")
    s = cfg.paths.claude_settings
    line(s.exists() and "cosmos" in s.read_text(), f"hooks in {s}")
    line(shutil.which("claude") is not None, "claude CLI on PATH")
    line(shutil.which("cosmos") is not None or True, f"cosmos entrypoint: {shutil.which('cosmos') or sys.executable + ' -m cosmos'}")
    from .providers import get_provider
    prov = get_provider(cfg.get("llm", {}) or {})
    if prov is None:
        line(False, "LLM: none available — dreams run on heuristics only. Log in to Claude Code (`claude`, then /login) or set ANTHROPIC_API_KEY.")
    else:
        try:
            r = prov.complete("Reply with JSON.", '{"ping": true}', {"type": "object", "properties": {"pong": {"type": "boolean"}}, "required": ["pong"], "additionalProperties": False})
            line(bool(r), f"LLM: {prov.name}" + ("" if r else " (no reply)"))
        except Exception as e:
            line(False, f"LLM: {prov.name} configured but failing — {str(e)[:120]}")
    if cfg.paths.log.exists():
        tail = cfg.paths.log.read_text().splitlines()[-3:]
        print(col("  last hook log lines:", "d"))
        for t in tail:
            print(col("   " + t, "d"))
    return 0 if ok else 1


def cmd_uninstall(a) -> int:
    from .hooks import uninstall_hooks
    cfg = load_config()
    ch = uninstall_hooks(cfg.paths.claude_settings)
    print(col("✓", "g"), "hooks removed" if ch else "no cosmos hooks found", "— .cosmos/ and the managed blocks were left in place")
    return 0


def cmd_update(a) -> int:
    from .wrapper import vendor, write_wrapper
    cfg = load_config(); _require(cfg)
    write_wrapper(cfg.paths.cosmos); d = vendor(cfg.paths.cosmos)
    from .hooks import install_hooks
    if install_hooks(cfg.paths.claude_settings):
        print(col("✓", "g"), "hooks refreshed in .claude/settings.json (restart open sessions to pick them up)")
    print(col("✓", "g"), f"vendored cosmos {__version__} → {d}")
    return 0


# ---------------------------------------------------------------- lanes · atlas · charter · horizon · gate
def cmd_lanes(a) -> int:
    from .lanes import assign_lanes, lane_report, propose
    cfg = load_config(); _require(cfg)
    mems = Ledger(cfg.paths).load()
    if a.propose:
        res = propose(cfg, mems, Observations(cfg.paths).iter_all(), use_llm=not a.no_llm)
        print(col(f"proposed lanes ({res['source']}):", "B"))
        for k, v in res["lanes"].items():
            print(f"  {k:<28} {', '.join(v)}")
        if res.get("note"):
            print(col("  " + res["note"], "d"))
        if a.write:
            cfg.data["lanes"] = res["lanes"]; cfg.save()
            n = assign_lanes(mems, cfg, only_missing=False); Ledger(cfg.paths).save_all(mems.values())
            from .render import render_all; render_all(cfg, mems)
            print(col("✓", "g"), f"written to .cosmos/config.json → lanes; {n} memories re-filed")
        else:
            print(col("  add --write to save into .cosmos/config.json and re-file every memory", "d"))
        return 0
    if assign_lanes(mems, cfg):
        Ledger(cfg.paths).save_all(mems.values())
    rows = lane_report(cfg, mems, Observations(cfg.paths).iter_all(), a.days)
    if a.json:
        print(json.dumps(rows, indent=1)); return 0
    if not rows:
        print(col("no lanes yet — facts and findings get a lane after `cosmos dream`", "d")); return 0
    print(col(f"{'lane':<28} {'facts':>5} {'open findings':>13}  contributors (last {a.days}d)", "d"))
    for r in rows:
        who = ", ".join(f"{c['name']} ({c['observations']})" for c in r["contributors"]) or "—"
        flag = col("  ⚠ overlap", "y") if r["overlap"] else ""
        print(f"{r['lane']:<28} {r['facts']:>5} {r['findings_open']:>13}  {who}{flag}")
    return 0


def cmd_atlas(a) -> int:
    from .atlas import build, check
    cfg = load_config(); _require(cfg)
    if a.check:
        r = check(cfg)
        if not r["exists"]:
            print(col("no atlas yet — run `cosmos atlas`", "y")); return 1
        if r["drift"] or r["missing"]:
            print(col(f"⚠ atlas drift: {len(r['drift'])} changed, {len(r['missing'])} missing since {r['generated']} @ {r['commit']}", "y"))
            for f in r["drift"][:15]: print("  changed ", f)
            for f in r["missing"][:15]: print("  missing ", f)
            print(col("  run `cosmos atlas` (deterministic) and /atlas in Claude Code (deep pass)", "d")); return 1
        print(col("✓", "g"), f"atlas in sync (generated {r['generated']} @ {r['commit']})"); return 0
    inv = build(cfg)
    print(col("✓", "g"), f"atlas → .cosmos/ledger/atlas/  ({len(inv['apps'])} apps · {len(inv['services'])} services · {len(inv['stores'])} stores · {len(inv['k8s'])} k8s objects · {len(inv['terraform'])} tf types · {sum(len(x['endpoints']) for x in inv['api'])} endpoints · {len(inv['env_keys'])} config keys)")
    print(col("  deeper pass: type /atlas in Claude Code", "d"))
    return 0


def cmd_charter(a) -> int:
    from .charter import add_section_rule, body, ensure, gate_config, path
    cfg = load_config(); _require(cfg)
    ensure(cfg)
    if a.action == "add":
        text = " ".join(a.text)
        add_section_rule(cfg, text, a.section)
        from .privacy import redact
        mems = Ledger(cfg.paths).load(); mid = make_id(text)
        from .config import git_author
        mems[mid] = mems.get(mid) or Memory(id=mid, text=redact(text)[0], category="convention", source="explicit", confidence=0.95, importance=0.95, authors=[git_author(cfg.paths.root)])
        _finish(cfg, mems)
        print(col("✓", "g"), f"added to charter ({a.section}) and ledger: {text}"); return 0
    if a.action == "edit":
        import os as _os
        editor = _os.environ.get("VISUAL") or _os.environ.get("EDITOR") or "nano"
        subprocess.call([editor, str(path(cfg))]); return 0
    if a.action == "gate":
        print(json.dumps(gate_config(cfg), indent=1)); return 0
    print(body(cfg)); return 0


def cmd_intake(a) -> int:
    from .intake import analyse, read_attachment, render_md, save
    from .config import git_author
    cfg = load_config(); _require(cfg)
    brief = Path(a.brief).read_text(errors="ignore") if a.brief else ""
    atts = [read_attachment(Path(x)) for x in (a.attach or []) if Path(x).exists()]
    res = analyse(cfg, " ".join(a.text), a.file, brief=brief, attachments=atts)
    if a.json:
        print(json.dumps({k: (v if not isinstance(v, list) or not v or not hasattr(v[0], "id") else [m.id for m in v]) for k, v in res.items()}, indent=1, default=str)); return 0
    print(render_md(res, git_author(cfg.paths.root)))
    if not a.no_save:
        p = save(cfg, res)
        print(col("✓", "g"), f"saved {p.relative_to(cfg.paths.root)}")
    return 0


def cmd_gate(a) -> int:
    from .charter import gate_config
    from .gate import evaluate, message
    cfg = load_config(); _require(cfg)
    if a.transcript:
        res = evaluate(cfg, {"transcript_path": a.transcript, "session_id": "manual"})
        print(message(res) if res["block"] else col("✓ gate would let this turn through", "g"))
        return 2 if res["block"] else 0
    gc = gate_config(cfg)
    print(col("GATE", "B"), "enabled" if gc.get("enabled", True) else col("disabled", "y"))
    print(f"  require tests   {gc.get('require_tests')}   patterns: {', '.join(gc.get('test_patterns', [])[:6])}…")
    print(f"  require refs    {gc.get('require_refs')}   (path/to/file.ext:line in the final summary)")
    print(f"  open findings on touched files must be addressed or deferred")
    print(col("  edit in .cosmos/charter.md (gate: {...}) or .cosmos/config.json → gate", "d"))
    return 0


# ---------------------------------------------------------------- audit
def _findings(cfg, a):
    from .audit import findings
    return findings(Ledger(cfg.paths).load(), getattr(a, "status", None), getattr(a, "severity", None))


def _find_finding(cfg, key: str) -> Optional[Memory]:
    mems = Ledger(cfg.paths).load()
    for m in mems.values():
        if m.category == "finding" and (m.id == key or m.meta.get("audit_id") == key or m.meta.get("audit_id", "").endswith("-" + key)):
            return m
    return _find({k: v for k, v in mems.items() if v.category == "finding"}, key)


def cmd_audit_import(a) -> int:
    from .audit import import_findings
    cfg = load_config(); _require(cfg)
    new, upd, reg = import_findings(cfg, Path(a.file), a.prefix, a.source or "")
    _finish(cfg, Ledger(cfg.paths).load())
    print(col("✓", "g"), f"imported {len(new)} new, {len(upd)} updated, {len(reg)} regressed finding(s) from {a.file}")
    for m in new[:10]:
        print(col("  +", "g"), f"{m.meta['audit_id']} [{m.meta['severity']}] {m.text}")
    for m in reg:
        print(col("  ⚠ REGRESSION", "r"), f"{m.meta['audit_id']} {m.text}")
    return 0


def cmd_audit_list(a) -> int:
    from .audit import SEV_ICON
    cfg = load_config(); _require(cfg)
    fs = _findings(cfg, a)
    if a.json:
        from .audit import export_json
        print(json.dumps(export_json(fs), indent=1, ensure_ascii=False)); return 0
    if not fs:
        print(col("no findings", "d")); return 0
    from .audit import CLOSED, NOTE, OPEN_LIKE
    st_ = [m.meta.get("finding_status", "open") for m in fs]
    print(col(f"open {sum(s in OPEN_LIKE for s in st_)} · closed {sum(s in CLOSED for s in st_)} · notes {sum(s == NOTE for s in st_)}", "d"))
    for m in fs:
        st = m.meta.get("finding_status", "open")
        print(f"{SEV_ICON.get(m.meta.get('severity'),'⚪')} {m.meta.get('audit_id','').ljust(12)} {m.meta.get('severity','').ljust(8)} "
              + (col(st.ljust(10), "y" if st in ("open", "regressed") else "d")) + f" {m.text}")
    return 0


def cmd_audit_show(a) -> int:
    cfg = load_config(); _require(cfg)
    m = _find_finding(cfg, a.id)
    if not m:
        print(col("no such finding", "r")); return 1
    print(col(f"{m.meta.get('audit_id')} · {m.meta.get('severity','').upper()} · {m.meta.get('finding_status','open')}", "B"))
    print(m.text)
    if m.meta.get("locations"):
        print(col("  where  ", "d") + m.meta["locations"])
    for label, text in m.details:
        print(f"\n  {col(label, 'B')}\n  {text}")
    print(col(f"\n  memory {m.id} · found at {m.meta.get('found_commit','?')} · verified {m.last_verified}" + (f" · fixed at {m.meta['fixed_commit']}" if m.meta.get("fixed_commit") else ""), "d"))
    if m.reason:
        print(col("  " + m.reason, "d"))
    return 0


def cmd_audit_set(new_status: str):
    def fn(a) -> int:
        from .audit import set_status
        cfg = load_config(); _require(cfg)
        m = _find_finding(cfg, a.id)
        if not m:
            print(col("no such finding", "r")); return 1
        set_status(cfg, m, new_status, " ".join(a.note or []))
        _finish(cfg, Ledger(cfg.paths).load())
        print(col("✓", "g"), f"{m.meta.get('audit_id')} → {new_status}")
        return 0
    return fn


def cmd_audit_export(a) -> int:
    from .audit import export_json
    cfg = load_config(); _require(cfg)
    data = export_json(_findings(cfg, a))
    if a.out:
        Path(a.out).write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n"); print(col("✓", "g"), f"wrote {len(data)} findings to {a.out}")
    else:
        print(json.dumps(data, indent=2, ensure_ascii=False))
    return 0


def cmd_audit_report(a) -> int:
    from .audit import report_markdown, report_slack
    cfg = load_config(); _require(cfg)
    fs = _findings(cfg, a)
    text = report_markdown(cfg, fs) if a.format == "md" else json.dumps(report_slack(cfg, fs), indent=1, ensure_ascii=False)
    if a.out:
        Path(a.out).write_text(text); print(col("✓", "g"), f"wrote {a.out}")
    else:
        print(text)
    return 0


def cmd_audit_slack(a) -> int:
    from .audit_slack import PostState, SlackClient, publish, validate_cards
    cfg = load_config(); _require(cfg)
    from .audit import findings
    from .audit import PUBLISHABLE
    fs = [m for m in findings(Ledger(cfg.paths).load(), None, a.severity) if m.meta.get("finding_status", "open") in PUBLISHABLE]
    state = PostState(cfg.paths.state / "slack-posted.json")
    if a.seed_state:
        n = state.seed_from(Path(a.seed_state), a.prefix); state.save()
        print(col("✓", "g"), f"seeded {n} already-posted id(s) from {a.seed_state}")
    if a.validate:
        errs = validate_cards(SlackClient(None), fs)
        for e in errs:
            print(col("✗", "r"), e)
        print(col("✓", "g") if not errs else col("!", "y"), f"{len(fs) - len(errs)}/{len(fs)} cards valid")
        return 1 if errs else 0
    if a.status:
        from .audit import NOTE
        pend = [m.meta.get("audit_id") for m in fs if not state.posted(m.meta.get("audit_id", m.id))]
        notes = sum(1 for m in fs if m.meta.get("finding_status") == NOTE)
        print(f"open {len(fs) - notes} · notes {notes} · posted {len(fs) - len(pend)} · pending {len(pend)}" + (": " + ", ".join(pend) if pend else ""))
        return 0
    channel = a.channel or os.environ.get("SLACK_CHANNEL") or ""
    if a.convert:
        from .audit_slack import convert
        if not channel:
            print(col("--channel (or SLACK_CHANNEL) is required", "r")); return 2
        return convert(cfg, fs, channel, a.dry, a.only, a.ts, state)
    if a.send and not channel:
        print(col("--channel (or SLACK_CHANNEL) is required to send", "r")); return 2
    res = publish(cfg, fs, channel, a.send, a.all, state)
    print(col("✓", "g"), f"{'posted' if a.send else 'previewed'} {res['posted'] if a.send else len(fs) - res['skipped']} · skipped {res['skipped']} already posted" + ("" if a.send else "   (add --send to publish)"))
    return 0


def cmd_audit_lint(a) -> int:
    from .audit_lint import config_from, lint
    cfg = load_config(); _require(cfg)
    lc = config_from(cfg.get("audit", {}) or {}, {"repo_base": a.repo_base, "crud_glob": a.crud_glob, "module_prefix": a.module_prefix, "roots": a.roots, "sys_path": a.sys_path})
    os.chdir(cfg.paths.root)
    issues = lint(lc)
    if a.json:
        print(json.dumps([i.__dict__ for i in issues], indent=1)); return 1 if issues else 0
    for i in issues:
        print(col("✗", "r"), i)
    print(col("✓ no suspect filter keys", "g") if not issues else col(f"{len(issues)} suspect filter key(s)", "y"))
    return 1 if issues else 0


# ---------------------------------------------------------------- parser
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="cosmos", description="Git-native shared engineering memory for AI coding agents.")
    p.add_argument("--version", action="version", version=f"cosmos {__version__}")
    sp = p.add_subparsers(dest="cmd", required=True)

    s = sp.add_parser("init", help="set up .cosmos/, hooks, CLAUDE.md/AGENTS.md block, Obsidian vault"); s.add_argument("path", nargs="?"); s.add_argument("--command", help="hook command override"); s.add_argument("--no-vendor", action="store_true", help="don't vendor cosmos into .cosmos/vendor (teammates must pip install)"); s.add_argument("--no-user-hooks", action="store_true", help="do not touch ~/.claude/settings.json"); s.add_argument("--no-seed", action="store_true", help="do not read past sessions or start the first dream"); s.add_argument("--no-branch", action="store_true", help="keep .cosmos/ tracked in the main tree instead of on its own branch"); s.set_defaults(fn=cmd_init)
    s = sp.add_parser("status", help="quick status"); s.add_argument("--json", action="store_true"); s.set_defaults(fn=cmd_status)
    s = sp.add_parser("hook", help="(internal) Claude Code hook entrypoint, reads event JSON on stdin"); s.set_defaults(fn=cmd_hook)
    s = sp.add_parser("capture", help="capture from session logs: Claude Code, Codex, Gemini/Antigravity"); s.add_argument("--transcript"); s.add_argument("--agent", default="all", choices=["all", "claude", "codex", "gemini"]); s.add_argument("-v", "--verbose", action="store_true"); s.add_argument("--rebuild-journal", action="store_true", help="re-read whole transcripts and write the journal for work done before cosmos was installed"); s.add_argument("--days", type=int, default=14, help="when reading whole transcripts, only turns from the last N days are read by the model (default 14)"); s.add_argument("--reread", action="store_true", help="start again from the beginning of every transcript (with --days, the model reads only recent turns)"); s.set_defaults(fn=cmd_capture)
    s = sp.add_parser("mcp", help="run the MCP server (stdio) — one point of contact for every agent"); s.set_defaults(fn=cmd_mcp)
    s = sp.add_parser("connect", help="wire agents to cosmos: instruction files + MCP configs"); s.add_argument("agents", nargs="*", default=["all"], choices=["all", "claude", "codex", "gemini", "cursor", "copilot", "cline", "windsurf"]); s.add_argument("--write-user", action="store_true", help="also write ~/.codex/config.toml"); s.set_defaults(fn=cmd_connect)
    s = sp.add_parser("sync", help="commit and push the cosmos branch (dreams and the watcher do this for you)"); s.add_argument("--push", action="store_true"); s.add_argument("-m", "--message"); s.set_defaults(fn=cmd_sync)
    s = sp.add_parser("watch", help="follow every agent's sessions on this machine (all worktrees, subagents; hooks not required)"); s.add_argument("--interval", type=int, default=30); s.add_argument("--once", action="store_true"); s.add_argument("--agent", choices=["all", "claude", "codex", "gemini"], default="all"); s.add_argument("--daemon", action="store_true", help=argparse.SUPPRESS); s.add_argument("--idle", type=int, default=120, help=argparse.SUPPRESS); s.set_defaults(fn=cmd_watch)
    s = sp.add_parser("hooks", help="install the Claude Code hooks at user level (~/.claude/settings.json) so any checkout or worktree is covered"); s.add_argument("--user", action="store_true", help="(default) user level"); s.set_defaults(fn=cmd_hooks)
    s = sp.add_parser("dream", help="consolidate observations into the ledger"); s.add_argument("--llm", action="store_true", help="force LLM refinement"); s.add_argument("--no-llm", action="store_true"); s.add_argument("--auto", action="store_true", help=argparse.SUPPRESS); s.add_argument("--recurate", action="store_true", help="ask the model to re-judge every existing fact against the current bar (keep · rewrite · retire)"); s.set_defaults(fn=cmd_dream)
    for name in ("ui", "ledger"):
        s = sp.add_parser(name, help="open the control room (overview · ledger · flares · dreams · verdicts · activity)"); s.add_argument("--port", type=int, default=7331, help="first port to try (default 7331; the next free one is used if busy)"); s.add_argument("--strict-port", action="store_true", help="fail instead of moving to the next free port"); s.add_argument("--static", action="store_true", help="write a read-only snapshot HTML instead of serving"); s.add_argument("--obsidian", action="store_true"); s.add_argument("--no-open", action="store_true"); s.set_defaults(fn=cmd_ledger)
    s = sp.add_parser("obsidian", help="prepare/open the ledger as an Obsidian vault"); s.add_argument("--open", action="store_true"); s.add_argument("--vault", help="link ledger into an existing vault"); s.set_defaults(fn=cmd_obsidian)
    s = sp.add_parser("remember", help="add an explicit memory"); s.add_argument("text", nargs="+"); s.add_argument("-c", "--category", default="convention", choices=["architecture", "decision", "convention", "constraint", "bug", "dependency", "workflow", "domain", "rejected", "finding"]); s.add_argument("-f", "--file", action="append"); s.set_defaults(fn=cmd_remember)
    s = sp.add_parser("forget", help="retire a memory"); s.add_argument("id"); s.add_argument("--hard", action="store_true", help="delete the note instead of marking forgotten"); s.set_defaults(fn=cmd_forget)
    s = sp.add_parser("verify", help="mark a memory verified today"); s.add_argument("id"); s.add_argument("--resolve", action="store_true", help="also supersede whatever it contradicts"); s.set_defaults(fn=cmd_verify)
    s = sp.add_parser("why", help="explain a memory: evidence, timeline, contradictions"); s.add_argument("query", nargs="+"); s.set_defaults(fn=cmd_why)
    s = sp.add_parser("search", help="rank memories for a query / file"); s.add_argument("query", nargs="*"); s.add_argument("-f", "--file", action="append"); s.add_argument("-k", type=int, default=8); s.add_argument("--json", action="store_true"); s.set_defaults(fn=cmd_search)
    s = sp.add_parser("review", help="list contradictions and stale candidates"); s.set_defaults(fn=cmd_review)
    s = sp.add_parser("health", help="memory quality metrics"); s.set_defaults(fn=cmd_health)
    s = sp.add_parser("render", help="rewrite CLAUDE.md/AGENTS.md block and ledger index"); s.set_defaults(fn=cmd_render)
    s = sp.add_parser("doctor", help="check the installation"); s.set_defaults(fn=cmd_doctor)
    s = sp.add_parser("uninstall", help="remove hooks from .claude/settings.json"); s.set_defaults(fn=cmd_uninstall)
    s = sp.add_parser("update", help="refresh the vendored copy in .cosmos/vendor from the installed cosmos"); s.set_defaults(fn=cmd_update)

    s = sp.add_parser("lanes", help="facts, findings and people per feature lane; flags overlap"); s.add_argument("--days", type=int, default=30); s.add_argument("--json", action="store_true"); s.add_argument("--propose", action="store_true", help="suggest a lanes mapping (LLM if configured, else from paths)"); s.add_argument("--write", action="store_true", help="with --propose: save to config and re-file"); s.add_argument("--no-llm", action="store_true"); s.set_defaults(fn=cmd_lanes)
    s = sp.add_parser("atlas", help="build architecture inventory + diagrams from the repo (or --check for drift)"); s.add_argument("--check", action="store_true"); s.set_defaults(fn=cmd_atlas)
    s = sp.add_parser("charter", help="the team's working agreement: show | add \"rule\" | edit | gate"); s.add_argument("action", nargs="?", default="show", choices=["show", "add", "edit", "gate"]); s.add_argument("text", nargs="*"); s.add_argument("--section", default="Architecture rules"); s.set_defaults(fn=cmd_charter)
    s = sp.add_parser("horizon", aliases=["intake"], help="map a feature before coding: lanes, collisions, findings, people"); s.add_argument("text", nargs="+"); s.add_argument("-f", "--file", action="append", help="folder or file it will touch (repeatable)"); s.add_argument("--attach", action="append", help="ad-hoc document to read as context (PRD, spec, notes)"); s.add_argument("--brief", help="text file with the brief"); s.add_argument("--json", action="store_true"); s.add_argument("--no-save", action="store_true"); s.set_defaults(fn=cmd_intake)
    s = sp.add_parser("gate", help="show Gate rules, or dry-run it on a transcript"); s.add_argument("--transcript"); s.set_defaults(fn=cmd_gate)

    au = sp.add_parser("flares", aliases=["audit"], help="QA / security findings (flares) as memory: import, track lifecycle, report, publish").add_subparsers(dest="audit_cmd", required=True)
    from .audit import FINDING_STATUSES as FST, SEVERITIES as SEVS
    x = au.add_parser("import", help="import findings JSON (id, severity, title, area, locations, sections)"); x.add_argument("file"); x.add_argument("--prefix", default="QA", help="stable id prefix, e.g. QA"); x.add_argument("--source", help="source document name"); x.set_defaults(fn=cmd_audit_import)
    x = au.add_parser("list", help="list findings"); x.add_argument("--status", choices=FST); x.add_argument("--severity", choices=SEVS); x.add_argument("--json", action="store_true"); x.set_defaults(fn=cmd_audit_list)
    x = au.add_parser("show", help="show one finding"); x.add_argument("id"); x.set_defaults(fn=cmd_audit_show)
    for name, status, help_ in (("fix", "fixed", "mark fixed (records HEAD commit)"), ("withdraw", "withdrawn", "not a bug / by design — kept so nobody re-files it"),
                                ("wontfix", "wontfix", "accepted risk"), ("reopen", "open", "reopen a closed finding"), ("claim", "claimed", "someone / the fix loop is on it"),
                                ("pr-open", "pr_open", "a PR is open for it"), ("needs-human", "needs_human", "could not reproduce or intent is ambiguous — a human decides")):
        x = au.add_parser(name, help=help_); x.add_argument("id"); x.add_argument("note", nargs="*"); x.set_defaults(fn=cmd_audit_set(status))
    x = au.add_parser("set", help="set any lifecycle status"); x.add_argument("id"); x.add_argument("status", choices=FST); x.add_argument("note", nargs="*"); x.set_defaults(fn=lambda a: cmd_audit_set(a.status)(a))
    x = au.add_parser("lint", help="flag repository filter keys that are not real model columns (AST; see docs/flares.md)"); x.add_argument("--repo-base"); x.add_argument("--crud-glob"); x.add_argument("--module-prefix"); x.add_argument("--roots", nargs="*"); x.add_argument("--sys-path", nargs="*"); x.add_argument("--json", action="store_true"); x.set_defaults(fn=cmd_audit_lint)
    x = au.add_parser("export", help="export findings JSON (same schema as import)"); x.add_argument("-o", "--out"); x.add_argument("--status", choices=FST); x.add_argument("--severity", choices=SEVS); x.set_defaults(fn=cmd_audit_export)
    x = au.add_parser("report", help="regenerate the audit report from the ledger"); x.add_argument("--format", choices=["md", "slack"], default="md"); x.add_argument("-o", "--out"); x.add_argument("--status", choices=FST); x.add_argument("--severity", choices=SEVS); x.set_defaults(fn=cmd_audit_report)
    x = au.add_parser("slack", help="publish open findings as Block Kit cards (dry run unless --send)"); x.add_argument("--send", action="store_true"); x.add_argument("--status", action="store_true", help="what is posted vs pending"); x.add_argument("--validate", action="store_true", help="blocks.validate every card (no token needed)"); x.add_argument("--all", action="store_true", help="repost everything"); x.add_argument("--channel"); x.add_argument("--seed-state", help="import a legacy .slack-posted.json"); x.add_argument("--prefix", default="QA"); x.add_argument("--severity", choices=SEVS)
    x.add_argument("--convert", action="store_true", help="rewrite already-posted messages in place as cards (chat.update)"); x.add_argument("--dry", action="store_true"); x.add_argument("--only", help="one audit id"); x.add_argument("--ts", help="message ts or permalink (skips channels:history)")
    x.set_defaults(fn=cmd_audit_slack)
    return p


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return int(args.fn(args) or 0)
    except KeyboardInterrupt:
        return 130
