"""`cosmos ui`: the local control room. One HTML app + a tiny stdlib JSON server on localhost.

Pages: Overview (live pipeline), Ledger (memory explorer), Flares (kanban by lifecycle), Dreams (execution history,
run a dream), Verdicts (contradictions / stale candidates / findings that need a human), Activity (observations, hook log).
Every action goes through POST /api/action and calls the same functions the CLI uses.
"""
from __future__ import annotations

import json
import threading
import webbrowser
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, List

from . import __version__
from .config import Config, git_author, git_head
from .store import Ledger, Memory, Observations, State, make_id, today


# ---------------------------------------------------------------- data
def _mem(m: Memory) -> Dict[str, Any]:
    return {"id": m.id, "text": m.text, "category": m.category, "status": m.status, "confidence": m.confidence, "importance": m.importance,
            "source": m.source, "created": m.created, "updated": m.updated, "last_verified": m.last_verified, "evidence_count": m.evidence_count,
            "files": m.files, "tags": m.tags, "authors": m.authors, "supersedes": m.supersedes, "superseded_by": m.superseded_by,
            "contradicts": m.contradicts, "related": m.related, "reason": m.reason, "meta": m.meta, "details": m.details}


def snapshot(cfg: Config) -> Dict[str, Any]:
    mems = Ledger(cfg.paths).load()
    state = State(cfg.paths)
    obs = list(Observations(cfg.paths).iter_all())
    pending = [o for o in obs if o.get("id") and not state.is_dreamed(o["id"])]
    runs: List[Dict] = []
    d = cfg.paths.state / "dreams"
    if d.exists():
        for p in sorted(d.glob("*.json"), reverse=True)[:50]:
            try:
                runs.append(json.loads(p.read_text()))
            except Exception:
                pass
    log = cfg.paths.log.read_text().splitlines()[-80:] if cfg.paths.log.exists() else []
    active = [m for m in mems.values() if m.status == "active"]
    fresh = sum(1 for m in active if (date.today() - date.fromisoformat(m.last_verified)).days <= 90) if active else 0
    settings = cfg.paths.claude_settings
    hooks = sorted(json.loads(settings.read_text()).get("hooks", {}).keys()) if settings.exists() else []
    hooks = [h for h in hooks if "cosmos" in settings.read_text()]
    from .atlas import check as atlas_check
    from .charter import body as charter_body, gate_config, rules as charter_rules
    from .intake import list_intakes
    from .lanes import lane_report
    atlas_dir = cfg.paths.ledger / "atlas"
    atlas_docs = {}
    if atlas_dir.exists():
        for name in ("inventory", "containers", "deployment", "api", "dependencies", "system-context", "data-flow", "lanes"):
            f = atlas_dir / f"{name}.md"
            if f.exists():
                atlas_docs[name] = f.read_text()
    return {
        "lanes": lane_report(cfg, mems, obs), "atlas": {"check": atlas_check(cfg), "docs": atlas_docs},
        "charter": {"body": charter_body(cfg), "rules": [_mem(m) for m in charter_rules(mems)], "gate": gate_config(cfg)},
        "intakes": list_intakes(cfg),
        "version": __version__, "repo": cfg.paths.root.name, "root": str(cfg.paths.root), "head": git_head(cfg.paths.root), "author": git_author(cfg.paths.root),
        "memories": [_mem(m) for m in mems.values()],
        "observations": sorted(obs, key=lambda o: o.get("ts", ""), reverse=True)[:300],
        "pending_observations": len(pending), "dreams": runs, "hooklog": log, "hooks": hooks,
        "sessions": len(state.data.get("sessions", {})), "agents": sorted({o.get("agent", "claude") for o in obs}),
        "health": {"total": len(mems), "active": len(active), "with_evidence": int(100 * sum(1 for m in active if m.files) / max(1, len(active))),
                   "fresh90": int(100 * fresh / max(1, len(active))), "contradicted": sum(1 for m in mems.values() if m.status == "contradicted"),
                   "stale": sum(1 for m in mems.values() if m.status == "stale-candidate"), "superseded": sum(1 for m in mems.values() if m.status == "superseded"),
                   "explicit": sum(1 for m in mems.values() if m.source == "explicit"), "findings": sum(1 for m in mems.values() if m.category == "finding")},
        "config": cfg.data,
    }


def act(cfg: Config, req: Dict[str, Any]) -> Dict[str, Any]:
    from .render import render_all
    t = req.get("type")
    ledger = Ledger(cfg.paths)
    mems = ledger.load()
    if t == "dream":
        from .dream import dream
        rep = dream(cfg, use_llm=req.get("llm"))
        render_all(cfg, ledger.load())
        return {"ok": True, "report": rep.to_dict()}
    if t == "atlas":
        from .atlas import build
        inv = build(cfg)
        return {"ok": True, "apps": len(inv["apps"]), "services": len(inv["services"]), "stores": len(inv["stores"])}
    if t in ("horizon", "intake"):
        from .intake import analyse, save
        text = " ".join(str(req.get("text", "")).split())
        if len(text) < 6:
            return {"ok": False, "error": "describe the feature in a sentence"}
        files = req.get("files") if isinstance(req.get("files"), list) else [f for f in str(req.get("files", "")).split() if f]
        atts = [{"name": str(a.get("name", "file"))[:120], "text": str(a.get("text", ""))[:200_000]} for a in (req.get("attachments") or []) if isinstance(a, dict)]
        res = analyse(cfg, text, files, brief=str(req.get("brief", ""))[:20_000], attachments=atts)
        p = save(cfg, res)
        return {"ok": True, "file": p.name}
    if t == "charter_add":
        from .charter import add_section_rule
        from .privacy import redact
        text = redact(" ".join(str(req.get("text", "")).split()))[0]
        if len(text) < 8:
            return {"ok": False, "error": "too short"}
        add_section_rule(cfg, text, str(req.get("section", "Architecture rules")))
        mid = make_id(text)
        mems[mid] = mems.get(mid) or Memory(id=mid, text=text, category="convention", source="explicit", confidence=0.95, importance=0.95, authors=[git_author(cfg.paths.root)])
        brain.save_all(mems.values()); render_all(cfg, mems)
        return {"ok": True}
    if t == "capture":
        from .adapters import find_claude_sessions
        from .hooks import capture
        n = sum(capture(cfg, {"transcript_path": str(p), "session_id": sid, "hook_event_name": "manual", "cwd": str(cfg.paths.root)}) for p, sid in find_claude_sessions(cfg.paths.root))
        return {"ok": True, "captured": n}
    if t == "remember":
        from .privacy import redact
        text, _ = redact(" ".join(str(req.get("text", "")).split()))
        if len(text) < 8:
            return {"ok": False, "error": "too short"}
        mid = make_id(text)
        m = mems.get(mid) or Memory(id=mid, text=text, category=req.get("category", "convention"), source="explicit", confidence=0.95, importance=0.95, authors=[git_author(cfg.paths.root)])
        m.status, m.updated, m.last_verified = "active", today(), today()
        mems[mid] = m
    elif t in ("verify", "forget", "keep", "both_valid", "reopen"):
        m = mems.get(req.get("id", ""))
        if not m:
            return {"ok": False, "error": "no such memory"}
        if t == "verify":
            m.status, m.last_verified, m.updated = "active", today(), today()
            m.confidence = min(0.99, m.confidence + 0.1)
            m.reason = f"Verified in UI by {git_author(cfg.paths.root)} on {today()}"
        elif t == "forget":
            m.status, m.updated, m.reason = "forgotten", today(), f"Forgotten in UI by {git_author(cfg.paths.root)} on {today()}"
        elif t == "reopen":
            m.status, m.updated, m.reason = "active", today(), f"Reopened in UI on {today()}"
        elif t == "keep":       # keep this one, supersede the other side of the contradiction
            other = mems.get(req.get("drop", ""))
            m.status, m.last_verified, m.updated = "active", today(), today()
            m.contradicts = [c for c in m.contradicts if c != (other.id if other else None)]
            if other:
                other.status, other.superseded_by, other.updated = "superseded", m.id, today()
                other.reason = f"Superseded on {today()}: team kept [[{m.id}]]" + (f" — {req['note']}" if req.get("note") else "")
                other.contradicts = [c for c in other.contradicts if c != m.id]
                m.supersedes = other.id
            m.reason = f"Kept over {other.id if other else '?'} on {today()}"
        elif t == "both_valid":
            other = mems.get(req.get("other", ""))
            for a, b in ((m, other), (other, m)):
                if a is None:
                    continue
                a.status, a.updated = "active", today()
                a.contradicts = [c for c in a.contradicts if b is None or c != b.id]
                a.reason = f"Reviewed {today()}: both valid" + (f" — {req['note']}" if req.get("note") else "")
    elif t == "finding_status":
        from .audit import set_status
        m = mems.get(req.get("id", ""))
        if not m:
            return {"ok": False, "error": "no such finding"}
        try:
            set_status(cfg, m, str(req.get("status")), str(req.get("note", "")))
        except SystemExit as e:
            return {"ok": False, "error": str(e)}
        render_all(cfg, ledger.load())
        return {"ok": True}
    else:
        return {"ok": False, "error": f"unknown action {t}"}
    ledger.save_all(mems.values())
    render_all(cfg, mems)
    return {"ok": True}


