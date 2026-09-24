"""`cosmos mcp`: a Model Context Protocol server over stdio - the one point of contact for every agent.

Claude Code, Codex, Gemini CLI, Cursor, Copilot, Cline and Cowork all speak MCP. This server exposes the
ledger, charter, atlas, lanes and intake as tools, so any agent can recall, remember and file findings into the
same git-tracked store. Standard library only; newline-delimited JSON-RPC 2.0 as the MCP stdio transport requires.
"""
from __future__ import annotations

import json
import re
import sys
from typing import Any, Dict, List

from . import __version__
from .config import Config, git_author, load_config
from .store import Ledger, Memory, make_id, today

PROTOCOL = "2025-06-18"

ICON = "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCA2NCA2NCI+PHJlY3Qgd2lkdGg9IjY0IiBoZWlnaHQ9IjY0IiByeD0iMTIiIGZpbGw9IiMwNTA1MDYiLz48bGluZSB4MT0iMzIiIHkxPSI2IiB4Mj0iMzIiIHkyPSI1OCIgc3Ryb2tlPSIjRUNFQUU0IiBzdHJva2Utd2lkdGg9IjEuNSIvPjxjaXJjbGUgY3g9IjMyIiBjeT0iMzIiIHI9IjE1IiBmaWxsPSIjMDUwNTA2IiBzdHJva2U9IiNFQ0VBRTQiIHN0cm9rZS13aWR0aD0iMS42Ii8+PGNpcmNsZSBjeD0iMzIiIGN5PSIzMiIgcj0iOSIgZmlsbD0ibm9uZSIgc3Ryb2tlPSIjRThDRkEwIiBzdHJva2Utd2lkdGg9IjEuNiIvPjwvc3ZnPgo="

TOOLS: List[Dict[str, Any]] = [
    {"name": "cosmos_recall", "description": "Team facts, rules and open findings relevant to a task. Call before changing code you did not write. Pass the files you are about to touch.",
     "inputSchema": {"type": "object", "properties": {"query": {"type": "string", "description": "what you are about to do"}, "files": {"type": "array", "items": {"type": "string"}}, "k": {"type": "integer", "default": 8}}, "required": ["query"]}},
    {"name": "cosmos_remember", "description": "Record durable team knowledge. kind=fact (default): something the agent learned about the codebase this turn - architecture, a decision with its reason, a constraint, a correction the user made. kind=rule: something the user stated as a team rule (outranks facts). Not for task progress.",
     "inputSchema": {"type": "object", "properties": {"text": {"type": "string"}, "kind": {"type": "string", "enum": ["fact", "rule"], "default": "fact"}, "category": {"type": "string", "enum": ["architecture", "decision", "convention", "constraint", "bug", "dependency", "workflow", "domain", "rejected"], "default": "convention"}, "lane": {"type": "string", "description": "feature or module, kebab-case"}, "files": {"type": "array", "items": {"type": "string"}}, "importance": {"type": "number"}}, "required": ["text"]}},
    {"name": "cosmos_flare", "description": "File a QA / security finding with a lifecycle (open → claimed → fixed …).",
     "inputSchema": {"type": "object", "properties": {"title": {"type": "string"}, "severity": {"type": "string", "enum": ["critical", "high", "medium", "low"], "default": "medium"}, "locations": {"type": "string", "description": "file:line list"}, "what": {"type": "string"}, "impact": {"type": "string"}, "fix": {"type": "string"}}, "required": ["title"]}},
    {"name": "cosmos_handoff", "description": "Leave a handoff for whoever continues this branch (any machine): what was learned, what is open, what to do next. Use it when stopping mid-work; a finished turn needs none (its final message is kept automatically).",
     "inputSchema": {"type": "object", "properties": {"learned": {"type": "string"}, "open": {"type": "string"}, "next": {"type": "string"}, "branch": {"type": "string"}}, "required": ["next"]}},
    {"name": "cosmos_charter", "description": "The team's working agreement: coding style, testing, how to point at code, self-review, architecture rules. Read it before writing code.", "inputSchema": {"type": "object", "properties": {}}},
    {"name": "cosmos_why", "description": "Explain a fact: evidence files, timeline, who saw it, contradictions.", "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}},
    {"name": "cosmos_horizon", "description": "Map a feature before coding: lanes touched, colliding decisions, open findings in the way, people active there, model assessment. Pass folders/files it will touch and the brief text if you have it.", "inputSchema": {"type": "object", "properties": {"text": {"type": "string"}, "files": {"type": "array", "items": {"type": "string"}}, "brief": {"type": "string"}}, "required": ["text"]}},
    {"name": "cosmos_atlas", "description": "Architecture status and diagrams (inventory, containers, deployment, api) generated from the repo, with drift status.", "inputSchema": {"type": "object", "properties": {"doc": {"type": "string", "enum": ["status", "inventory", "containers", "deployment", "api", "dependencies", "data-flow", "system-context"], "default": "status"}}}},
    {"name": "cosmos_lanes", "description": "Feature lanes: facts, open findings and people active per lane; overlap warnings.", "inputSchema": {"type": "object", "properties": {"days": {"type": "integer", "default": 30}}}},
]


def _txt(s: str) -> Dict[str, Any]:
    return {"content": [{"type": "text", "text": s}]}


def call_tool(cfg: Config, name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    from .render import render_all
    mems = Ledger(cfg.paths).load()
    if name == "cosmos_recall":
        from .retrieve import format_for_agent, retrieve
        from .charter import rules
        hits = retrieve(mems, str(args.get("query", "")), paths=args.get("files") or [], k=int(args.get("k", 8)))
        rs = [m for m in rules(mems) if m not in hits][:5]
        out = format_for_agent(hits, "cosm◎s · what the team knows:") or "cosm◎s · no recorded facts match yet."
        if rs:
            out += "\n\nExplicit team rules:\n" + "\n".join(f"- {m.text}" for m in rs)
        return _txt(out)
    if name == "cosmos_remember":
        from .privacy import redact
        raw = next((args[k] for k in ("text", "fact", "note", "content", "rule", "memory") if isinstance(args.get(k), str) and args[k].strip()), "")
        if not raw:
            return _txt(f"cosmos_remember needs `text` (got: {', '.join(sorted(args)) or 'nothing'}). Example: {{\"text\": \"Universe erase treats an empty s3_key as 'nothing to delete'\", \"category\": \"constraint\", \"kind\": \"fact\", \"files\": [\"path/file.py\"]}}")
        text = redact(" ".join(str(raw).split()))[0]
        if len(text) < 8:
            return _txt(f"cosmos_remember: `text` is {len(text)} characters; write the fact as one full sentence (what is true, where, why).")
        mid = make_id(text)
        rule = str(args.get("kind", "fact")) == "rule"
        if mid not in mems:   # search before write: an existing near-duplicate is confirmed, not duplicated
            from .retrieve import retrieve as _retrieve, tokens as _tokens
            from .dream import jaccard as _jaccard
            near = next((m for m in _retrieve(mems, text, k=5) if _jaccard(_tokens(m.text), _tokens(text)) >= 0.6), None)
            if near is not None and not rule:
                near.evidence_count += 1; near.updated = near.last_verified = today()
                Ledger(cfg.paths).save(near)
                return _txt(f"cosm◎s · already known as {near.id}: {near.text} — evidence count raised; nothing duplicated. To restate it, use kind=rule.")
        imp = args.get("importance")
        imp = min(1.0, max(0.3, float(imp))) if isinstance(imp, (int, float)) else (0.95 if rule else 0.7)
        m = mems.get(mid) or Memory(id=mid, text=text, category=str(args.get("category", "convention")), source="explicit" if rule else "agent",
                                    confidence=0.95 if rule else 0.8, importance=imp, files=list(args.get("files") or [])[:8], authors=[git_author(cfg.paths.root)])
        if args.get("lane"):
            m.lane = re.sub(r"[^a-z0-9/._\-]+", "-", str(args["lane"]).lower()).strip("-")[:40]
        m.status, m.updated, m.last_verified = "active", today(), today()
        mems[mid] = m
        Ledger(cfg.paths).save_all(mems.values()); render_all(cfg, mems)
        return _txt(f"cosm◎s · remembered {mid} ({'rule' if rule else 'fact'}): {text}")
    if name in ("cosmos_flare", "cosmos_finding"):
        from .audit import import_findings
        import tempfile, os
        title = next((str(args[k]).strip() for k in ("title", "text", "summary", "finding") if isinstance(args.get(k), str) and args[k].strip()), "")
        if len(title) < 8:
            return _txt(f"cosmos_flare needs `title` (got: {', '.join(sorted(args)) or 'nothing'}). Example: {{\"title\": \"GET /transitions has no role gate\", \"severity\": \"high\", \"locations\": \"webserver/app/api/v1/endpoints/transitions.py:42\", \"what\": \"…\", \"fix\": \"…\"}}")
        sev = str(args.get("severity", "medium")).lower()
        if sev not in ("critical", "high", "medium", "low", "note"):
            sev = "medium"
        item = {"id": make_id(title)[-6:], "severity": sev, "title": title, "area": "",
                "locations": str(args.get("locations", "")), "sections": [[k.title(), str(args[k])] for k in ("what", "impact", "fix") if args.get(k)]}
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
            json.dump([item], fh); tmp = fh.name
        try:
            new, upd, _ = import_findings(cfg, __import__("pathlib").Path(tmp), "QA", "mcp")
        finally:
            os.unlink(tmp)
        render_all(cfg, Ledger(cfg.paths).load())
        m = (new or upd)[0]
        return _txt(f"cosm◎s · filed {m.meta['audit_id']} [{m.meta['severity']}] {m.text}")
    if name == "cosmos_handoff":
        from .handoff import record_explicit
        p = record_explicit(cfg, str(args.get("learned", "")), str(args.get("open", "")), str(args.get("next", "")), str(args.get("branch", "")))
        return _txt(f"cosm◎s · handoff recorded for this branch ({p.name}); the next session here opens with it.")
    if name == "cosmos_charter":
        from .charter import body, rules
        rs = rules(mems)
        return _txt(body(cfg) + ("\n\n## Explicit team rules\n" + "\n".join(f"- [{m.category}] {m.text}" for m in rs) if rs else ""))
    if name == "cosmos_why":
        q = str(args.get("query", "")).lower()
        hit = mems.get(q) or next((m for m in mems.values() if q in m.text.lower()), None)
        if not hit:
            return _txt("No memory matches.")
        L = [hit.text, f"id {hit.id} · {hit.category} · {hit.status} · {int(hit.confidence*100)}% · seen {hit.evidence_count}×", f"created {hit.created} · updated {hit.updated} · verified {hit.last_verified}"]
        L += [f"evidence: {f}" for f in hit.files] + ([f"seen by: {', '.join(hit.authors)}"] if hit.authors else []) + ([f"note: {hit.reason}"] if hit.reason else [])
        L += [f"contradicts {c}: {mems[c].text}" for c in hit.contradicts if c in mems]
        return _txt("\n".join(L))
    if name in ("cosmos_horizon", "cosmos_intake"):
        from .intake import analyse, render_md, save
        res = analyse(cfg, str(args.get("text", "")), args.get("files") or [], brief=str(args.get("brief", "")))
        save(cfg, res)
        return _txt(render_md(res, git_author(cfg.paths.root)))
    if name == "cosmos_atlas":
        from .atlas import check
        doc = str(args.get("doc", "status"))
        c = check(cfg)
        if doc == "status" or not c["exists"]:
            if not c["exists"]:
                return _txt("No atlas yet. Run `cosmos atlas`.")
            drift = c["drift"] + c["missing"]
            return _txt(f"Atlas generated {c['generated']} at {c['commit']}: {json.dumps(c['counts'])}. " + (f"DRIFT in {len(drift)} source file(s): {', '.join(drift[:8])}. Run `cosmos atlas`." if drift else "In sync with the code."))
        p = cfg.paths.ledger / "atlas" / f"{doc}.md"
        return _txt(p.read_text() if p.exists() else f"{doc}.md not generated yet (run `cosmos atlas`, then /atlas for the deep pass).")
    if name == "cosmos_lanes":
        from .lanes import lane_report
        from .store import Observations
        rows = lane_report(cfg, mems, Observations(cfg.paths).iter_all(), int(args.get("days", 30)))
        return _txt("\n".join(f"{r['lane']}: {r['facts']} facts, {r['findings_open']} open findings, people: " + (", ".join(c['name'] for c in r['contributors']) or "—") + (" ⚠ overlap" if r["overlap"] else "") for r in rows) or "No lanes yet.")
    return {"content": [{"type": "text", "text": f"unknown tool {name}"}], "isError": True}


def serve(cfg: Config) -> None:
    """Blocking stdio loop. One JSON-RPC message per line."""
    import importlib
    from . import code_stamp, fresh_modules
    out = sys.stdout
    stamp, tools = code_stamp(), call_tool
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except Exception:
            continue
        mid = req.get("id")
        method = req.get("method", "")
        params = req.get("params") or {}
        resp: Dict[str, Any]
        try:
            if method == "initialize":
                resp = {"protocolVersion": params.get("protocolVersion", PROTOCOL), "capabilities": {"tools": {"listChanged": False}},
                        "serverInfo": {"name": "cosmos", "title": "cosm◎s", "version": __version__, "icons": [{"src": ICON, "mimeType": "image/svg+xml", "sizes": ["any"]}]},
                        "instructions": "cosmos is this repository's shared engineering memory, charter and architecture. Call cosmos_charter once at the start, cosmos_recall before editing files you did not write, cosmos_remember for durable decisions, cosmos_flare for bugs worth tracking."}
            elif method == "ping":
                resp = {}
            elif method == "tools/list":
                resp = {"tools": [dict(t, icons=[{"src": ICON, "mimeType": "image/svg+xml", "sizes": ["any"]}]) for t in TOOLS]}
            elif method == "tools/call":
                if code_stamp() != stamp:                # cosmos was updated: serve this call from the new code
                    fresh_modules()
                    tools = importlib.import_module("cosmos.mcp").call_tool
                    cfg = importlib.import_module("cosmos.config").load_config(cfg.paths.root)
                    stamp = importlib.import_module("cosmos").code_stamp()
                resp = tools(cfg, str(params.get("name")), params.get("arguments") or {})
            elif method.startswith("notifications/"):
                continue
            else:
                out.write(json.dumps({"jsonrpc": "2.0", "id": mid, "error": {"code": -32601, "message": f"method not found: {method}"}}) + "\n"); out.flush()
                continue
            if mid is None:
                continue
            out.write(json.dumps({"jsonrpc": "2.0", "id": mid, "result": resp}) + "\n")
        except Exception as e:
            out.write(json.dumps({"jsonrpc": "2.0", "id": mid, "error": {"code": -32000, "message": str(e)}}) + "\n")
        out.flush()