# ---------------------------------------------------------------- server
class _Handler(BaseHTTPRequestHandler):
    cfg: Config = None  # type: ignore
    html: str = ""

    def log_message(self, *a):  # quiet
        pass

    def _send(self, code: int, body: bytes, ctype: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.startswith("/api/state"):
            self._send(200, json.dumps(snapshot(self.cfg), ensure_ascii=False, default=str).encode(), "application/json")
        elif self.path.startswith("/api/tree"):
            import urllib.parse
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            rel = (q.get("path", [""])[0] or "").strip("/")
            root = self.cfg.paths.root.resolve()
            target = (root / rel).resolve() if rel else root
            if not str(target).startswith(str(root)) or not target.is_dir():
                self._send(404, b"[]", "application/json"); return
            skip = {".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build", ".cosmos", ".next", "target", ".idea"}
            items = []
            for e in sorted(target.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
                if e.name in skip or (e.name.startswith(".") and e.is_dir()):
                    continue
                items.append({"name": e.name, "dir": e.is_dir(), "path": str(e.relative_to(root))})
                if len(items) >= 300:
                    break
            self._send(200, json.dumps(items).encode(), "application/json")
        elif self.path.startswith("/api/note/"):
            mid = self.path.rsplit("/", 1)[-1]
            for p in self.cfg.paths.ledger.rglob(f"{mid}-*.md"):
                self._send(200, p.read_bytes(), "text/markdown; charset=utf-8"); return
            self._send(404, b"not found", "text/plain")
        else:
            self._send(200, self.html.encode(), "text/html; charset=utf-8")

    def do_POST(self):
        n = int(self.headers.get("Content-Length", "0"))
        try:
            req = json.loads(self.rfile.read(n) or b"{}")
            # loopback only, same-origin app; still refuse anything not from our page
            if self.headers.get("Origin") and not self.headers["Origin"].startswith("http://127.0.0.1") and not self.headers["Origin"].startswith("http://localhost"):
                self._send(403, b"{}", "application/json"); return
            res = act(self.cfg, req)
        except Exception as e:  # report, never crash the server
            res = {"ok": False, "error": str(e)}
        self._send(200, json.dumps(res, ensure_ascii=False, default=str).encode(), "application/json")


def write_html(cfg: Config) -> Path:
    out = cfg.paths.state / "ui.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(HTML.replace("__REPO__", cfg.paths.root.name).replace("__VERSION__", __version__))
    return out


def serve(cfg: Config, port: int = 7331, open_browser: bool = True, strict_port: bool = False) -> None:
    """Serve this repo's console. If the port is taken (another repo's console, usually) the next free one is used."""
    import errno
    _Handler.cfg = cfg
    _Handler.html = write_html(cfg).read_text()
    srv = None
    for p in range(port, port + 20):
        try:
            srv = ThreadingHTTPServer(("127.0.0.1", p), _Handler)
            break
        except OSError as e:
            if e.errno not in (errno.EADDRINUSE, 48, 98) or strict_port:
                raise SystemExit(f"port {p} is in use (another `cosmos ui`?). Pick one with --port.")
    if srv is None:
        raise SystemExit(f"no free port between {port} and {port + 19}; pass --port")
    port = srv.server_address[1]
    url = f"http://127.0.0.1:{port}/"
    print(f"cosmos ui · {cfg.paths.root.name} → {url}   (ctrl-c to stop)", flush=True)
    if open_browser:
        threading.Timer(0.4, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()


# ---------------------------------------------------------------- app
HTML = r"""<!doctype html><html lang="en"><head><meta charset="utf-8"><title>cosmos · __REPO__</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 viewBox=%270 0 64 64%27%3E%3Crect width=%2764%27 height=%2764%27 rx=%2712%27 fill=%27%23050506%27/%3E%3Cline x1=%2732%27 y1=%276%27 x2=%2732%27 y2=%2758%27 stroke=%27%23ECEAE4%27 stroke-width=%271.5%27/%3E%3Ccircle cx=%2732%27 cy=%2732%27 r=%2715%27 fill=%27%23050506%27 stroke=%27%23ECEAE4%27 stroke-width=%271.6%27/%3E%3Ccircle cx=%2732%27 cy=%2732%27 r=%279%27 fill=%27none%27 stroke=%27%23E8CFA0%27 stroke-width=%271.6%27/%3E%3C/svg%3E">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;1,400&family=DM+Sans:wght@300;400;500&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
/* Theme: cosmic — near-black ground, thin light type, one warm rim-light accent. Matches the site. Single theme. */
:root{--bg:#050506;--bg2:#0a0a0c;--panel:#0d0d10;--panel2:#141418;--line:#1f2024;--fg:#ECEAE4;--mut:#9A998F;--dim:#5C5B58;
--acc:#E8CFA0;--acc2:#F4E4C4;--ok:#9CC9B0;--warn:#E8CFA0;--bad:#D89A9A;--info:#9FB8D0;
--navy:#050506;--navy2:#121216;--ivory:#ECEAE4;--brass:#E8CFA0;--brass2:#F4E4C4;--emerald:#E8CFA0;--sage:#9CC9B0;--dusty:#9FB8D0;
--architecture:#9FB8D0;--decision:#C7B3E6;--convention:#9CC9B0;--constraint:#D89A9A;--bug:#E2B48C;--dependency:#E8CFA0;--workflow:#8FD0D6;--domain:#B9D48C;--rejected:#8A8984;--finding:#D89A9A;
--critical:#D89A9A;--high:#E2B48C;--medium:#E8CFA0;--low:#9FB8D0;--note:#C7B3E6;--info-sev:#8A8984;
--r:4px;--shadow:none;color-scheme:dark}
*{box-sizing:border-box}html,body{height:100%}
body{margin:0;background:var(--bg);color:var(--fg);font:14px/1.55 "DM Sans","Inter",-apple-system,"Segoe UI",sans-serif;font-weight:300;-webkit-font-smoothing:antialiased}
h1,h2,h3,.logo,.kpi,.node .k,.node .t,.run .when,.fs b,.stat b{font-family:"Cormorant Garamond",Georgia,serif;font-weight:400}
a{color:var(--acc)}code,.mono,pre{font-family:"IBM Plex Mono",ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12px}
code{background:var(--panel2);padding:1px 6px;border-radius:3px;color:var(--acc2)}
#app{display:grid;grid-template-columns:232px 1fr;height:100vh}
nav{background:var(--bg);padding:22px 14px;display:flex;flex-direction:column;gap:2px;color:var(--fg)}
.logo{display:flex;align-items:center;gap:0;padding:6px 8px 24px;font-size:24px;letter-spacing:.38em;color:var(--fg);font-weight:400;font-family:"Cormorant Garamond",serif}
.logo .dot{display:inline-block;width:12px;height:22px;border-radius:0;background:none;position:relative;margin:0 .05em 0 .08em;order:1}
.logo .dot:before{content:"";position:absolute;left:5.5px;top:-7px;bottom:-7px;width:1px;background:var(--fg)}
.logo .dot:after{content:"";position:absolute;left:0.5px;top:5px;width:10px;height:10px;border:1px solid var(--fg);border-radius:50%;background:var(--bg)}
.logo small{display:block;font-family:"DM Sans",sans-serif;font-weight:400;color:var(--mut);font-size:9.5px;letter-spacing:.3em;text-transform:uppercase;margin-top:2px}
nav button{all:unset;display:flex;justify-content:space-between;align-items:center;padding:8px 12px;border-radius:4px;color:rgba(248,244,232,.78);cursor:pointer;font-weight:600;font-size:14px}
nav button:hover{background:var(--navy2);color:var(--ivory)}nav button.on{background:var(--navy2);color:var(--ivory);box-shadow:inset 3px 0 0 var(--brass2)}
nav .lb{display:inline-flex;align-items:center;gap:10px}
nav i[data-ic]{display:inline-grid;place-items:center;width:18px;height:18px}
nav i[data-ic] svg{width:17px;height:17px;stroke:currentColor;fill:none;stroke-width:1.2;stroke-linecap:round;stroke-linejoin:round;opacity:.9}
nav button.on i[data-ic] svg{stroke:var(--acc);opacity:1}
nav .n{font-size:10.5px;background:var(--panel);border:1px solid transparent;padding:1px 8px;border-radius:999px;color:var(--mut);letter-spacing:0}
nav .n.bad{color:var(--bad)}nav .n.warn{color:var(--warn)}
nav .foot{margin-top:auto;color:rgba(248,244,232,.6);font-size:11px;padding:8px}
main{overflow:auto;padding:22px 28px 40px}
header.top{display:flex;align-items:center;gap:14px;margin-bottom:18px}
header.top h1{font-size:34px;margin:0;font-weight:400;color:var(--fg);letter-spacing:.02em}header.top .sub{color:var(--mut);font-size:13px}
.spacer{flex:1}
.btn{all:unset;cursor:pointer;padding:8px 14px;border-radius:999px;background:var(--panel);border:1px solid transparent;color:var(--fg);font-weight:400;font-size:11.5px;letter-spacing:.18em;text-transform:uppercase;display:inline-flex;gap:8px;align-items:center}
.btn:hover{background:var(--panel2)}.btn.primary{border-color:var(--acc);color:var(--acc2);background:transparent}.btn.primary:hover{background:rgba(232,207,160,.08)}
.btn.ok{color:var(--ok)}.btn.bad{color:var(--bad)}.btn.warn{color:var(--warn)}.btn.sm{padding:5px 10px;font-size:12px;font-weight:500}
.btn[disabled]{opacity:.5;cursor:default}
.grid{display:grid;gap:14px}.g3{grid-template-columns:repeat(3,1fr)}.g4{grid-template-columns:repeat(4,1fr)}.g2{grid-template-columns:1fr 1fr}
@media(max-width:1100px){.g4{grid-template-columns:repeat(2,1fr)}.g3{grid-template-columns:1fr 1fr}}
.card{background:var(--panel);border-radius:6px;padding:22px 24px}
.card h3{margin:0 0 12px;font-size:10.5px;color:var(--mut);font-weight:400;text-transform:uppercase;letter-spacing:.26em;font-family:"DM Sans",sans-serif}
.kpi{font-size:44px;font-weight:400;letter-spacing:0;color:var(--fg)}.kpi small{font-size:12px;color:var(--mut);font-weight:500;margin-left:6px}
.badge{display:inline-block;padding:1px 8px;border-radius:999px;font-size:10.5px;font-weight:400;letter-spacing:.08em;border:1px solid transparent;color:var(--mut);white-space:nowrap;background:var(--panel2)}
.badge.cat{background:color-mix(in srgb,var(--c) 14%,transparent);color:var(--c)}
.badge.active{color:var(--ok)}.badge.contradicted{color:var(--bad)}.badge.stale-candidate{color:var(--warn)}.badge.superseded,.badge.forgotten{color:var(--dim);text-decoration:line-through}
.badge.sev{background:color-mix(in srgb,var(--c) 14%,transparent);color:var(--c)}
.muted{color:var(--mut)}.dim{color:var(--dim)}.small{font-size:12px}
input,select,textarea{background:var(--bg);border:1px solid var(--line);color:var(--fg);border-radius:6px;padding:9px 12px;font:inherit}
input::placeholder{color:var(--dim)}
input:focus,select:focus,textarea:focus{outline:none;border-color:var(--acc)}
.row{display:flex;gap:10px;align-items:center;flex-wrap:wrap}
/* flow */
.flow{display:grid;grid-template-columns:1fr 34px 1fr 34px 1fr 34px 1fr 34px 1fr;gap:0;align-items:center}
.node{padding:16px 10px;text-align:center;align-self:stretch}
.node .t{font-size:11px;letter-spacing:.26em;text-transform:uppercase;color:var(--mut);font-family:"DM Sans",sans-serif}.node .k{font-size:34px;margin:6px 0;color:var(--fg)}.node .d{color:var(--mut);font-size:12px}
.node.hot .k{color:var(--acc)}
.arrow{height:1px;margin:0 4px;background:repeating-linear-gradient(90deg,var(--acc) 0 6px,transparent 6px 12px);animation:flow 1.4s linear infinite;position:relative;opacity:.8}
.arrow:after{content:"";position:absolute;right:-1px;top:-3px;width:5px;height:5px;border-radius:50%;background:var(--acc)}
@keyframes flow{to{background-position:14px 0}}
/* memory list */
.mem{background:var(--panel);border-left:2px solid var(--c);border-radius:6px;padding:12px 14px;margin-bottom:8px;cursor:pointer}
.mem:hover{background:var(--panel2)}.mem .t{font-weight:600}.mem .m{display:flex;gap:8px;flex-wrap:wrap;margin-top:6px;color:var(--mut);font-size:12px;align-items:center}
.split{display:grid;grid-template-columns:1fr 420px;gap:16px;align-items:start}
@media(max-width:1000px){.split{grid-template-columns:1fr}}
.sticky{position:sticky;top:0}
dl{display:grid;grid-template-columns:120px 1fr;gap:6px 10px;margin:10px 0}dt{color:var(--mut)}dd{margin:0}
.chips{display:flex;gap:6px;flex-wrap:wrap}.chip{padding:4px 10px;border-radius:999px;border:1px solid transparent;color:var(--mut);cursor:pointer;font-size:12px;background:var(--panel)}
.chip.on{color:var(--fg);border-color:var(--acc)}
/* kanban */
.board{display:grid;grid-auto-flow:column;grid-auto-columns:minmax(250px,1fr);gap:12px;overflow-x:auto;padding-bottom:10px}
.col{padding:0 4px;min-height:300px}
.col h4{margin:2px 6px 10px;font-size:12px;text-transform:uppercase;letter-spacing:.6px;color:var(--mut);display:flex;justify-content:space-between}
.fcard{background:var(--panel);border-radius:6px;padding:10px 12px;margin-bottom:8px;cursor:pointer;border-left:2px solid var(--c)}
.fcard:hover{background:var(--panel2)}.fcard code,.mem code{display:inline-block;max-width:100%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;vertical-align:bottom}.fcard .id{font-size:11px;color:var(--mut)}.fcard .t{font-weight:600;font-size:13px;margin:2px 0}
/* dreams */
.run{display:grid;grid-template-columns:170px 1fr auto;gap:14px;align-items:center;padding:14px 16px;border-radius:6px;background:var(--panel);margin-bottom:8px;cursor:pointer}
.run:hover{background:var(--panel2)}.run .when{font-weight:600}.run .stats{display:flex;gap:14px;color:var(--mut);font-size:12px;flex-wrap:wrap}.run .stats b{color:var(--fg)}
.pill{display:inline-flex;align-items:center;gap:6px;padding:4px 10px;border-radius:999px;background:var(--panel2);font-size:12px;color:var(--fg)}
/* verdicts */
.pair{display:grid;grid-template-columns:1fr 60px 1fr;gap:12px;align-items:center;margin-bottom:12px}
.side{background:var(--panel);border-radius:6px;padding:16px}.vs{text-align:center;color:var(--dim)}
.actions{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px}
/* activity */
.ev{display:grid;grid-template-columns:110px 1fr;gap:12px;padding:10px 0;font-size:13px}
.ev .ts{color:var(--dim);font-family:ui-monospace,Menlo,monospace;font-size:11px}
pre.log{background:var(--panel);color:var(--mut);border-radius:6px;padding:12px;max-height:320px;overflow:auto;font-size:11.5px}
.empty{padding:40px;text-align:center;color:var(--dim);border:1px dashed var(--line);border-radius:var(--r)}
.toast{position:fixed;bottom:20px;right:20px;background:var(--panel2);color:var(--fg);border:1px solid var(--acc);padding:10px 14px;border-radius:10px;box-shadow:var(--shadow);opacity:0;transition:.3s}
.toast.show{opacity:1}
.sect{margin-top:10px}.sect b{display:block;color:var(--fg)}
canvas#graph{width:100%;height:280px;display:block;border-radius:10px;background:var(--bg2);border:1px solid var(--line)}
.docs{display:grid;grid-template-columns:210px minmax(0,1fr);gap:20px;align-items:start}
@media(max-width:900px){.docs{grid-template-columns:1fr}.toc{position:static;flex-direction:row;flex-wrap:wrap}}
.doc{min-width:0}.doc pre{max-width:100%;white-space:pre-wrap;word-break:break-word}
.toc{position:sticky;top:0;display:flex;flex-direction:column;gap:2px}.toc a{color:var(--mut);text-decoration:none;padding:6px 10px;border-radius:8px;font-size:13px}.toc a:hover{background:var(--panel);color:var(--fg)}
.doc{max-width:860px}.doc h2{font-size:26px;margin:40px 0 10px;color:var(--fg)}.doc h2:first-child{border:0;margin-top:0}
.doc p,.doc li{color:var(--fg);line-height:1.6}.doc pre{background:var(--panel);color:var(--fg);border:1px solid var(--line);border-radius:var(--r);padding:12px 14px;overflow:auto;font-size:12.5px;line-height:1.5}
.doc table{border-collapse:collapse;width:100%;font-size:13px;margin:8px 0}.doc th,.doc td{text-align:left;padding:8px 10px;vertical-align:top}.doc tr+tr td{border-top:1px solid var(--line)}.doc th{color:var(--mut);font-weight:600}
.step{display:grid;grid-template-columns:34px 1fr;gap:12px;margin:10px 0}.step .no{width:28px;height:28px;border-radius:50%;border:1px solid var(--acc);color:var(--acc);background:transparent;font-weight:700;display:grid;place-items:center;font-size:13px}
.callout{border-left:1px solid var(--acc);background:var(--panel);padding:10px 14px;border-radius:8px;margin:10px 0;color:#c9d0dd}
.lanerow{display:grid;grid-template-columns:1.2fr .5fr .7fr 1.6fr;gap:12px;padding:14px 16px;border-radius:6px;background:var(--panel);margin-bottom:8px;align-items:center}
.lanerow.ov{box-shadow:inset 2px 0 0 var(--acc)}.lanerow .ln{font-weight:700}.lanerow .who{display:flex;gap:6px;flex-wrap:wrap}
.person{padding:2px 9px;border-radius:999px;background:var(--panel2);font-size:12px}
.mmd{background:var(--panel);border-radius:6px;padding:14px;overflow:auto;margin-top:8px}.mmd svg{max-width:100%;height:auto}
.mdtxt{white-space:pre-wrap;font-size:13px;line-height:1.55;color:var(--fg)}.mdtxt h1,.mdtxt h2,.mdtxt h3{font-size:20px;color:var(--fg);margin:14px 0 4px;font-family:"Cormorant Garamond",serif;font-weight:400}
.tabs{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:12px}
.charter{white-space:pre-wrap;font-size:14px;line-height:1.7;background:var(--panel);border-radius:6px;padding:24px 28px;color:var(--fg)}
.charter h2,.charter h1{font-size:22px;color:var(--fg);margin:20px 0 4px;font-weight:400;font-family:"Cormorant Garamond",serif}
.intk{background:var(--panel);border-radius:6px;padding:12px 14px;margin-bottom:8px;cursor:pointer}.intk:hover{background:var(--panel2)}
.lead{font-family:"Cormorant Garamond",serif;font-size:30px;line-height:1.25;font-weight:400;color:var(--fg);max-width:34ch;margin:4px 0 26px}.lead b{font-weight:400;color:var(--acc2)}
.acts{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}
@media(max-width:760px){.acts{grid-template-columns:1fr}}
.act{display:grid;grid-template-rows:auto auto 1fr auto;gap:6px;background:var(--panel);border-radius:6px;padding:22px 24px;min-height:190px}
.act .k{font-family:"Cormorant Garamond",serif;font-size:56px;line-height:1;color:var(--fg)}
.act .btn{justify-self:start;margin-top:10px}
.act.warn .k{color:var(--acc)}.act.bad .k{color:var(--bad)}.act.ok .k{color:var(--dim)}
.act .t{font-size:11px;letter-spacing:.24em;text-transform:uppercase;color:var(--fg)}.act .d{font-size:13px;color:var(--mut);line-height:1.5}
.flowline{display:flex;align-items:center;gap:14px;flex-wrap:wrap;margin-top:22px;color:var(--mut);font-size:12.5px;letter-spacing:.04em}
.flowline b{color:var(--fg);font-family:"Cormorant Garamond",serif;font-size:20px;margin-right:4px}.flowline i{flex:0 0 26px;height:1px;background:var(--acc);opacity:.6}
h3.sec{font-family:"Cormorant Garamond",serif;font-size:22px;font-weight:400;color:var(--fg);margin:0 0 10px}
.mem.quiet .t{font-size:13.5px}
.lanemini{display:grid;grid-template-columns:1fr 120px auto;gap:12px;align-items:center;padding:9px 0;font-size:13px}
.lanemini .ln{color:var(--fg)}.lanemini .bar{height:2px;background:var(--panel2);border-radius:1px;overflow:hidden}.lanemini .bar i{display:block;height:100%;background:var(--acc)}.lanemini .n{color:var(--mut);font-size:12px;white-space:nowrap}
.dreamflow{background:var(--panel);border-radius:6px;padding:26px 28px 22px;margin-bottom:18px}
.dfhead{display:flex;justify-content:space-between;align-items:baseline;gap:12px;flex-wrap:wrap;margin-bottom:26px}
.dsteps{display:grid;grid-template-columns:repeat(7,1fr);gap:0;position:relative}
@media(max-width:1100px){.dsteps{grid-template-columns:repeat(4,1fr);row-gap:28px}.dstep:nth-child(4n) .dline{display:none}}
@media(max-width:640px){.dsteps{grid-template-columns:repeat(2,1fr)}.dstep:nth-child(2n) .dline{display:none}.dstep:nth-child(4n) .dline{display:none}}
.dstep{position:relative;text-align:center;padding:0 8px}
.dline{position:absolute;top:22px;left:50%;right:-50%;height:1px;background:linear-gradient(90deg,var(--line2),var(--line2))}
.dstep:last-child .dline{display:none}
.dstep.lit .dline{background:linear-gradient(90deg,var(--acc),var(--line2))}
.dnode{position:relative;z-index:1;width:44px;height:44px;margin:0 auto;border-radius:50%;border:1px solid var(--line2);background:var(--panel);display:grid;place-items:center}
.dnode svg{width:20px;height:20px;stroke:var(--fg);fill:none;stroke-width:1.1;stroke-linecap:round;stroke-linejoin:round;opacity:.85}
.dstep.lit .dnode{border-color:var(--acc)}.dstep.lit .dnode svg{stroke:var(--acc2);opacity:1}
.dstep.llm .dnode{box-shadow:0 0 0 6px rgba(232,207,160,.06),0 0 30px -8px rgba(232,207,160,.5)}
.dnum{font-family:"Cormorant Garamond",serif;font-size:13px;color:var(--dim);margin-top:12px;letter-spacing:.2em}
.dt{font-family:"Cormorant Garamond",serif;font-size:19px;color:var(--fg);margin-top:2px;line-height:1.15}
.dstep.llm .dt{color:var(--acc2)}
.dd{font-size:11.5px;color:var(--mut);margin-top:6px;line-height:1.45;min-height:34px}
.dv{font-family:"Cormorant Garamond",serif;font-size:26px;color:var(--fg);margin-top:8px;line-height:1}.dv span{display:block;font-family:"DM Sans",sans-serif;font-size:10.5px;letter-spacing:.2em;text-transform:uppercase;color:var(--dim);margin-top:4px}
.stats2{display:grid;grid-template-columns:repeat(5,1fr);gap:14px}
@media(max-width:1000px){.stats2{grid-template-columns:repeat(3,1fr)}}@media(max-width:600px){.stats2{grid-template-columns:1fr 1fr}}
.stat2{background:var(--panel);border-radius:6px;padding:20px 22px 18px}
.stat2 .v{font-family:"Cormorant Garamond",serif;font-size:44px;line-height:1;color:var(--fg);overflow-wrap:anywhere}.stat2 .v.txt{font-size:26px;line-height:1.1;padding-top:8px;text-transform:lowercase;letter-spacing:.02em}.stat2.warn .v{color:var(--acc)}
.stat2 .l{font-size:10.5px;letter-spacing:.24em;text-transform:uppercase;color:var(--mut);margin-top:10px}.stat2 .s{font-size:12px;color:var(--dim);margin-top:4px}
.day{margin-bottom:18px}.dayhead{display:flex;justify-content:space-between;font-family:"Cormorant Garamond",serif;font-size:17px;color:var(--fg2);padding:0 0 6px;margin-bottom:4px;border-bottom:1px solid var(--line)}
.hooklist{display:grid;gap:6px}.hook{display:grid;grid-template-columns:auto 1fr auto;gap:12px;align-items:center;background:var(--panel);border-radius:6px;padding:10px 14px}
.hook .dot{width:8px;height:8px;border-radius:50%;background:var(--dim)}.hook.on .dot{background:var(--acc);box-shadow:0 0 12px -2px var(--acc)}
.hook .hn{font-family:ui-monospace,"IBM Plex Mono",monospace;font-size:12.5px;color:var(--fg)}.hook .hd{font-size:11.5px;color:var(--mut)}.hook .hs{font-size:10px;letter-spacing:.2em;text-transform:uppercase;color:var(--dim)}.hook.on .hs{color:var(--acc)}
.kinds{display:grid;gap:8px}.kind{display:grid;grid-template-columns:120px 1fr auto;gap:12px;align-items:center;font-size:12px}
.kind .bar{height:2px;background:var(--panel2);border-radius:1px;overflow:hidden}.kind .bar i{display:block;height:100%}.kind .n{color:var(--mut);font-family:"Cormorant Garamond",serif;font-size:18px}
.dreamflow.compact{padding:20px 22px 18px;margin:18px 0}
.dreamflow.compact .dnode{width:36px;height:36px}.dreamflow.compact .dnode svg{width:16px;height:16px}.dreamflow.compact .dline{top:18px}
.dreamflow.compact .dt{font-size:16px}.dreamflow.compact .dd{font-size:11px;min-height:30px}.dreamflow.compact .dv{font-size:20px}.dreamflow.compact .dnum{margin-top:8px}
.toolbar{background:var(--panel);border-radius:6px;padding:16px 18px;display:grid;gap:12px;margin-bottom:16px}
.trow{display:grid;grid-template-columns:64px 1fr auto;gap:12px;align-items:center}.tl{font-size:10.5px;letter-spacing:.24em;text-transform:uppercase;color:var(--dim)}
.composer{display:grid;grid-template-columns:auto 1fr auto auto;gap:0;align-items:center;background:var(--bg);border:1px solid var(--line);border-radius:999px;padding:4px 6px 4px 14px}
.composer svg{width:18px;height:18px;stroke:var(--dim);fill:none;stroke-width:1.2;margin-right:10px}
.composer input{border:0;background:transparent;padding:9px 6px;min-width:0}.composer input:focus{outline:none}
.composer select{border:0;border-left:1px solid var(--line);border-radius:0;background:transparent;padding:8px 30px 8px 14px;color:var(--mut);appearance:none;-webkit-appearance:none;background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='10' height='6' viewBox='0 0 10 6'><path d='M1 1l4 4 4-4' fill='none' stroke='%238A8984' stroke-width='1.2'/></svg>");background-repeat:no-repeat;background-position:right 12px center}
.composer .btn{margin-left:6px}
select{appearance:none;-webkit-appearance:none;padding-right:30px;background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='10' height='6' viewBox='0 0 10 6'><path d='M1 1l4 4 4-4' fill='none' stroke='%238A8984' stroke-width='1.2'/></svg>");background-repeat:no-repeat;background-position:right 12px center}
.intakeform{display:grid;grid-template-columns:1fr 1fr;gap:18px;background:var(--panel);border-radius:6px;padding:20px 22px}
@media(max-width:900px){.intakeform{grid-template-columns:1fr}}
.ifcol .tl{display:block}
.drop{display:grid;grid-template-columns:auto 1fr;gap:14px;align-items:center;border:1px dashed var(--line2);border-radius:6px;padding:14px 16px;color:var(--fg2);font-size:13px}
.drop.over{border-color:var(--acc);background:rgba(232,207,160,.05)}.drop svg{width:22px;height:22px;stroke:var(--mut);fill:none;stroke-width:1.2}
.browser{background:var(--bg);border:1px solid var(--line);border-radius:6px;padding:10px 12px;max-height:290px;overflow:auto}
.crumbs{font-size:12px;color:var(--mut);margin-bottom:8px;position:sticky;top:0;background:var(--bg);padding-bottom:6px}.crumbs a{color:var(--acc);text-decoration:none}
.treelist{display:grid;gap:2px}.titem{display:grid;grid-template-columns:18px 1fr;gap:8px;align-items:center;font-size:13px;padding:3px 4px;border-radius:4px}.titem:hover{background:var(--panel)}.titem.on{color:var(--acc2)}
.titem a{color:var(--fg);text-decoration:none}.titem.on a{color:var(--acc2)}.tpick{cursor:pointer;color:var(--dim);text-align:center}.titem.on .tpick{color:var(--acc)}
.readonly{display:none;background:var(--panel);border:1px solid var(--acc);padding:8px 12px;border-radius:10px;color:var(--warn);margin-bottom:12px;font-size:13px}
</style></head><body>
<div id="app">
<nav>
 <div class="logo"><div><span>cosm</span><span class="dot"></span><span>s</span><small id="repo">__REPO__</small></div></div>
<script>
const ICONS={
 overview:'<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>',
 ledger:'<path d="M4 4h11a3 3 0 0 1 3 3v13H7a3 3 0 0 0-3 3z"/><path d="M4 4v16"/><path d="M8 9h6M8 13h6"/>',
 lanes:'<path d="M4 4v16M12 4v16M20 4v16"/><path d="M4 9h8M12 15h8"/>',
 atlas:'<circle cx="12" cy="12" r="9"/><path d="M15.5 8.5l-2 5-5 2 2-5z"/>',
 charter:'<path d="M7 3h10a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2z"/><path d="M9 8h6M9 12h6M9 16h3"/>',
 horizon:'<path d="M3 13l2.5-8h13L21 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><path d="M3 13h5l1.5 2h5L16 13h5"/>',
 flares:'<path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z"/><path d="M12 8v5M12 16v.5"/>',
 dreams:'<path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5z"/>',
 verdicts:'<path d="M9 12l2 2 4-5"/><rect x="3" y="4" width="18" height="16" rx="2"/>',
 activity:'<path d="M3 12h4l3-8 4 16 3-8h4"/>',
 docs:'<path d="M2 5h8a2 2 0 0 1 2 2v13a2 2 0 0 0-2-2H2z"/><path d="M22 5h-8a2 2 0 0 0-2 2v13a2 2 0 0 1 2-2h8z"/>'};
</script>
 <button data-p="overview"><span class="lb"><i data-ic="overview"></i>Overview</span></button>
 <button data-p="ledger"><span class="lb"><i data-ic="ledger"></i>Ledger</span><span class="n" id="n-ledger">–</span></button>
 <button data-p="lanes"><span class="lb"><i data-ic="lanes"></i>Lanes</span><span class="n" id="n-lanes">–</span></button>
 <button data-p="atlas"><span class="lb"><i data-ic="atlas"></i>Atlas</span><span class="n" id="n-atlas">–</span></button>
 <button data-p="charter"><span class="lb"><i data-ic="charter"></i>Charter</span><span class="n" id="n-charter">–</span></button>
 <button data-p="horizon"><span class="lb"><i data-ic="horizon"></i>Horizon</span><span class="n" id="n-horizon">–</span></button>
 <button data-p="flares"><span class="lb"><i data-ic="flares"></i>Flares</span><span class="n" id="n-find">–</span></button>
 <button data-p="dreams"><span class="lb"><i data-ic="dreams"></i>Dreams</span><span class="n" id="n-dreams">–</span></button>
 <button data-p="verdicts"><span class="lb"><i data-ic="verdicts"></i>Verdicts</span><span class="n" id="n-appr">–</span></button>
 <button data-p="activity"><span class="lb"><i data-ic="activity"></i>Activity</span><span class="n" id="n-act">–</span></button>
 <button data-p="docs"><span class="lb"><i data-ic="docs"></i>Docs</span></button>
 <div class="foot">v__VERSION__ · <span id="head" class="mono"></span><br><span id="mode"></span></div>
</nav>
<main>
 <div class="readonly" id="ro">Static snapshot — actions are disabled. Run <code>cosmos ui</code> for the live control room.</div>
 <header class="top"><h1 id="title">Overview</h1><span class="sub" id="subtitle"></span><span class="spacer"></span>
  <input id="q" placeholder="Search everything…" style="width:260px">
  <button class="btn" id="capture" title="Backfill from every Claude transcript of this repo">⤓ Capture</button>
  <button class="btn primary" id="dream">💤 Run dream</button></header>
 <section id="page"></section>
</main></div>
<div class="toast" id="toast"></div>
<script src="https://cdn.jsdelivr.net/npm/mermaid@10.9.1/dist/mermaid.min.js" onerror="window.__nomermaid=1"></script>
<script>
const LIVE = location.protocol.startsWith('http');
if(window.mermaid){mermaid.initialize({startOnLoad:false,theme:'base',themeVariables:{primaryColor:'#0d0d10',primaryTextColor:'#ECEAE4',primaryBorderColor:'#ECEAE4',lineColor:'#E8CFA0',secondaryColor:'#141418',tertiaryColor:'#050506',fontFamily:'inherit',fontSize:'14px'}})}
let S=null, page='overview', q='', sel=null, filt={cat:null,status:null}, selRun=null;
const CATS=["finding","architecture","decision","convention","constraint","bug","dependency","workflow","domain","rejected"];
const FSTAT=["open","claimed","pr_open","needs_human","regressed","fixed","wontfix","withdrawn","note"];
const SEVI={critical:"🔴",high:"🟠",medium:"🟡",low:"🔵",note:"🔬",info:"⚪"};
const $=s=>document.querySelector(s);
const esc=s=>String(s??'').replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const cc=c=>getComputedStyle(document.documentElement).getPropertyValue("--"+c).trim()||"#888";
const md=s=>esc(s).replace(/`([^`]+)`/g,'<code>$1</code>').replace(/\*\*(.+?)\*\*/g,'<b>$1</b>').replace(/\*(.+?)\*/g,'<b>$1</b>').replace(/(?<!\w)_(\S[^_]*?\S)_(?!\w)/g,'<i>$1</i>');
function toast(m){const t=$('#toast');t.textContent=m;t.classList.add('show');setTimeout(()=>t.classList.remove('show'),2600)}
async function load(){ if(LIVE){S=await (await fetch('/api/state')).json()} else {S=window.__SNAPSHOT__} ; render()}
async function act(body){ if(!LIVE){toast('read-only snapshot');return {ok:false}}; const r=await (await fetch('/api/action',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)})).json(); if(!r.ok)toast('✗ '+(r.error||'failed')); await load(); return r}
const byId=()=>Object.fromEntries(S.memories.map(m=>[m.id,m]));
const findings=()=>S.memories.filter(m=>m.category==='finding');
const fstatus=m=>(m.meta&&m.meta.finding_status)||'open';
const openIssues=()=>S.memories.filter(m=>m.status==='contradicted'||m.status==='stale-candidate');
const needsHuman=()=>findings().filter(m=>fstatus(m)==='needs_human');

function render(){
 $('#repo').textContent=S.repo; $('#head').textContent=S.head||'—'; $('#mode').textContent=LIVE?'● live':'○ snapshot';
 $('#ro').style.display=LIVE?'none':'block'; $('#dream').disabled=$('#capture').disabled=!LIVE;
 const living=S.memories.filter(m=>!['forgotten','superseded'].includes(m.status)&&m.category!=='finding').length;
 $('#n-ledger').textContent=living; $('#n-find').textContent=findings().filter(m=>['open','claimed','pr_open','needs_human','regressed'].includes(fstatus(m))).length;
 $('#n-dreams').textContent=S.dreams.length; const na=openIssues().length+needsHuman().length; const e=$('#n-appr'); e.textContent=na; e.className='n'+(na?' bad':'');
 const np=$('#n-act'); np.textContent=S.pending_observations; np.className='n'+(S.pending_observations?' warn':'');
 document.querySelectorAll('nav button').forEach(b=>b.classList.toggle('on',b.dataset.p===page));
 $('#title').textContent={overview:'Overview',ledger:'Ledger',lanes:'Lanes',atlas:'Atlas',charter:'Charter',horizon:'Horizon',flares:'Flares',dreams:'Dreams',verdicts:'Verdicts',activity:'Activity',docs:'Docs'}[page];
 $('#n-lanes').textContent=S.lanes.length; const ov=S.lanes.filter(l=>l.overlap).length; $('#n-lanes').className='n'+(ov?' warn':'');
 const ac=S.atlas.check; $('#n-atlas').textContent=ac.exists?((ac.drift.length+ac.missing.length)?'drift':'ok'):'–'; $('#n-atlas').className='n'+(ac.exists&&(ac.drift.length+ac.missing.length)?' warn':'');
 $('#n-charter').textContent=S.charter.rules.length; $('#n-horizon').textContent=S.intakes.length;
 ({overview,ledger,lanes,atlas,charterPage,horizon,flaresPage,dreams,verdicts,activity,docs})[page==='flares'?'flaresPage':page==='charter'?'charterPage':page]();
}
/* ---------- overview */
function ago(ts){if(!ts)return '';const d=(Date.now()-Date.parse(ts.replace(/^(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})(\d{2})Z$/,'$1-$2-$3T$4:$5:$6Z')))/6e4;return d<2?'just now':d<60?Math.round(d)+' min ago':d<1440?Math.round(d/60)+' h ago':Math.round(d/1440)+' d ago'}
function overview(){
 const h=S.health, last=S.dreams[0], c=S.atlas.check, drift=c.exists&&(c.drift.length+c.missing.length);
 const openF=findings().filter(m=>['open','claimed','pr_open','needs_human','regressed'].includes(fstatus(m)));
 const crit=openF.filter(m=>m.meta.severity==='critical').length, high=openF.filter(m=>m.meta.severity==='high').length;
 const decide=openIssues().length+needsHuman().length;
 const facts=S.memories.filter(m=>m.status==='active'&&m.category!=='finding');
 $('#subtitle').textContent='';
 const act=(n,label,sub,page_,tone,btn)=>`<div class="act ${tone}"><div class="k">${n}</div><div class="t">${label}</div><div class="d">${sub}</div><button class="btn sm" data-go-page="${page_}">${btn}</button></div>`;
 $('#page').innerHTML=`
 <p class="lead">Your AI knows <b>${facts.length} facts</b> about this codebase${S.charter.rules.length?`, follows <b>${S.charter.rules.length} team rules</b>`:''}${S.atlas.check.exists?`, and ${drift?'has an <b>out-of-date map</b>':'has a <b>current map</b>'} of it`:''}.</p>
 <div class="acts">
  ${act(decide,'to decide', decide?[h.contradicted?`${h.contradicted} contradiction${h.contradicted===1?'':'s'}`:'',h.stale?`${h.stale} possibly out of date`:'',needsHuman().length?`${needsHuman().length} finding${needsHuman().length===1?'':'s'} need a human`:''].filter(Boolean).join(' · '):'nothing is waiting on you','verdicts',decide?'warn':'ok','Decide')}
  ${act(openF.length,'open findings', openF.length?`${crit} critical · ${high} high · ${openF.length-crit-high} other`:'no open findings','findings',crit?'bad':openF.length?'warn':'ok','Work the board')}
  ${act(S.pending_observations,'to consolidate', S.pending_observations?'new observations waiting to become facts':last?`last dream ${ago(last.at)} · ${last.new.length} new facts`:'no dream has run yet','dreams',S.pending_observations?'warn':'ok',S.pending_observations?'Run dream':'Dreams')}
 </div>
 <div class="flowline">
  <span><b>${S.sessions}</b> sessions</span><i></i><span><b>${S.observations.length}</b> observations</span><i></i><span><b>${facts.length}</b> facts</span><i></i><span><b>${S.lanes.length}</b> lanes</span><i></i><span><b>${S.hooks.length}</b> hooks armed · ${S.agents.length?S.agents.join(', '):'claude'}</span>
 </div>
 <div class="grid g2" style="margin-top:28px">
  <div><h3 class="sec">What your AI reads first</h3><div class="small dim" style="margin:-6px 0 12px">The rules and facts injected at the start of every session. Click one to see its evidence, or forget it.</div>
   ${S.memories.filter(m=>m.status==='active').sort((a,b)=>(b.source==='explicit')-(a.source==='explicit')||b.importance*b.confidence-a.importance*a.confidence).slice(0,6).map(m=>`<div class="mem quiet" data-id="${m.id}" style="--c:${cc(m.category)}"><div class="t">${md(m.text)}</div><div class="m"><span class="badge cat" style="--c:${cc(m.category)}">${m.category}</span>${m.source==='explicit'?'<span class="badge" style="color:var(--acc)">team rule</span>':''}</div></div>`).join('')||'<div class="empty">Nothing yet — work in your agent, then run a dream.</div>'}</div>
  <div><h3 class="sec">Where the work is</h3><div class="small dim" style="margin:-6px 0 12px">Lanes with the most knowledge and open findings.</div>
   ${S.lanes.slice(0,7).map(l=>`<div class="lanemini"><span class="ln">${esc(l.lane)}</span><span class="bar"><i style="width:${Math.min(100,Math.round(100*(l.facts+l.findings)/Math.max(1,S.lanes[0].facts+S.lanes[0].findings)))}%"></i></span><span class="n">${l.facts} facts${l.findings_open?` · <span style="color:var(--bad)">${l.findings_open} open</span>`:''}${l.overlap?' · <span style="color:var(--warn)">overlap</span>':''}</span></div>`).join('')||'<div class="empty">Lanes appear after the first dream.</div>'}
   <div style="margin-top:14px"><button class="btn sm" data-go-page="lanes">All lanes</button> <button class="btn sm" data-go-page="atlas">${S.atlas.check.exists?(drift?'Atlas · drift':'Atlas · in sync'):'Build the atlas'}</button> <button class="btn sm" data-go-page="charter">Charter · ${S.charter.rules.length} rules</button></div></div>
 </div>`;
 document.querySelectorAll('[data-go-page]').forEach(b=>b.onclick=()=>{if(b.textContent==='Run dream'){$('#dream').click();return}page=b.dataset.goPage;sel=null;render()});
 bindMem();
}
const XI={gather:'<circle cx="12" cy="12" r="3"/><circle cx="4" cy="6" r="1.2"/><circle cx="20" cy="7" r="1.2"/><circle cx="6" cy="19" r="1.2"/><circle cx="19" cy="18" r="1.2"/><path d="M6.5 7.5l3.5 3M18 8.5l-3.5 2M8 17l2.5-3M17 16.5l-3-2.5"/>',
 curate:'<path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8z"/><path d="M19 17l.7 1.8 1.8.7-1.8.7L19 22l-.7-1.8-1.8-.7 1.8-.7z"/>',
 dedupe:'<circle cx="9" cy="12" r="6"/><circle cx="15" cy="12" r="6"/>', contra:'<path d="M4 12h6M14 12h6"/><path d="M8 8l4 4-4 4M16 8l-4 4 4 4"/>',
 super:'<path d="M5 17l4-10 4 10"/><path d="M7 14h4"/><path d="M15 7h4v10"/><path d="M13 12l3 3 3-3"/>', stale:'<circle cx="12" cy="12" r="8"/><path d="M12 7v5l3 2"/>',
 write:'<path d="M5 20h14"/><path d="M7 16l9.5-9.5a2 2 0 0 0-3-3L4 13v3z"/>', session:'<rect x="3" y="4" width="18" height="13" rx="2"/><path d="M8 20h8M12 17v3"/><path d="M7 9l3 2.5L7 14"/>',
 hook:'<path d="M12 3v9a4 4 0 0 0 8 0"/><circle cx="12" cy="3" r="1.5"/><path d="M4 12a4 4 0 0 0 8 0"/>', lane:'<path d="M4 4v16M12 4v16M20 4v16"/><path d="M4 9h8M12 15h8"/>',
 inject:'<path d="M4 12h12"/><path d="M12 8l4 4-4 4"/><rect x="17" y="5" width="4" height="14" rx="1"/>', people:'<circle cx="9" cy="8" r="3"/><circle cx="17" cy="9" r="2.5"/><path d="M3 20a6 6 0 0 1 12 0"/><path d="M14 20a4.5 4.5 0 0 1 7 0"/>',
 overlap:'<circle cx="10" cy="12" r="6"/><circle cx="14" cy="12" r="6"/><path d="M12 7.5v9" stroke-dasharray="1 2"/>', blind:'<circle cx="12" cy="12" r="8"/><path d="M8 12h8"/>',
 manifest:'<path d="M6 3h9l4 4v14H6z"/><path d="M15 3v4h4"/><path d="M9 12h6M9 16h6"/>', inventory:'<path d="M4 6h16M4 12h16M4 18h16"/><circle cx="7" cy="6" r="1"/><circle cx="7" cy="12" r="1"/><circle cx="7" cy="18" r="1"/>',
 diagram:'<rect x="3" y="4" width="6" height="5" rx="1"/><rect x="15" y="4" width="6" height="5" rx="1"/><rect x="9" y="15" width="6" height="5" rx="1"/><path d="M6 9v3h12V9M12 12v3"/>', fingerprint:'<path d="M12 4a8 8 0 0 1 8 8v3"/><path d="M12 8a4 4 0 0 1 4 4v6"/><path d="M12 12v8"/><path d="M8 12a4 4 0 0 1 .5-2"/><path d="M4 12a8 8 0 0 1 2.3-5.7"/>',
 drift:'<path d="M4 17c3-6 5-6 8 0s5 6 8 0"/><path d="M4 9c3-6 5-6 8 0s5 6 8 0" opacity=".5"/>', rule:'<path d="M7 3h10a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2z"/><path d="M9 8h6M9 12h6M9 16h3"/>',
 commit:'<circle cx="12" cy="12" r="3"/><path d="M12 3v6M12 15v6"/>', gate:'<path d="M4 20V8l8-4 8 4v12"/><path d="M9 20v-6h6v6"/>', describe:'<path d="M4 6h16M4 12h10M4 18h7"/>',
 collide:'<path d="M5 12h5M14 12h5"/><path d="M8 8l3 4-3 4M16 8l-3 4 3 4"/>', assess:'<path d="M4 19h16"/><path d="M6 16l4-6 4 3 4-7"/>', note:'<path d="M6 3h9l4 4v14H6z"/><path d="M9 13h6M9 17h4"/>',
 imp:'<path d="M12 3v12"/><path d="M8 11l4 4 4-4"/><path d="M4 19h16"/>', board:'<rect x="3" y="4" width="5" height="16" rx="1"/><rect x="9.5" y="4" width="5" height="10" rx="1"/><rect x="16" y="4" width="5" height="13" rx="1"/>',
 fix:'<path d="M14 6l4 4-9 9H5v-4z"/><path d="M12 8l4 4"/>', regress:'<path d="M4 14a8 8 0 1 1 2.3 5.7"/><path d="M4 20v-6h6"/>', slack:'<rect x="4" y="5" width="16" height="12" rx="2"/><path d="M8 21l4-4 4 4"/>',
 human:'<circle cx="12" cy="8" r="3.5"/><path d="M5 21a7 7 0 0 1 14 0"/>', evidence:'<circle cx="11" cy="11" r="6"/><path d="M20 20l-4.5-4.5"/>', decide:'<path d="M5 12l4 4 10-10"/>', record:'<path d="M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18z"/><circle cx="12" cy="12" r="3"/>'};
function stepper(steps, o={}){ // steps: [{k,icon,title,desc,value,unit,lit,llm}]
 return `<div class="dreamflow ${o.compact?'compact':''}"><div class="dfhead"><h3 class="sec" style="margin:0">${o.title||'How it works'}</h3>${o.sub?`<span class="small dim">${o.sub}</span>`:''}</div>
  <div class="dsteps" style="grid-template-columns:repeat(${steps.length},1fr)">${steps.map((st,i)=>`<div class="dstep ${st.llm?'llm':''} ${st.lit?'lit':''}"><div class="dline"></div><div class="dnode"><svg viewBox="0 0 24 24">${XI[st.icon]||''}</svg></div><div class="dnum">${i+1}</div><div class="dt">${st.title}</div><div class="dd">${st.desc}</div>${st.value!==undefined&&st.value!==''?`<div class="dv">${st.value}<span>${st.unit||''}</span></div>`:''}</div>`).join('')}</div>
  ${o.foot?`<div class="small dim" style="margin-top:14px">${o.foot}</div>`:''}</div>`}
const statsRow=(items)=>`<div class="stats2" style="grid-template-columns:repeat(${items.length},1fr)">${items.map(([v,l,sub,tone])=>`<div class="stat2 ${tone||''}"><div class="v ${/^[\d.,%]+$/.test(String(v))?'':'txt'}">${v}</div><div class="l">${l}</div>${sub?`<div class="s">${sub}</div>`:''}</div>`).join('')}</div>`;
const kpi=(l,v,s,color)=>`<div class="card"><h3>${l}</h3><div class="kpi" style="color:${color||'var(--fg)'}">${v}</div><div class="small muted">${s}</div></div>`;
const fmt=ts=>ts?ts.replace(/^(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})(\d{2})Z$/,'$1-$2-$3 $4:$5Z').replace('T',' ').slice(0,17):'';
/* ---------- ledger */
function memRow(m){return `<div class="mem" data-id="${m.id}" style="--c:${cc(m.category)}"><div class="t">${md(m.text)}</div><div class="m"><span class="badge cat" style="--c:${cc(m.category)}">${m.category}</span>${m.status!=='active'?`<span class="badge ${m.status}">${m.status}</span>`:''}<span>${Math.round(m.confidence*100)}%</span>${m.files[0]?`<code>${esc(m.files[0])}</code>`:''}${m.source==='explicit'?'<span class="badge" style="color:var(--acc2)">explicit</span>':''}</div></div>`}
function bindMem(){document.querySelectorAll('.mem,.fcard').forEach(el=>el.onclick=()=>{sel=el.dataset.id;render()})}
function ledger(){
 const HIDDEN=['forgotten','superseded'];
 const all=S.memories.filter(m=>m.category!=='finding');
 // base = what a reader wants by default: living facts. Hidden statuses only appear when explicitly selected.
 const base=all.filter(m=>filt.status?m.status===filt.status:!HIDDEN.includes(m.status));
 const byCat=all.filter(m=>(!filt.cat||m.category===filt.cat));
 const vis=base.filter(m=>(!filt.cat||m.category===filt.cat)&&(!q||(m.text+' '+m.tags.join(' ')+' '+m.files.join(' ')).toLowerCase().includes(q)));
 const living=all.filter(m=>!HIDDEN.includes(m.status)).length;
 $('#subtitle').textContent=(filt.cat||filt.status||q)?`showing ${vis.length} of ${living} facts`:`${living} facts your AI knows${all.length-living?` · ${all.length-living} retired`:''}`;
 const catChips=CATS.filter(c=>c!=='finding').map(c=>{const n=base.filter(m=>m.category===c).length;return n?`<span class="chip ${filt.cat===c?'on':''}" data-cat="${c}" style="${filt.cat===c?'border-color:'+cc(c)+';color:'+cc(c):''}">${c} ${n}</span>`:''}).join('');
 const stChips=["contradicted","stale-candidate","superseded","forgotten"].map(st=>{const n=byCat.filter(m=>m.status===st).length;return n?`<span class="chip ${filt.status===st?'on':''}" data-status="${st}">${st==='stale-candidate'?'possibly out of date':st} ${n}</span>`:''}).join('');
 const m=sel&&byId()[sel];
 const explicit=all.filter(m=>m.source==='explicit'&&!HIDDEN.includes(m.status)).length, curated=all.filter(m=>m.meta&&m.meta.curated&&!HIDDEN.includes(m.status)).length, stale=all.filter(m=>m.status==='stale-candidate').length, retired=all.length-living;
 const topN=S.config.retrieval.session_start_max;
 $('#page').innerHTML=`${statsRow([[living,'facts','your AI knows'],[curated,'model-curated',living?Math.round(100*curated/Math.max(1,living))+'% of facts':''],[explicit,'stated by people','explicit facts'],[stale,'possibly out of date','review in Verdicts',stale?'warn':''],[retired,'retired','forgotten or superseded']])}
  ${stepper([{icon:'session',title:'Sessions',desc:'people work with their agent',value:S.sessions,unit:'sessions',lit:S.sessions},{icon:'hook',title:'Capture',desc:'hooks keep durable sentences, redact secrets',value:S.observations.length,unit:'observations',lit:S.observations.length},{icon:'curate',title:'Model curates',desc:'keep · rewrite · category · lane',value:curated,unit:'facts',lit:curated,llm:true},{icon:'lane',title:'Filed by lane',desc:'the feature it belongs to',value:S.lanes.length,unit:'lanes',lit:S.lanes.length},{icon:'inject',title:'Recalled',desc:'top facts at session start, the rest per prompt',value:topN,unit:'per session'}],{compact:true,title:'How a fact gets here'})}
  <div class="toolbar">
   <div class="trow"><span class="tl">kind</span><div class="chips">${catChips}</div></div>
   <div class="trow"><span class="tl">state</span><div class="chips">${stChips||'<span class="small dim">all facts are current</span>'}</div>${(filt.cat||filt.status||q)?'<button class="btn sm" id="clearf">clear filters</button>':''}</div>
   <form id="rem" class="composer"><svg viewBox="0 0 24 24">${XI.record}</svg><input id="remtext" placeholder="Record a fact you know about this codebase…"><select id="remcat">${CATS.filter(c=>!['finding','convention'].includes(c)).map(c=>`<option ${c==='decision'?'selected':''}>${c}</option>`).join('')}</select><button class="btn sm primary">Record</button></form>
   <div class="small dim" style="padding:0 4px">A fact is something true about the code. A rule about how the team works goes in the <a href="#" data-go-page="charter" style="color:var(--acc)">Charter</a>.</div>
  </div>
  <div class="split"><div>${vis.map(memRow).join('')||`<div class="empty">${(filt.cat||filt.status||q)?'Nothing matches these filters.':'No facts yet — work in your agent, then run a dream.'}</div>`}</div>
  <div class="sticky">${m?detail(m):'<div class="card"><h3>Graph</h3><canvas id="graph"></canvas><div class="small dim" style="margin-top:8px">nodes = facts · edges = shared files or tags · red = contradiction · dashed = superseded. Click a node.</div></div>'}</div></div>`;
 document.querySelectorAll('.chip').forEach(c=>c.onclick=()=>{if(c.dataset.cat)filt.cat=filt.cat===c.dataset.cat?null:c.dataset.cat;if(c.dataset.status)filt.status=filt.status===c.dataset.status?null:c.dataset.status;render()});
 const cf=$('#clearf');if(cf)cf.onclick=()=>{filt={cat:null,status:null};q='';$('#q').value='';render()};
 document.querySelectorAll('[data-go-page]').forEach(a=>a.onclick=e=>{e.preventDefault();page=a.dataset.goPage;render()});
 $('#rem').onsubmit=async e=>{e.preventDefault();const t=$('#remtext').value.trim();if(!t)return;await act({type:'remember',text:t,category:$('#remcat').value});toast('recorded')};
 bindMem(); bindDetail(); if(!m)graph(vis);
}
function detail(m){const B=byId();const link=id=>B[id]?`<a href="#" data-go="${id}">${esc(B[id].text.slice(0,80))}</a>`:esc(id);
 const isF=m.category==='finding';
 return `<div class="card"><div class="row" style="justify-content:space-between"><span class="badge cat" style="--c:${cc(m.category)}">${m.category}</span><button class="btn sm" data-close>✕</button></div>
 <h2 style="font-size:16px;margin:10px 0">${md(m.text)}</h2>
 ${isF?`<div class="row"><span class="badge sev" style="--c:${cc(m.meta.severity)}">${SEVI[m.meta.severity]||''} ${m.meta.severity}</span><span class="badge">${m.meta.audit_id}</span><span class="badge ${fstatus(m)==='regressed'?'contradicted':'active'}">${fstatus(m)}</span>${m.meta.area?`<span class="badge">${esc(m.meta.area)}</span>`:''}</div>
   ${m.meta.locations?`<div class="small" style="margin:8px 0">📍 ${md(m.meta.locations)}</div>`:''}
   ${(m.details||[]).map(([l,t])=>`<div class="sect"><b>${esc(l)}</b><div class="small">${md(t)}</div></div>`).join('')}
   <div class="actions">${['claimed','pr_open','needs_human','fixed','wontfix','withdrawn','open'].filter(s=>s!==fstatus(m)&&fstatus(m)!=='note').map(s=>`<button class="btn sm ${s==='fixed'?'ok':s==='needs_human'?'warn':s==='withdrawn'?'bad':''}" data-fs="${s}">${s.replace('_',' ')}</button>`).join('')}</div>
   ${m.meta.status_note?`<div class="small muted" style="margin-top:8px">note: ${esc(m.meta.status_note)}</div>`:''}`
 :`<dl><dt>status</dt><dd><span class="badge ${m.status}">${m.status}</span></dd><dt>confidence</dt><dd>${Math.round(m.confidence*100)}% · ${m.evidence_count} observation${m.evidence_count!==1?'s':''} · ${m.source}</dd>
   <dt>timeline</dt><dd>created ${m.created} · updated ${m.updated} · verified ${m.last_verified}</dd>
   ${m.files.length?`<dt>evidence</dt><dd>${m.files.map(f=>`<code>${esc(f)}</code>`).join('<br>')}</dd>`:''}${m.authors.length?`<dt>seen by</dt><dd>${m.authors.map(esc).join(', ')}</dd>`:''}
   ${m.reason?`<dt>note</dt><dd class="small">${md(m.reason)}</dd>`:''}${m.supersedes?`<dt>supersedes</dt><dd class="small">${link(m.supersedes)}</dd>`:''}${m.superseded_by?`<dt>superseded by</dt><dd class="small">${link(m.superseded_by)}</dd>`:''}
   ${m.contradicts.length?`<dt style="color:var(--bad)">contradicts</dt><dd class="small">${m.contradicts.map(link).join('<br>')}</dd>`:''}${m.related.length?`<dt>related</dt><dd class="small">${m.related.map(link).join('<br>')}</dd>`:''}
   ${m.tags.length?`<dt>tags</dt><dd class="small muted">${m.tags.map(t=>'#'+esc(t)).join(' ')}</dd>`:''}</dl>
   <div class="actions"><button class="btn sm ok" data-act="verify">✓ Verify</button>${m.status==='forgotten'||m.status==='superseded'?`<button class="btn sm" data-act="reopen">Reopen</button>`:`<button class="btn sm bad" data-act="forget">Forget</button>`}<a class="btn sm" href="/api/note/${m.id}" target="_blank">.md</a></div>`}
 <div class="small dim" style="margin-top:10px"><code>cosmos why ${m.id}</code></div></div>`}
function bindDetail(){document.querySelectorAll('[data-go]').forEach(a=>a.onclick=e=>{e.preventDefault();sel=a.dataset.go;render()});
 const c=document.querySelector('[data-close]');if(c)c.onclick=()=>{sel=null;render()};
 document.querySelectorAll('[data-act]').forEach(b=>b.onclick=()=>act({type:b.dataset.act,id:sel}));
 document.querySelectorAll('[data-fs]').forEach(b=>b.onclick=async()=>{const note=b.dataset.fs==='needs_human'||b.dataset.fs==='withdrawn'||b.dataset.fs==='wontfix'?prompt('Why? (recorded as status_note)')||'':'';await act({type:'finding_status',id:sel,status:b.dataset.fs,note})});}
function graph(v){const cv=$('#graph');if(!cv)return;const r=cv.getBoundingClientRect();cv.width=r.width;cv.height=r.height;const ctx=cv.getContext('2d');
 const ids=new Set(v.map(m=>m.id));const N=v.map((m,i)=>({m,x:cv.width/2+Math.cos(i)*90,y:cv.height/2+Math.sin(i)*70,vx:0,vy:0}));const P=Object.fromEntries(N.map(n=>[n.m.id,n]));const E=[];
 for(const m of v){for(const r of m.related)if(ids.has(r)&&m.id<r)E.push([P[m.id],P[r],'rel']);for(const c of m.contradicts)if(ids.has(c)&&m.id<c)E.push([P[m.id],P[c],'con']);if(m.supersedes&&ids.has(m.supersedes))E.push([P[m.id],P[m.supersedes],'sup'])}
 let f=0;(function loop(){for(const a of N){for(const b of N){if(a===b)continue;let dx=a.x-b.x,dy=a.y-b.y,d2=dx*dx+dy*dy+.01,k=700/d2;a.vx+=dx*k/Math.sqrt(d2);a.vy+=dy*k/Math.sqrt(d2)}a.vx+=(cv.width/2-a.x)*.003;a.vy+=(cv.height/2-a.y)*.003}
  for(const[a,b]of E){let dx=b.x-a.x,dy=b.y-a.y,d=Math.hypot(dx,dy)+.01,k=(d-60)*.012;a.vx+=dx/d*k;a.vy+=dy/d*k;b.vx-=dx/d*k;b.vy-=dy/d*k}
  for(const n of N){n.vx*=.85;n.vy*=.85;n.x=Math.max(8,Math.min(cv.width-8,n.x+n.vx));n.y=Math.max(8,Math.min(cv.height-8,n.y+n.vy))}
  ctx.clearRect(0,0,cv.width,cv.height);for(const[a,b,t]of E){ctx.strokeStyle=t==='con'?cc('bad'):t==='sup'?cc('dim'):cc('line');ctx.lineWidth=t==='con'?1.6:1;ctx.setLineDash(t==='sup'?[4,4]:[]);ctx.beginPath();ctx.moveTo(a.x,a.y);ctx.lineTo(b.x,b.y);ctx.stroke()}
  ctx.setLineDash([]);for(const n of N){ctx.globalAlpha=n.m.status==='superseded'?.35:1;ctx.fillStyle=cc(n.m.category);ctx.beginPath();ctx.arc(n.x,n.y,4+n.m.evidence_count*1.5,0,7);ctx.fill()}ctx.globalAlpha=1;
  if(f++<160)requestAnimationFrame(loop)})();
 cv.onclick=e=>{const r=cv.getBoundingClientRect(),x=e.clientX-r.left,y=e.clientY-r.top;let best=null,bd=400;for(const n of N){const d=(n.x-x)**2+(n.y-y)**2;if(d<bd){bd=d;best=n}}if(best){sel=best.m.id;render()}}}
/* ---------- lanes */
function lanes(){
 const L=S.lanes.filter(l=>!q||l.lane.includes(q));const ov=S.lanes.filter(l=>l.overlap).length;
 $('#subtitle').textContent=`${S.lanes.length} lanes · ${ov} with two or more people active in the last 30 days`;
 const withF=S.lanes.filter(l=>l.findings_open).length, blind=S.lanes.filter(l=>l.findings_open&&!l.facts).length, people=new Set(S.lanes.flatMap(l=>l.contributors.map(c=>c.name))).size;
 $('#page').innerHTML=`${statsRow([[S.lanes.length,'lanes','features the team works in'],[withF,'with open findings','',withF?'warn':''],[blind,'blind spots','open findings, no captured knowledge',blind?'warn':''],[ov,'with overlap','two or more people this month',ov?'warn':''],[people,'people active','last 30 days']])}
  ${stepper([{icon:'manifest',title:'Files',desc:'every fact and finding points at files',value:S.memories.filter(m=>m.files.length).length,unit:'anchored',lit:true},{icon:'curate',title:'Model names the lane',desc:'the feature a PM would recognise',value:Object.keys(S.config.lanes||{}).length,unit:'configured lanes',lit:Object.keys(S.config.lanes||{}).length,llm:true},{icon:'lane',title:'Filed',desc:'ledger, index and CLAUDE.md grouped by lane',value:S.lanes.length,unit:'lanes',lit:true},{icon:'overlap',title:'Overlap',desc:'two people in one lane this month',value:ov,unit:'lanes',lit:ov},{icon:'blind',title:'Blind spots',desc:'open findings, no captured knowledge',value:blind,unit:'lanes',lit:blind}],{compact:true,title:'How lanes work',foot:'Change the mapping with <code>cosmos lanes --propose --write</code> or in <code>config.json → lanes</code>.'})}
  <div class="lanerow" style="background:transparent;border:0;color:var(--mut);font-size:11px;text-transform:uppercase;letter-spacing:.22em"><span>lane</span><span>facts</span><span>open findings</span><span>people · last 30 days</span></div>
  ${L.map(l=>`<div class="lanerow ${l.overlap?'ov':''}"><div><div class="ln">${esc(l.lane)}</div><div class="small dim">${l.files.slice(0,2).map(esc).join(' · ')}</div></div><div>${l.facts}</div><div style="color:${l.findings_open?'var(--bad)':'var(--mut)'}">${l.findings_open}</div><div class="who">${l.contributors.map(c=>`<span class="person">${esc(c.name)} · ${c.observations}</span>`).join('')||'<span class="dim">nobody recorded</span>'}${l.overlap?'<span class="badge contradicted">overlap</span>':''}</div></div>`).join('')||'<div class="empty">No lanes yet — facts get a lane on the next dream.</div>'}`;
}
/* ---------- atlas */
let atlasTab='containers';
function atlas(){
 const A=S.atlas, docs=A.docs, names=Object.keys(docs);
 const c=A.check; const drift=c.exists&&(c.drift.length+c.missing.length);
 $('#subtitle').textContent=c.exists?`${c.counts.apps} apps · ${c.counts.services} services · ${c.counts.stores} stores · ${c.counts.endpoints} endpoints`:'no atlas yet';
 if(!names.includes(atlasTab))atlasTab=names[0];
 const md=docs[atlasTab]||'';const mer=(md.match(/```mermaid\n([\s\S]*?)```/)||[])[1];
 const rest=md.replace(/^---[\s\S]*?---\n/,'').replace(/```mermaid[\s\S]*?```/,'');
 const K=c.counts||{};
 $('#page').innerHTML=`${c.exists?statsRow([[drift?'drift':'in sync','status',drift?`${c.drift.length+c.missing.length} source file(s) changed`:`generated ${c.generated}`,drift?'warn':''],[K.apps||0,'apps & packages',''],[K.services||0,'services','docker-compose'],[K.stores||0,'stores & queues',''],[K.k8s||0,'k8s objects',''],[K.endpoints||0,'api endpoints','from OpenAPI']]):''}
  ${stepper([{icon:'manifest',title:'Read the repo',desc:'manifests · compose · k8s · Terraform · OpenAPI',value:c.exists?(S.atlas.docs.inventory||'').split('\n- `').length-1:'',unit:'sources',lit:c.exists},{icon:'inventory',title:'Inventory',desc:'apps, services, stores, endpoints, config keys',value:c.exists?(K.apps||0)+(K.services||0)+(K.stores||0):'',unit:'components',lit:c.exists},{icon:'diagram',title:'Diagrams',desc:'containers · deployment · api, in Mermaid',value:c.exists?Object.keys(S.atlas.docs).length:'',unit:'documents',lit:c.exists},{icon:'curate',title:'Deep pass',desc:'/atlas: data flows, dependency index, lanes',value:S.atlas.docs['data-flow']||S.atlas.docs.dependencies?'done':'not yet',unit:'',lit:!!(S.atlas.docs['data-flow']||S.atlas.docs.dependencies),llm:true},{icon:'fingerprint',title:'Fingerprint',desc:'every source file hashed',value:'',unit:'',lit:c.exists},{icon:'drift',title:'Drift',desc:'reported when the code moves and the picture does not',value:c.exists?(c.drift.length+c.missing.length):'',unit:'changed files',lit:drift}],{compact:true,title:'How the atlas stays true'})}
  <div class="row" style="margin:0 0 12px"><span class="spacer"></span><button class="btn sm" id="atlasrun">↻ Rebuild</button><span class="small dim">deep pass: <code>/atlas</code> in Claude Code</span></div>
  ${names.length?`<div class="tabs">${names.map(n=>`<span class="chip ${n===atlasTab?'on':''}" data-tab="${n}">${n}</span>`).join('')}</div>
  ${mer?`<div class="mmd" id="mmd">${window.mermaid?'':'<pre class="log">'+esc(mer)+'</pre>'}</div>`:''}
  <div class="card mdtxt" style="margin-top:12px">${mdlite(rest)}</div>`:'<div class="empty">Run <code>cosmos atlas</code> (or the button above) to generate inventory and diagrams from the repository.</div>'}`;
 document.querySelectorAll('[data-tab]').forEach(t=>t.onclick=()=>{atlasTab=t.dataset.tab;render()});
 $('#atlasrun').onclick=async()=>{const r=await act({type:'atlas'});if(r.ok)toast(`atlas rebuilt: ${r.apps} apps · ${r.services} services · ${r.stores} stores`)};
 if(mer&&window.mermaid){mermaid.render('m'+Date.now(),mer).then(o=>{const el=$('#mmd');if(el)el.innerHTML=o.svg}).catch(e=>{const el=$('#mmd');if(el)el.innerHTML='<pre class="log">'+esc(mer)+'</pre>'})}
}
function mdlite(t){return esc(t).replace(/^### (.+)$/gm,'<h3>$1</h3>').replace(/^## (.+)$/gm,'<h2>$1</h2>').replace(/^# (.+)$/gm,'<h1>$1</h1>').replace(/`([^`]+)`/g,'<code>$1</code>').replace(/\*\*(.+?)\*\*/g,'<b>$1</b>').replace(/(?<!\w)_(\S[^_\n]*?\S)_(?!\w)/g,'<i>$1</i>').replace(/^\|(.+)\|$/gm,(m)=>'<div style="font-family:ui-monospace,Menlo,monospace;font-size:12px;color:var(--mut)">'+m+'</div>')}
/* ---------- charter */
function charterPage(){
 const C=S.charter;
 $('#subtitle').textContent='';
 const sections=(C.body.match(/^## /gm)||[]).length;
 $('#page').innerHTML=`${statsRow([[C.rules.length,'explicit rules','stated by the team'],[sections,'charter sections','.cosmos/charter.md'],[C.gate.enabled?'on':'off','gate',C.gate.enabled?'holds a turn until the checklist is met':'disabled',C.gate.enabled?'':'warn'],[C.gate.require_tests?'required':'optional','tests','when code changed'],[C.gate.require_refs?'required':'optional','file:line refs','in the summary']])}
  ${stepper([{icon:'rule',title:'Write the rules',desc:'style · testing · pointing · self-review · architecture',value:sections,unit:'sections',lit:sections},{icon:'commit',title:'Agree in a PR',desc:'the team, not one person, owns it',value:C.rules.length,unit:'explicit rules',lit:C.rules.length},{icon:'inject',title:'Injected first',desc:'every session, every machine, every agent',value:S.hooks.includes('SessionStart')?'on':'off',unit:'',lit:S.hooks.includes('SessionStart')},{icon:'gate',title:'Gate enforces',desc:'tests ran · file:line cited · findings addressed',value:C.gate.enabled?'on':'off',unit:'',lit:C.gate.enabled}],{compact:true,title:'How the charter works',foot:'Facts about the code live in the Ledger; the Charter is how the team works.'})}
  <div class="split"><div>
   <div class="charter">${mdlite(C.body)}</div></div>
  <div class="sticky"><div class="card" style="margin-bottom:14px"><h3>Add a rule</h3><div class="small dim" style="margin:-4px 0 10px">A rule is how the team works (style, testing, review, architecture). It goes into <code>.cosmos/charter.md</code> and is injected first into every session. Facts about the code live in the Ledger.</div><form id="chf" class="stack" style="display:grid;gap:8px"><input id="cht" placeholder="e.g. Never call the DB from a controller"><select id="chs">${['Architecture rules','How we write code','How we test','How we point at things','How we review our own work'].map(x=>`<option>${x}</option>`).join('')}</select><button class="btn sm primary">Add to charter + ledger</button></form>
   <div class="small dim" style="margin-top:8px">Also works from any session: type <code>remember: …</code></div></div>
   <div class="card" style="margin-bottom:14px"><h3>Explicit rules in the ledger</h3>${C.rules.map(memRow).join('')||'<div class="small dim">none yet</div>'}</div>
   <div class="card"><h3>Gate</h3><dl><dt>enabled</dt><dd>${C.gate.enabled}</dd><dt>tests</dt><dd>${C.gate.require_tests?'required when code changed':'not required'}</dd><dt>file:line refs</dt><dd>${C.gate.require_refs?'required in the summary':'not required'}</dd><dt>findings</dt><dd>open findings on touched files must be addressed or deferred</dd></dl><div class="small dim">Edit the <code>gate:</code> line in .cosmos/charter.md</div></div></div></div>`;
 $('#chf').onsubmit=async e=>{e.preventDefault();const t=$('#cht').value.trim();if(!t)return;const r=await act({type:'charter_add',text:t,section:$('#chs').value});if(r.ok)toast('added to charter')};
 bindMem();
}
/* ---------- intake */
let selHorizon=null, pickPath='', picked=new Set(), attached=[];
async function tree(rel){try{return await (await fetch('/api/tree?path='+encodeURIComponent(rel))).json()}catch(e){return []}}
function horizon(){
 const I=S.intakes; const cur=selHorizon&&I.find(x=>x.file===selHorizon);
 $('#subtitle').textContent='';
 const laneHits={}; I.forEach(x=>{try{JSON.parse(x.lanes.replace(/'/g,'"')).forEach(l=>laneHits[l]=(laneHits[l]||0)+1)}catch(e){}});
 const topLane=Object.entries(laneHits).sort((a,b)=>b[1]-a[1])[0];
 $('#page').innerHTML=`${statsRow([[I.length,'features mapped','before a line was written'],[topLane?topLane[0]:'—','most-touched lane',topLane?`${topLane[1]} intake${topLane[1]===1?'':'s'}`:''],[findings().filter(m=>['open','claimed','pr_open','needs_human','regressed'].includes(fstatus(m))).length,'open findings','that intakes check against'],[S.atlas.check.exists?'yes':'no','atlas available','for structural context']])}
  ${stepper([{icon:'describe',title:'Describe',desc:'one sentence, a brief, documents'},{icon:'manifest',title:'Point at code',desc:'folders and files it will touch',lit:true},{icon:'evidence',title:'Retrieve',desc:'facts, decisions and constraints that collide',lit:true},{icon:'board',title:'Flares',desc:'open findings in the way',value:findings().filter(m=>['open','claimed','pr_open','needs_human','regressed'].includes(fstatus(m))).length,unit:'open',lit:true},{icon:'assess',title:'Model assesses',desc:'impact, risks, decide-first questions',llm:true,lit:true},{icon:'note',title:'Saved',desc:'a note beside the code, travels with the PR',value:I.length,unit:'intakes',lit:I.length}],{compact:true,title:'How intake works'})}
  <div class="intakeform">
   <div class="ifcol">
    <div class="tl" style="margin-bottom:8px">the feature</div>
    <input id="int" placeholder="Describe the feature in one sentence" style="width:100%">
    <div class="tl" style="margin:16px 0 8px">brief · optional</div>
    <textarea id="inb" rows="6" placeholder="Paste the PRD, ticket, Slack thread or acceptance criteria here…" style="width:100%;resize:vertical"></textarea>
    <div class="tl" style="margin:16px 0 8px">documents · optional</div>
    <div class="drop" id="drop"><input type="file" id="infile" multiple style="display:none"><svg viewBox="0 0 24 24">${XI.imp}</svg><div>Drop files here or <a href="#" id="pickfiles" style="color:var(--acc)">browse</a><div class="small dim">specs, notes, exports — text is read in your browser and saved with the intake; nothing is uploaded anywhere else</div></div></div>
    <div id="attlist" class="chips" style="margin-top:8px">${attached.map((a,i)=>`<span class="chip on" data-rm="${i}">${esc(a.name)} · ${Math.round(a.text.length/1000)}k ✕</span>`).join('')}</div>
   </div>
   <div class="ifcol">
    <div class="tl" style="margin-bottom:8px">code it will touch · optional</div>
    <div class="browser"><div class="crumbs" id="crumbs"></div><div id="treelist" class="treelist"><span class="small dim">loading…</span></div></div>
    <div id="picked" class="chips" style="margin-top:8px">${[...picked].map(p=>`<span class="chip on" data-unpick="${esc(p)}">${esc(p)} ✕</span>`).join('')}</div>
    <div class="small dim" style="margin-top:8px">Folders contribute every code and doc file inside them.</div>
   </div>
  </div>
  <div class="row" style="margin:14px 0 24px"><button class="btn primary" id="mapit">Map it</button><span class="small dim" id="mapnote">${S.charter?'the model will write an impact assessment from what it finds':''}</span></div>
  <div class="${cur?'split':''}"><div>${I.map(x=>`<div class="intk" data-intake="${esc(x.file)}"><b>${esc(x.title)}</b><div class="small dim">${x.created} · lanes ${esc(x.lanes)}</div></div>`).join('')||'<div class="empty">No intakes yet.</div>'}</div>
  ${cur?`<div class="card sticky mdtxt"><div class="row" style="justify-content:space-between"><b>${esc(cur.title)}</b><button class="btn sm" data-close>✕</button></div>${mdlite(cur.body.replace(/^---[\s\S]*?---\n/,''))}</div>`:''}</div>`;
 // repo browser
 async function showTree(rel){pickPath=rel;const items=await tree(rel);const parts=rel?rel.split('/'):[];
  $('#crumbs').innerHTML=`<a href="#" data-cd="">${esc(S.repo)}</a>`+parts.map((p,i)=>` / <a href="#" data-cd="${esc(parts.slice(0,i+1).join('/'))}">${esc(p)}</a>`).join('');
  $('#treelist').innerHTML=items.map(it=>`<div class="titem ${picked.has(it.path)?'on':''}"><span class="tpick" data-pick="${esc(it.path)}" title="use as context">${picked.has(it.path)?'●':'○'}</span>${it.dir?`<a href="#" data-cd="${esc(it.path)}">${esc(it.name)}/</a>`:`<span>${esc(it.name)}</span>`}</div>`).join('')||'<span class="small dim">empty</span>';
  document.querySelectorAll('[data-cd]').forEach(a=>a.onclick=e=>{e.preventDefault();showTree(a.dataset.cd)});
  document.querySelectorAll('[data-pick]').forEach(a=>a.onclick=()=>{const p=a.dataset.pick;picked.has(p)?picked.delete(p):picked.add(p);$('#picked').innerHTML=[...picked].map(p=>`<span class="chip on" data-unpick="${esc(p)}">${esc(p)} ✕</span>`).join('');bindUnpick();showTree(pickPath)});
 }
 function bindUnpick(){document.querySelectorAll('[data-unpick]').forEach(c=>c.onclick=()=>{picked.delete(c.dataset.unpick);intake()})}
 bindUnpick(); showTree(pickPath);
 // attachments
 const readFiles=files=>{[...files].forEach(f=>{const r=new FileReader();r.onload=()=>{attached.push({name:f.name,text:String(r.result||'').slice(0,200000)});$('#attlist').innerHTML=attached.map((a,i)=>`<span class="chip on" data-rm="${i}">${esc(a.name)} · ${Math.round(a.text.length/1000)}k ✕</span>`).join('');bindRm()};r.readAsText(f)})};
 function bindRm(){document.querySelectorAll('[data-rm]').forEach(c=>c.onclick=()=>{attached.splice(+c.dataset.rm,1);intake()})}
 bindRm();
 $('#pickfiles').onclick=e=>{e.preventDefault();$('#infile').click()};$('#infile').onchange=e=>readFiles(e.target.files);
 const dz=$('#drop');dz.ondragover=e=>{e.preventDefault();dz.classList.add('over')};dz.ondragleave=()=>dz.classList.remove('over');dz.ondrop=e=>{e.preventDefault();dz.classList.remove('over');readFiles(e.dataTransfer.files)};
 $('#mapit').onclick=async()=>{const t=$('#int').value.trim();if(!t){toast('describe the feature first');return}$('#mapit').disabled=true;$('#mapnote').textContent='mapping… the model is reading the brief, the code you pointed at, the ledger and the findings';
  const r=await act({type:'horizon',text:t,files:[...picked],brief:$('#inb').value,attachments:attached});$('#mapit').disabled=false;
  if(r.ok){selHorizon=r.file;picked=new Set();attached=[];toast('mapped');render()}};
 document.querySelectorAll('[data-intake]').forEach(el=>el.onclick=()=>{selHorizon=el.dataset.intake;render()});const c=document.querySelector('[data-close]');if(c)c.onclick=()=>{selHorizon=null;render()};
}
/* ---------- findings board */
function flaresPage(){
 const fs=findings().filter(m=>!q||(m.text+' '+JSON.stringify(m.meta)).toLowerCase().includes(q));
 $('#subtitle').textContent='';
 const openL=fs.filter(m=>['open','claimed','pr_open','needs_human','regressed'].includes(fstatus(m)));
 const sev=k=>openL.filter(m=>m.meta.severity===k).length;
 const m=sel&&byId()[sel];
 const sevOrder={critical:0,high:1,medium:2,low:3,note:4,info:5};
 const cols=FSTAT.filter(s=>fs.some(f=>fstatus(f)===s)||['open','claimed','pr_open','needs_human','fixed'].includes(s));
 $('#page').innerHTML=`${fs.length?statsRow([[openL.length,'open findings',`${fs.length} total`],[sev('critical'),'critical','',sev('critical')?'bad':''],[sev('high'),'high','',sev('high')?'warn':''],[sev('medium')+sev('low'),'medium & low',''],[fs.filter(m=>fstatus(m)==='needs_human').length,'need a human','could not reproduce / unclear',fs.filter(m=>fstatus(m)==='needs_human').length?'warn':''],[fs.filter(m=>fstatus(m)==='fixed').length,'fixed','']])+'<div style="height:18px"></div>':'<div class="empty">No findings yet. <code>cosmos flares import &lt;findings.json&gt; --prefix &lt;ID-PREFIX&gt;</code></div>'}
  ${fs.length?stepper([{icon:'imp',title:'Import or file',desc:'audit JSON, or flare: in a session',value:fs.length,unit:'flares',lit:true},{icon:'board',title:'Triage',desc:'kanban by lifecycle',value:openL.length,unit:'open',lit:openL.length},{icon:'human',title:'Claim / needs human',desc:'a person or the fix loop takes it',value:fs.filter(m=>['claimed','pr_open','needs_human'].includes(fstatus(m))).length,unit:'in progress',lit:fs.some(m=>['claimed','pr_open','needs_human'].includes(fstatus(m)))},{icon:'fix',title:'Fix',desc:'commit recorded',value:fs.filter(m=>fstatus(m)==='fixed').length,unit:'fixed',lit:fs.some(m=>fstatus(m)==='fixed')},{icon:'regress',title:'Regression watch',desc:'a fixed bug reported again is flagged',value:fs.filter(m=>fstatus(m)==='regressed').length,unit:'regressed',lit:fs.some(m=>fstatus(m)==='regressed')},{icon:'slack',title:'Slack',desc:'one card per finding, never twice'}],{compact:true,title:'The finding lifecycle'})+'<div style="height:14px"></div>':''}
  <div class="${m?'split':''}"><div class="board">${cols.map(s=>{const L=fs.filter(f=>fstatus(f)===s).sort((a,b)=>sevOrder[a.meta.severity]-sevOrder[b.meta.severity]);
   return `<div class="col"><h4><span>${s.replace('_',' ')}</span><span>${L.length}</span></h4>${L.map(f=>`<div class="fcard" data-id="${f.id}" style="--c:${cc(f.meta.severity)}"><div class="id">${esc(f.meta.audit_id)}${f.meta.area?' · '+esc(f.meta.area):''}</div><div class="t">${md(f.text)}</div>${f.files[0]?`<code>${esc(f.files[0])}</code>`:''}</div>`).join('')}</div>`}).join('')}</div>
  ${m?`<div class="sticky">${detail(m)}</div>`:''}</div>`;
 bindMem();bindDetail();
}
/* ---------- dreams */
function runRow(r,compact){return `<div class="run" data-run="${r.at}"><div><div class="when">${fmt(r.at)}</div><div class="small dim">${r.memories_total} memories after${r.llm_used?' · LLM':''}</div></div>
 <div class="stats"><span><b>${r.observations_processed}</b> observations</span><span><b style="color:var(--ok)">+${r.new.length}</b> new</span><span><b>${r.merged.length}</b> merged</span><span><b style="color:${r.contradictions.length?'var(--bad)':'var(--fg)'}">${r.contradictions.length}</b> contradictions</span><span><b style="color:var(--warn)">${r.superseded.length}</b> superseded</span><span><b>${r.stale.length}</b> stale</span>${r.recurated?`<span><b style="color:var(--acc)">${r.recurated}</b> re-curated · ${r.recurated_dropped||0} retired</span>`:''}</div>${compact?'':'<span class="muted">›</span>'}</div>`}
function dreams(){
 $('#subtitle').textContent='';
 const r=selRun&&S.dreams.find(x=>x.at===selRun);const B=byId();const t=id=>B[id]?esc(B[id].text.slice(0,90)):id;
 const L=(selRun&&S.dreams.find(x=>x.at===selRun))||S.dreams[0]||null;
 const lit=v=>v!==''&&v!=='0'&&v!==0;
 const ST=[
  {icon:'gather',title:'New observations',desc:'captured by hooks since the last dream',value:L?L.observations_processed:'',unit:'observations',lit:L&&L.observations_processed},
  {icon:'curate',title:'Model curates',desc:'keep · rewrite · category · lane',value:L?(L.recurated?L.recurated:(L.observations_processed||0)-(L.dropped||0)):'',unit:L?(L.recurated?`re-curated · ${L.recurated_dropped||0} retired`:(L.llm_used?`kept · ${L.dropped||0} dropped`:'no model')):'',lit:L&&L.llm_used,llm:true},
  {icon:'dedupe',title:'Dedupe',desc:'same fact twice → one memory, evidence +1',value:L?L.merged.length:'',unit:'merged',lit:L&&L.merged.length},
  {icon:'contra',title:'Contradictions',desc:'same subject, different claim → a human decides',value:L?L.contradictions.length:'',unit:'found',lit:L&&L.contradictions.length},
  {icon:'super',title:'Supersession',desc:'only with evidence: old files gone, or an explicit rule',value:L?L.superseded.length:'',unit:'superseded',lit:L&&L.superseded.length},
  {icon:'stale',title:'Staleness',desc:'evidence missing or not seen in months → review',value:L?L.stale.length:'',unit:'flagged',lit:L&&L.stale.length},
  {icon:'write',title:'Write',desc:'ledger · lanes · index · CLAUDE.md · AGENTS.md',value:L?L.memories_total:'',unit:'facts now'}];
 $('#page').innerHTML=`${stepper(ST,{title:'What a dream does',sub:L?`${selRun?'selected run':'last run'} ${fmt(L.at)} · ${L.llm_used?'model curated':'heuristics only'}`:'no run yet — press Run dream',foot:S.pending_observations?`<b style="color:var(--acc)">${S.pending_observations} observations</b> are waiting — press <b>Run dream</b>.`:'Nothing pending. Dreams that change nothing are not recorded.'})}
   <div class="${r?'split':''}"><div>${S.dreams.map(x=>runRow(x)).join('')||'<div class="empty">No dream has run yet.</div>'}</div>
  ${r?`<div class="card sticky"><div class="row" style="justify-content:space-between"><h3 style="margin:0">Run ${fmt(r.at)}</h3><button class="btn sm" data-close>✕</button></div>
   <div class="small muted" style="margin:6px 0 12px">${esc(r.summary)}</div>
   ${sec('New memories',r.new.map(n=>`<span class="badge cat" style="--c:${cc(n.category)}">${n.category}</span> <a href="#" data-go="${n.id}">${esc(n.text.slice(0,100))}</a>`))}
   ${sec('Merged into existing',r.merged.map(x=>`${esc(x.text.slice(0,70))} → <a href="#" data-go="${x.into}">${t(x.into)}</a>`))}
   ${sec('Contradictions (need a decision)',r.contradictions.map(x=>`<a href="#" data-go="${x.older}">${t(x.older)}</a> <span style="color:var(--bad)">↔</span> <a href="#" data-go="${x.newer}">${t(x.newer)}</a>`))}
   ${sec('Superseded by evidence',r.superseded.map(x=>`<s class="dim">${t(x.old)}</s> → <a href="#" data-go="${x.by}">${t(x.by)}</a>`))}
   ${sec('Stale candidates',r.stale.map(id=>`<a href="#" data-go="${id}">${t(id)}</a>`))}</div>`:''}</div>`;
 document.querySelectorAll('.run').forEach(el=>el.onclick=()=>{selRun=el.dataset.run;render()});const c=document.querySelector('[data-close]');if(c)c.onclick=()=>{selRun=null;render()};
 document.querySelectorAll('[data-go]').forEach(a=>a.onclick=e=>{e.preventDefault();sel=a.dataset.go;page=byId()[sel]&&byId()[sel].category==='finding'?'findings':'ledger';render()});
}
const sec=(t,items)=>items.length?`<div class="sect"><b class="small muted" style="text-transform:uppercase;letter-spacing:.5px">${t} · ${items.length}</b><div class="small">${items.map(i=>`<div style="padding:4px 0;border-bottom:1px solid var(--line)">${i}</div>`).join('')}</div></div>`:'';
/* ---------- verdicts */
function verdicts(){
 const B=byId();const seen=new Set();const pairs=[];
 for(const m of S.memories.filter(m=>m.status==='contradicted'))for(const c of m.contradicts){const k=[m.id,c].sort().join('|');if(seen.has(k)||!B[c])continue;seen.add(k);const [a,b]=[m,B[c]].sort((x,y)=>x.updated<y.updated?-1:1);pairs.push([a,b])}
 const stale=S.memories.filter(m=>m.status==='stale-candidate');const nh=needsHuman();
 $('#subtitle').textContent='';
 const side=(m,other,label)=>`<div class="side"><div class="small muted">${label} · ${m.source}</div><div style="font-weight:600;margin:6px 0">${md(m.text)}</div>${m.files.map(f=>`<code>${esc(f)}</code>`).join(' ')}
   <div class="actions"><button class="btn sm ok" data-keep="${m.id}" data-drop="${other.id}">Keep this</button></div></div>`;
 $('#page').innerHTML=`${statsRow([[pairs.length+stale.length+nh.length,'decisions waiting','on a human',pairs.length+stale.length+nh.length?'warn':''],[pairs.length,'contradictions','two facts disagree',pairs.length?'bad':''],[stale.length,'possibly out of date','evidence gone or not seen',stale.length?'warn':''],[nh.length,'findings need a human','could not reproduce / unclear',nh.length?'warn':'']])}
  ${stepper([{icon:'contra',title:'Conflict or doubt',desc:'two facts disagree · evidence vanished · finding unclear',value:pairs.length+stale.length+nh.length,unit:'items',lit:pairs.length+stale.length+nh.length},{icon:'evidence',title:'Evidence',desc:'files, dates, who saw it — shown side by side',lit:true},{icon:'human',title:'A person decides',desc:'keep · both valid · still true · forget'},{icon:'record',title:'Recorded',desc:'who, when, why — the decision becomes memory',value:S.memories.filter(m=>/Kept over|Reviewed|Verified|Forgotten/.test(m.reason||'')).length,unit:'decisions',lit:true}],{compact:true,title:'How verdicts work',foot:'Nothing here is decided by the machine.'})}
  ${pairs.length?`<h3 class="sec">Contradictions</h3>`+pairs.map(([a,b])=>`<div class="pair">${side(a,b,'older')}<div class="vs">VS<br><button class="btn sm" data-both="${a.id}" data-other="${b.id}" title="both statements are true">both</button></div>${side(b,a,'newer')}</div>`).join(''):''}
  ${stale.length?`<h3 class="sec" style="margin-top:28px">Possibly out of date</h3>`+stale.map(m=>`<div class="mem quiet" style="--c:${cc(m.category)};cursor:default"><div class="row" style="justify-content:space-between;align-items:start"><div><div class="t">${md(m.text)}</div><div class="m"><span class="badge cat" style="--c:${cc(m.category)}">${m.category}</span><span class="small dim">${esc(m.reason)}</span></div></div><div class="actions" style="margin:0;flex:none"><button class="btn sm ok" data-act2="verify" data-id="${m.id}">Still true</button><button class="btn sm bad" data-act2="forget" data-id="${m.id}">Forget</button></div></div></div>`).join(''):''}
  ${nh.length?`<h3 class="sec" style="margin-top:28px">Flares that need a human</h3>`+nh.map(m=>`<div class="card" style="margin-bottom:8px"><div class="row" style="justify-content:space-between"><div><span class="badge sev" style="--c:${cc(m.meta.severity)}">${SEVI[m.meta.severity]||''} ${esc(m.meta.audit_id)}</span> <b>${md(m.text)}</b><div class="small muted" style="margin-top:4px">${esc(m.meta.status_note||m.reason||'')}</div></div><div class="actions" style="margin:0"><button class="btn sm" data-fs2="claimed" data-id="${m.id}">Claim</button><button class="btn sm ok" data-fs2="fixed" data-id="${m.id}">Fixed</button><button class="btn sm warn" data-fs2="wontfix" data-id="${m.id}">Won't fix</button><button class="btn sm bad" data-fs2="withdrawn" data-id="${m.id}">Withdraw</button></div></div></div>`).join(''):''}
  ${pairs.length+stale.length+nh.length?'':'<div class="empty">✓ Nothing needs a decision. The ledger is consistent.</div>'}`;
 document.querySelectorAll('[data-keep]').forEach(b=>b.onclick=()=>act({type:'keep',id:b.dataset.keep,drop:b.dataset.drop,note:prompt('Why keep this one? (optional)')||''}));
 document.querySelectorAll('[data-both]').forEach(b=>b.onclick=()=>act({type:'both_valid',id:b.dataset.both,other:b.dataset.other,note:prompt('Why are both true? (optional)')||''}));
 document.querySelectorAll('[data-act2]').forEach(b=>b.onclick=()=>act({type:b.dataset.act2,id:b.dataset.id}));
 document.querySelectorAll('[data-fs2]').forEach(b=>b.onclick=()=>act({type:'finding_status',id:b.dataset.id,status:b.dataset.fs2,note:prompt('Note (optional)')||''}));
}
/* ---------- activity */
function obsRow(o){return `<div class="ev"><span><span class="badge cat" style="--c:${cc(o.category)}">${esc(o.category)}</span>${o.source==='explicit'?' <span class="badge" style="color:var(--acc2)">explicit</span>':''}</span><span>${md(o.text)}<div class="small dim">${esc(o.author||'')}${o.files&&o.files[0]?' · <code>'+esc(o.files[0])+'</code>':''}</div></span></div>`}
function jRow(o){const files=o.files||[];return `<div class="ev"><span class="small dim">${esc((o.ts||'').slice(11,16))}<br>${esc(o.author||'')}</span><span>${o.ask?`<div>${esc(o.ask)}</div>`:''}<div class="small" style="margin-top:3px">${(o.commits||[]).map(c=>'<code>'+esc(c)+'</code>').join(' ')}${files.length?` <span class="dim">· ${files.length} file${files.length===1?'':'s'}${files[0]?' · <code>'+esc(files[0])+'</code>':''}</span>`:''}${o.tests?' <span class="badge" style="color:var(--ok)">tests ran</span>':''}${o.branch?` <span class="dim">· ${esc(o.branch)}</span>`:''}</div></span></div>`}
function activity(){
 const J=S.observations.filter(o=>o.kind==='journal'), F=S.observations.filter(o=>o.kind!=='journal');
 const obs=F.filter(o=>!q||(o.text||'').toLowerCase().includes(q));
 const jq=J.filter(o=>!q||((o.ask||'')+' '+(o.commits||[]).join(' ')).toLowerCase().includes(q));
 const commits=J.reduce((n,o)=>n+((o.commits||[]).length),0);
 const jDay={}; for(const o of J){const d=(o.ts||'').slice(0,10)||'unknown';(jDay[d]=jDay[d]||[]).push(o)}
 const jDays=Object.keys(jDay).sort().reverse();
 $('#subtitle').textContent='';
 const byAgent={}, byCat={}, byDay={};
 for(const o of F){byAgent[o.agent||'claude']=(byAgent[o.agent||'claude']||0)+1;byCat[o.category]=(byCat[o.category]||0)+1;const d=(o.ts||'').slice(0,10)||'unknown';(byDay[d]=byDay[d]||[]).push(o)}
 const days=Object.keys(byDay).sort().reverse();
 const stat=(v,l,sub,tone)=>`<div class="stat2 ${tone||''}"><div class="v">${v}</div><div class="l">${l}</div>${sub?`<div class="s">${sub}</div>`:''}</div>`;
 const HOOKS=[['SessionStart','charter · facts · atlas status injected'],['UserPromptSubmit','facts + findings for the files you name'],['Stop','capture observations · run the Gate'],['PreCompact','capture before context is compressed'],['SessionEnd','final capture']];
 $('#page').innerHTML=`
 <div class="stats2">
  ${stat(J.length,'journal entries','what was done, per turn',J.length?'':'')}
  ${stat(commits,'commits recorded','from the journal')}
  ${stat(F.length,'observations','candidate facts from sessions')}
  ${stat(S.pending_observations,'waiting for a dream',S.pending_observations?'press Run dream':'all consolidated',S.pending_observations?'warn':'')}
  ${stat(S.sessions,'sessions','read so far')}
  ${stat(Object.keys(byAgent).length,'agents',Object.entries(byAgent).map(([a,n])=>`${a} ${n}`).join(' · ')||'—')}
  ${stat(S.hooks.length,'hooks armed',S.hooks.length===5?'all five':'run cosmos init')}
 </div>
 ${stepper([{icon:'session',title:'Session',desc:'someone works with their agent',value:S.sessions,unit:'sessions',lit:S.sessions},{icon:'hook',title:'Hooks fire',desc:'Stop · PreCompact · SessionEnd',value:S.hooks.length,unit:'armed',lit:S.hooks.length},{icon:'gather',title:'Observations + journal',desc:'durable sentences and one work line per turn; secrets redacted, no transcripts',value:F.length,unit:'captured',lit:F.length},{icon:'curate',title:'Next dream',desc:'runs by itself when enough is waiting; the model turns them into facts',value:S.pending_observations,unit:'waiting',lit:S.pending_observations,llm:true}],{compact:true,title:'How activity becomes memory'})}
 <div class="grid g2" style="margin-top:26px;align-items:start">
  <div>
   <h3 class="sec">Journal</h3>
   <div class="small dim" style="margin:-6px 0 14px">One line per agent turn: what was asked, what was edited, which commits landed. Kept in <code>.cosmos/ledger/journal/</code> after each dream.</div>
   ${jDays.length?jDays.slice(0,14).map(d=>`<div class="day"><div class="dayhead"><span>${d}</span><span class="dim">${jDay[d].length}</span></div>${jDay[d].filter(o=>jq.includes(o)).map(jRow).join('')}</div>`).join(''):'<div class="empty">No journal yet — it starts with the next agent turn.</div>'}
   <h3 class="sec" style="margin-top:28px">What was captured</h3>
   <div class="small dim" style="margin:-6px 0 14px">Durable facts pulled from sessions, newest first. Each becomes a ledger fact on the next dream.</div>
   ${days.length?days.slice(0,30).map(d=>`<div class="day"><div class="dayhead"><span>${d}</span><span class="dim">${byDay[d].length}</span></div>${byDay[d].filter(o=>obs.includes(o)).map(obsRow).join('')}</div>`).join(''):'<div class="empty">Nothing captured yet — work in your agent; the Stop hook does the rest.</div>'}
  </div>
  <div>
   <h3 class="sec">Hooks</h3>
   <div class="small dim" style="margin:-6px 0 14px">Wired into <code>.claude/settings.json</code>. They finish in milliseconds and never block a session.</div>
   <div class="hooklist">${HOOKS.map(([h,d])=>`<div class="hook ${S.hooks.includes(h)?'on':''}"><span class="dot"></span><div><div class="hn">${h}</div><div class="hd">${d}</div></div><span class="hs">${S.hooks.includes(h)?'armed':'missing'}</span></div>`).join('')}</div>
   <h3 class="sec" style="margin-top:28px">By kind</h3>
   <div class="kinds">${Object.entries(byCat).sort((a,b)=>b[1]-a[1]).map(([c,n])=>`<div class="kind"><span class="badge cat" style="--c:${cc(c)}">${c}</span><span class="bar"><i style="width:${Math.round(100*n/Math.max(1,S.observations.length))}%;background:${cc(c)}"></i></span><span class="n">${n}</span></div>`).join('')||'<span class="dim small">—</span>'}</div>
   ${S.hooklog.length?`<h3 class="sec" style="margin-top:28px">Hook log</h3><pre class="log">${esc(S.hooklog.slice().reverse().slice(0,40).join('\n'))}</pre>`:''}
  </div>
 </div>`;
}
/* ---------- docs */
function docs(){
 $('#subtitle').textContent='everything you need to run cosmos on this repo';
 const repo=esc(S.repo);
 const step=(n,t,body)=>`<div class="step"><div class="no">${n}</div><div><b>${t}</b><div class="small" style="margin-top:2px">${body}</div></div></div>`;
 const SECTIONS=[
 ['roles','0 · What it means for each role',`
  <table><tr><th>role</th><th>the complaint</th><th>what changes</th></tr>
  <tr><td><b>Product manager</b></td><td>"I keep adding features and the app gets more confusing; nobody tells me what a feature collides with until it is half built."</td><td><b>Horizon</b> answers before a line is written: lanes touched, decisions it collides with, findings in the way, who owns that area. The <b>Atlas</b> shows the real shape of the product, always current.</td></tr>
  <tr><td><b>Project manager</b></td><td>"Three people ended up in the same feature. Every call repeats the same three asks. I cannot see who knows what."</td><td><b>Lanes</b> show who is active where and flag overlap this month. The <b>Gate</b> asks the three questions so the call does not have to. <b>Dreams</b> and <b>Verdicts</b> give a weekly rhythm: consolidate, decide, commit.</td></tr>
  <tr><td><b>Developer</b></td><td>"I re-learn the codebase every session. My AI writes in a different style from my teammate's. I did not know that constraint existed."</td><td>The <b>Ledger</b> hands over what others learned, matched to the files you touch. The <b>Charter</b> makes every AI write the same way. <code>remember:</code> keeps what you found in ten seconds.</td></tr>
  <tr><td><b>QA</b></td><td>"My findings live in a document nobody reopens. Fixed bugs come back. Nobody tells me when a finding is picked up."</td><td><b>Flares</b> have a lifecycle and a board; a fixed bug reported again is flagged <i>regressed</i>; an open finding on a file the AI edits is raised at the Gate; cards go to Slack once, with reactions to claim or close.</td></tr>
  <tr><td><b>Tech lead / architect</b></td><td>"There is no diagram, or it is a month old. Decisions live in people's heads."</td><td>The <b>Atlas</b> is generated from the repo and drift-checked. Every decision in the Ledger carries its reason, evidence and date; contradictions surface instead of silently coexisting.</td></tr></table>`],
 ['agents','1 · Works with every agent',`
  <p>One store, every tool. Claude Code, Codex (CLI and Desktop), Gemini CLI, Antigravity, Cursor, GitHub Copilot, Cline, Windsurf and Cowork all read the same Charter, Ledger and Atlas — three ways:</p>
  <table><tr><th>how</th><th>what</th><th>agents</th></tr>
  <tr><td>Instruction files</td><td>the same managed block written to <code>CLAUDE.md</code>, <code>AGENTS.md</code>, <code>GEMINI.md</code>, <code>.cursor/rules/cosmos.mdc</code>, <code>.github/copilot-instructions.md</code>, <code>.clinerules</code>, <code>.windsurfrules</code></td><td>all</td></tr>
  <tr><td>MCP server</td><td><code>cosmos mcp</code> — tools: <code>cosmos_recall</code>, <code>cosmos_remember</code>, <code>cosmos_flare</code>, <code>cosmos_charter</code>, <code>cosmos_why</code>, <code>cosmos_horizon</code>, <code>cosmos_atlas</code>, <code>cosmos_lanes</code>. Configured by <code>cosmos connect</code> in <code>.mcp.json</code>, <code>.cursor/mcp.json</code>, <code>.gemini/settings.json</code>, <code>.vscode/mcp.json</code>; Codex via <code>~/.codex/config.toml</code>; Cowork via Settings → Connectors.</td><td>all MCP clients</td></tr>
  <tr><td>Capture</td><td>Claude Code: hooks, automatic. Codex: <code>cosmos capture --agent codex</code> reads <code>~/.codex/sessions</code> rollouts (exact format). Gemini / Antigravity: best-effort JSON reader. Any agent: <code>cosmos_remember</code> over MCP.</td><td>Claude Code · Codex · Gemini · any via MCP</td></tr></table>
  <pre>cosmos connect all            # instruction files + MCP configs for every agent
cosmos connect codex --write-user
cosmos capture --agent all    # pull facts out of Claude, Codex and Gemini sessions</pre>
  <p><b>Shareable:</b> everything is in <code>.cosmos/</code> and the instruction files — commit and push, and every teammate on every tool has it. <code>cosmos ui --static</code> makes a read-only snapshot page for people outside the repo.</p>`],
 ['link','2 · Link an existing codebase & past sessions',`
  <p>Most projects already have months of history. Bring it in: initialise, read the old sessions, import the audit, consolidate, draw the architecture, wire every agent, commit on a branch.</p>
  <pre>cd &lt;your-repo&gt; &amp;&amp; cosmos init
cosmos capture --agent claude --transcript &lt;path-to-session&gt;.jsonl -v      <span style="color:var(--dim)"># one session</span>
cosmos capture --agent all -v                                             <span style="color:var(--dim)"># every Claude, Codex, Gemini session on this repo</span>
cosmos flares import &lt;findings.json&gt; --prefix &lt;ID-PREFIX&gt; --source &lt;report-name&gt;
cosmos flares slack --seed-state &lt;legacy .slack-posted.json&gt; --prefix &lt;ID-PREFIX&gt; --status
cosmos dream &amp;&amp; cosmos review &amp;&amp; cosmos lanes &amp;&amp; cosmos ui
cosmos atlas          <span style="color:var(--dim)"># then: claude → /atlas</span>
cosmos connect all
cosmos charter edit
git checkout -b cosmos/init origin/&lt;base-branch&gt;
git add .cosmos .claude/settings.json .claude/commands .mcp.json CLAUDE.md AGENTS.md GEMINI.md .gitignore
git commit -m "cosmos: charter, ledger, atlas, findings" &amp;&amp; git push -u origin cosmos/init</pre>
  <p><b>Already-open sessions</b> keep running without cosmos until restarted — hooks are read at session start: <code>claude --resume &lt;session-id&gt;</code>. Transcripts live in <code>~/.claude/projects/&lt;repo path, slashes → dashes&gt;/</code> (Claude Code), <code>~/.codex/sessions/</code> (Codex), <code>~/.gemini/</code> (Gemini). Transcripts are read, never stored; secrets are redacted.</p>`],
 ['start','3 · Getting started (a new repo)',`
  <div class="callout">Memory travels with the code. One person sets cosmos up and commits it; everyone else just clones.</div>
  <h3 class="small muted">FIRST PERSON ON THE REPO (once)</h3>
  <pre>pip install cosmos-dev
cd ${repo}
cosmos init
git add .cosmos .claude/settings.json CLAUDE.md AGENTS.md .gitignore
git commit -m "cosmos: ledger"</pre>
  <p><code>cosmos init</code> creates <code>.cosmos/</code> (config, ledger, observations, a <code>cosmosw</code> wrapper + vendored copy), wires five hooks into <code>.claude/settings.json</code>, writes the managed block in <code>CLAUDE.md</code>/<code>AGENTS.md</code>, and makes the ledger an Obsidian vault.</p>
  <h3 class="small muted">EVERYONE AFTER THAT</h3>
  <pre>git clone &lt;repo&gt; &amp;&amp; cd ${repo} &amp;&amp; claude</pre>
  <p>No install, no init. The hooks call <code>.cosmos/cosmosw</code>, which runs the vendored copy when <code>cosmos</code> is not installed. Their first session starts with the team's top facts already in context.</p>
  <p>Optional for the short command name: <code>pip install cosmos-dev</code>. Check the setup any time with <code>cosmos doctor</code>.</p>`],
 ['daily','4 · Daily use (nothing to do)',`
  ${step(1,'Work with Claude Code as usual','On <b>SessionStart</b> the top facts are injected. On every <b>UserPromptSubmit</b> the memories relevant to your prompt (by words and by the files they anchor to) are injected — including open findings on those files.')}
  ${step(2,'Cosmos captures silently','On <b>Stop</b>, <b>PreCompact</b> and <b>SessionEnd</b> the transcript is read incrementally and durable facts are extracted: architecture, decisions, conventions, constraints, bug root causes, dependency limits, workflows, domain rules. Narration, questions and one-off tasks are dropped. Secrets are redacted before anything touches disk; transcripts are never stored.')}
  ${step(3,'Force a memory when you want one','Type <code>remember: never modify prod schemas by hand</code> or <code>flare: /transitions has no role gate</code> in the chat — or use the <b>+ Remember</b> box on the Ledger page, or <code>cosmos remember "…" -c constraint</code>.')}
  ${step(4,'Ask why','<code>cosmos why redis</code> — evidence files, dates, who saw it, what it superseded. Or click any card here.')}`],
 ['dream','5 · Dreams (consolidation)',`
  <p>Observations pile up per developer. A <b>dream</b> turns them into the shared ledger: normalize → dedupe (same fact twice = one memory, evidence +1) → contradiction check → evidence-based supersession → staleness → optional LLM refinement → write notes, index, CLAUDE.md/AGENTS.md.</p>
  <pre>cosmos dream            # or the "Run dream" button top-right
cosmos review           # what needs a human
git add .cosmos CLAUDE.md AGENTS.md &amp;&amp; git commit -m "memory: dream" &amp;&amp; git push</pre>
  <p>Run it when the Activity badge shows pending observations, or nightly in CI (a workflow example is in the README). Dreams are idempotent. Every run is recorded on the <b>Dreams</b> page.</p>
  <p><b>The model does the thinking.</b> Every dream sends new observations to the model, which keeps or drops each one, rewrites it, names its category and its feature lane; it also adjudicates contradictions and proposes lane mappings. Default provider is your <b>Claude Code login</b> (<code>claude -p</code>) — nothing to configure. Alternatives in <code>.cosmos/config.json → llm.provider</code>: <code>anthropic</code> (API key), <code>openai</code>, <code>ollama</code>, <code>none</code>. Every answer is validated against real ids, paths and enums before it touches the ledger. <code>cosmos doctor</code> shows which provider is live; without one, dreams run on heuristics and say so.</p>`],
 ['charter','6 · Charter & Gate',`
  <p><b>Ledger vs Charter.</b> The Ledger holds <i>facts about the code</i> — what is true (Redis is used for locks; this endpoint is public). The Charter holds <i>rules about how the team works</i> — what to do (run tests before stopping; refer to code as file:line). Facts are mostly captured; rules are written by people. Both reach every session; rules first.</p>
  <p><b>Charter</b> — <code>.cosmos/charter.md</code>, the team's working agreement: how we write code, test, point at things, review our own work, architecture rules. Committed, changed in PRs, injected into every AI session at SessionStart so nobody's personal style leaks into the codebase. Add a rule here on the Charter page, with <code>cosmos charter add "…"</code>, or by typing <code>remember: …</code> in a session.</p>
  <p><b>Gate</b> — runs when Claude stops. If the turn edited code but ran no tests, cited no <code>file:line</code>, or ignored an open finding on a touched file, Claude is handed the exact list and continues; a turn is held at most once. Docs-only edits are never gated. Configure in the charter's <code>gate:</code> line.</p>
  <pre>cosmos charter | charter add "Never call the DB from a controller" | charter edit | charter gate
cosmos gate            # effective rules
cosmos gate --transcript ~/.claude/projects/&lt;repo&gt;/&lt;session&gt;.jsonl   # dry run</pre>`],
 ['atlas','7 · Atlas & Lanes',`
  <p><b>Atlas</b> — architecture generated from the repository: manifests, docker-compose, k8s, Terraform, OpenAPI, <code>.env.example</code>, README → inventory, containers and deployment diagrams (Mermaid), API surface. Every source is hashed; when the code moves and the picture does not, everyone sees <i>drift</i> at SessionStart, in dreams and on the Atlas page. <code>/atlas</code> in Claude Code runs the deeper LLM pass (dependency index, data flows, proposed lanes).</p>
  <p><b>Lanes</b> — every fact, finding and diagram is filed under the feature/module it belongs to, inferred from its files (or configured in <code>config.json → lanes</code>). The Lanes page shows facts, open findings and the people active in each lane over the last 30 days, and flags overlap.</p>
  <pre>cosmos atlas            # build · cosmos atlas --check   # drift
cosmos lanes [--days 30]</pre>`],
 ['horizon','8 · Horizon',`
  <p>A feature enters with a map, not a Slack message. <code>cosmos horizon "bulk invite with partial success" -f path/hint.py</code> answers, from what the repo already knows: lanes touched (with overlap warnings), recorded decisions it collides with, open findings in the way, who has been working there, a suggested owner. Saved under <code>.cosmos/ledger/intake/</code> so the PR that implements the feature carries its own impact note.</p>`],
 ['approve','9 · Verdicts (the human gate)',`
  <p>Three things are never decided automatically; they wait on the <b>Verdicts</b> page (and <code>cosmos review</code>):</p>
  <table><tr><th>item</th><th>why it appears</th><th>your options</th></tr>
  <tr><td>Contradiction</td><td>two active facts about the same subject disagree (different technology, or one negated)</td><td><b>Keep this</b> (other becomes <i>superseded</i> with your reason) · <b>both</b> valid</td></tr>
  <tr><td>Stale candidate</td><td>evidence files disappeared, or not re-observed within the category limit</td><td><b>Still true</b> (verified today) · <b>Forget</b></td></tr>
  <tr><td>Finding needs a human</td><td>the fix loop could not reproduce it or the intent is ambiguous</td><td><b>Claim</b> · <b>Fixed</b> · <b>Won't fix</b> · <b>Withdraw</b> (+ note)</td></tr></table>
  <p>Supersession happens without you only when evidence is unambiguous: the old fact's files are gone and the new fact's exist, or a developer's explicit rule contradicts an inferred fact. Explicit rules always outrank inferred ones.</p>`],
 ['flares','10 · Flares (QA findings lifecycle)',`
  <pre>open → claimed → pr_open → fixed
                 ↘ needs_human → (human) fixed | wontfix | withdrawn
fixed/wontfix reported again by a later audit → regressed ⚠️</pre>
  <table><tr><th>stage</th><th>how</th></tr>
  <tr><td>Report</td><td>An audit session writes <code>qa-findings.json</code> → <code>cosmos flares import docs/qa-findings.json --prefix QA</code>. Same id = update, never a duplicate. Or type <code>flare: …</code> in a session.</td></tr>
  <tr><td>Triage</td><td><b>Flares</b> board, kanban by status. Click a card for What / Impact / Evidence / Fix.</td></tr>
  <tr><td>Fix</td><td><code>cosmos flares claim QA-12</code> → <code>pr-open</code> → <code>fix QA-12 "PR #<n>"</code> (records the commit). Or the buttons in the card. Or the QA fix loop, which writes <code>status</code>/<code>status_note</code>/<code>status_at</code> into the JSON — re-import is the sync point; an incoming <i>open</i> never downgrades a local <i>claimed</i>.</td></tr>
  <tr><td>Withdraw</td><td><code>cosmos flares withdraw QA-8 "shared reference data by design"</code>. Kept forever so nobody re-files it; hidden from retrieval.</td></tr>
  <tr><td>Publish</td><td><code>cosmos flares slack --validate</code> → <code>cosmos flares slack --send --channel C…</code> (token from <code>SLACK_BOT_TOKEN</code> only). One Block Kit card per open finding, 👀 ✅ 🚫 pre-seeded, never double-posts. <code>--convert</code> rewrites already-posted messages in place.</td></tr>
  <tr><td>Report</td><td><code>cosmos flares report -o docs/qa-audit.md</code> regenerates the full report from the ledger. <code>cosmos flares export</code> writes the JSON back.</td></tr>
  <tr><td>Lint</td><td><code>cosmos flares lint …</code> flags repository filter keys that are not real model columns (the bug class behind two findings).</td></tr></table>
  <p>Severity <code>note</code> items are verification notes: no lifecycle, never claimable.</p>`],
 ['obsidian','11 · Obsidian & other agents',`
  <p>The ledger <b>is</b> a vault: one markdown note per fact with frontmatter, <code>[[wikilinks]]</code> between related / contradicting / superseding facts, <code>_index.md</code> as the map of content, graph colours per category.</p>
  <pre>cosmos obsidian --open                 # open this ledger in Obsidian
cosmos obsidian --vault ~/Obsidian/Team  # link several repos' ledgers into one vault</pre>
  <p>Edits in Obsidian are real: reword the title line, change <code>status</code>, then <code>cosmos render</code>.</p>
  <p><code>AGENTS.md</code> carries the same managed block as <code>CLAUDE.md</code>, so Codex, Cursor, Gemini CLI and Copilot read the same facts.</p>`],
 ['cli','12 · Command reference',`
  <table>
  <tr><th>command</th><th>does</th></tr>
  <tr><td><code>cosmos init [--no-vendor]</code></td><td>set up this repo (charter, hooks, ledger, atlas, /atlas command, wrapper, CLAUDE.md/AGENTS.md block, vault)</td></tr>
  <tr><td><code>cosmos charter [show|add|edit|gate]</code> · <code>gate [--transcript F]</code></td><td>the working agreement · the Stop-hook checklist</td></tr>
  <tr><td><code>cosmos atlas [--check]</code> · <code>lanes [--days N]</code> · <code>horizon "…" [-f F]</code></td><td>architecture from the repo · feature lanes and overlap · map a feature before coding</td></tr>
  <tr><td><code>cosmos connect [all|claude|codex|gemini|cursor|copilot|cline|windsurf]</code> · <code>mcp</code> · <code>capture --agent all</code></td><td>wire every agent · the MCP server · read other agents' session logs</td></tr>
  <tr><td><code>cosmos status</code> · <code>doctor</code> · <code>health</code></td><td>quick state · installation check · memory quality metrics</td></tr>
  <tr><td><code>cosmos ui</code> [<code>--static</code>] · <code>ledger --obsidian</code></td><td>this control room · read-only snapshot HTML · open the vault</td></tr>
  <tr><td><code>cosmos capture [--transcript F]</code></td><td>backfill from existing Claude transcripts of this repo</td></tr>
  <tr><td><code>cosmos dream [--llm|--no-llm]</code></td><td>consolidate observations into the ledger</td></tr>
  <tr><td><code>cosmos review</code></td><td>list contradictions and stale candidates</td></tr>
  <tr><td><code>cosmos remember "…" [-c CAT] [-f FILE]</code></td><td>add an explicit rule (highest priority)</td></tr>
  <tr><td><code>cosmos why &lt;id|text&gt;</code> · <code>search &lt;q&gt; [-f FILE]</code></td><td>explain a fact · rank facts for a query / file</td></tr>
  <tr><td><code>cosmos verify ID [--resolve]</code> · <code>forget ID</code></td><td>mark verified (and supersede what it contradicts) · retire</td></tr>
  <tr><td><code>cosmos render</code></td><td>rewrite CLAUDE.md/AGENTS.md block and ledger index</td></tr>
  <tr><td><code>cosmos update</code> · <code>uninstall</code></td><td>refresh the vendored copy · remove hooks</td></tr>
  <tr><td><code>cosmos flares import|list|show|claim|pr-open|needs-human|fix|wontfix|withdraw|reopen|set|export|report|slack|lint</code></td><td>QA findings lifecycle (section 5)</td></tr>
  </table>
  <p class="small dim">Teammates without an install: prefix with <code>.cosmos/cosmosw</code>, e.g. <code>.cosmos/cosmosw status</code>.</p>`],
 ['config','13 · Configuration & layout',`
  <pre>${esc(JSON.stringify(S.config,null,2))}</pre>
  <p><code>.cosmos/config.json</code> — committed. Notable keys: <code>capture.min_score</code> (extraction threshold), <code>privacy.author</code> (<i>git</i> | <i>anonymous</i>), <code>retrieval.session_start_max</code> / <code>prompt_max</code>, <code>dream.staleness_days</code> per category, <code>ignore</code> globs (facts anchored only on ignored paths are dropped).</p>
  <pre>.cosmos/
  config.json          committed
  cosmosw            wrapper (committed) · vendor/ vendored copy
  ledger/               Obsidian vault, one note per fact — committed
  observations/        sanitized JSONL, day-partitioned — committed (so CI can dream)
  state/               per-machine offsets, dream runs, hook.log, slack-posted.json — gitignored</pre>
  <p><b>Privacy:</b> hooks always exit 0 and never block a session; transcripts are never stored; API keys, tokens (incl. Slack xox*/xapp-), passwords, private keys and credentials in URLs are redacted before persistence; nothing is sent anywhere unless you run <code>audit slack --send</code> or enable an LLM provider.</p>`]];
 $('#page').innerHTML=`<div class="docs"><div class="toc">${SECTIONS.map(([id,t])=>`<a href="#doc-${id}">${t.replace(/^\d+ · /,'')}</a>`).join('')}</div><div class="doc card">${SECTIONS.map(([id,t,b])=>`<h2 id="doc-${id}">${t}</h2>${b}`).join('')}</div></div>`;
 document.querySelectorAll('.toc a').forEach(a=>a.onclick=e=>{e.preventDefault();document.querySelector(a.getAttribute('href')).scrollIntoView({behavior:'smooth',block:'start'})});
}
/* ---------- wiring */
document.querySelectorAll('nav i[data-ic]').forEach(i=>{i.innerHTML='<svg viewBox="0 0 24 24" aria-hidden="true">'+ICONS[i.dataset.ic]+'</svg>'});
document.querySelectorAll('nav button').forEach(b=>b.onclick=()=>{page=b.dataset.p;sel=null;render()});
$('#q').oninput=e=>{q=e.target.value.toLowerCase();render()};
$('#dream').onclick=async()=>{$('#dream').textContent='💤 dreaming…';$('#dream').disabled=true;const r=await act({type:'dream'});$('#dream').textContent='💤 Run dream';$('#dream').disabled=false;if(r.ok){toast(r.report.summary);page='dreams';selRun=S.dreams[0]&&S.dreams[0].at;render()}};
$('#capture').onclick=async()=>{$('#capture').disabled=true;const r=await act({type:'capture'});$('#capture').disabled=false;if(r.ok)toast(`captured ${r.captured} observation(s)`)};
window.addEventListener('resize',()=>{if(page==='ledger'&&!sel)render()});
load();
</script></body></html>"""
