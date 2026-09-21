"""Intake: a feature request enters with a map, not a Slack message.

Before code is written, `cosmos intake "…"` names the lanes it touches, the existing decisions and constraints it
collides with, the open findings sitting on those files, and who has been working there - deterministically,
from the ledger and the observations already in the repo.
"""
from __future__ import annotations

import re
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from .config import Config, git_author
from .lanes import infer_lane, lane_report
from .retrieve import retrieve
from .store import Ledger, Memory, Observations, slugify, today


def expand_hints(cfg: Config, hints: Optional[Iterable[str]], limit: int = 60) -> List[str]:
    """A hint may be a file or a folder (relative to the repo or absolute). Folders contribute every code/doc file inside."""
    from .transcript import relativize
    out: List[str] = []
    root = cfg.paths.root
    for h in hints or []:
        h = str(h).strip()
        if not h:
            continue
        p = (root / h) if not h.startswith("/") else Path(h)
        rel = relativize(str(p), root) if p.exists() else h.rstrip("/")
        if p.is_dir():
            out.append(rel + "/")
            for f in sorted(p.rglob("*")):
                if f.is_file() and not any(part.startswith(".") or part in ("node_modules", "__pycache__", "dist", "build") for part in f.relative_to(p).parts) \
                        and f.suffix in (".py", ".ts", ".tsx", ".js", ".kt", ".java", ".go", ".rs", ".rb", ".sql", ".md", ".yml", ".yaml", ".json"):
                    out.append(relativize(str(f), root))
                    if len(out) >= limit:
                        return out
        else:
            out.append(rel)
    return out


def analyse(cfg: Config, text: str, files: Optional[Iterable[str]] = None, k: int = 14, brief: str = "", attachments: Optional[List[Dict]] = None) -> Dict:
    """`brief` is pasted text (a PRD, a Slack thread); `attachments` are [{"name", "text"}] read from ad-hoc files.
    Both widen the retrieval query and are handed to the model - never stored in the ledger as facts."""
    mems = Ledger(cfg.paths).load()
    obs = list(Observations(cfg.paths).iter_all())
    files = expand_hints(cfg, files)
    attachments = [a for a in (attachments or []) if a.get("name")]
    context = " ".join([brief or ""] + [str(a.get("text", ""))[:4000] for a in attachments])
    hits = retrieve(mems, (text + " " + context[:2000]).strip(), paths=list(files or []), k=k)
    lanes = Counter()
    for m in hits:
        if m.lane:
            lanes[m.lane] += 1
    for f in files or []:
        lanes[infer_lane([f], cfg.get("lanes", {}) or {})] += 2
    touched = [l for l, _ in lanes.most_common(5)]
    report = {r["lane"]: r for r in lane_report(cfg, mems, obs)}
    from .audit import OPEN_LIKE
    collisions = [m for m in hits if m.category in ("decision", "constraint", "convention", "architecture") and m.status == "active"]
    findings = [m for m in mems.values() if m.category == "finding" and m.meta.get("finding_status", "open") in OPEN_LIKE and (m.lane in touched or m in hits)]
    people: Counter = Counter()
    for l in touched:
        for c in report.get(l, {}).get("contributors", []):
            people[c["name"]] += c["observations"]
    res = {"text": text, "files": list(files or []), "lanes": touched, "lane_details": [report[l] for l in touched if l in report],
           "collisions": collisions, "findings": findings, "related": [m for m in hits if m not in collisions],
           "people": [{"name": n, "observations": c} for n, c in people.most_common(5)],
           "suggested_owner": people.most_common(1)[0][0] if people else "", "overlap": [l for l in touched if report.get(l, {}).get("overlap")],
           "brief": (brief or "")[:6000], "attachments": [{"name": a["name"], "chars": len(str(a.get("text", ""))), "text": str(a.get("text", ""))[:6000]} for a in attachments],
           "assessment": ""}
    res["assessment"] = _llm_assessment(cfg, res)
    return res


def _llm_assessment(cfg: Config, res: Dict) -> str:
    """With a model available: a short impact assessment grounded ONLY in the retrieved facts and findings."""
    from .providers import get_provider
    prov = get_provider(cfg.get("llm", {}) or {})
    if prov is None:
        return ""
    import json
    payload = {"feature": res["text"], "brief": res.get("brief", "")[:4000], "attached_documents": [{"name": a["name"], "excerpt": a["text"][:3000]} for a in res.get("attachments", [])][:5],
               "paths": res["files"][:40], "lanes": res["lanes"],
               "decisions_and_constraints": [m.text for m in res["collisions"][:12]],
               "open_findings": [f"{m.meta.get('audit_id')}: {m.text}" for m in res["findings"][:12]],
               "related_facts": [m.text for m in res["related"][:10]],
               "people": res["people"]}
    schema = {"type": "object", "properties": {"assessment": {"type": "string"}, "risks": {"type": "array", "items": {"type": "string"}}, "questions": {"type": "array", "items": {"type": "string"}}},
              "required": ["assessment", "risks", "questions"], "additionalProperties": False}
    try:
        out = prov.complete("You assess the impact of a proposed feature for an engineering team. The brief and attached documents describe what is wanted; the facts, decisions, findings and paths describe the codebase. Use ONLY what is given; "
                            "never invent code details. Write 3-5 plain sentences a product manager and a developer both understand: what this touches, "
                            "what it collides with, what must be decided first. Then list concrete risks and the questions to answer before coding.",
                            json.dumps(payload, ensure_ascii=False), schema)
    except Exception:
        return ""
    if not out:
        return ""
    parts = [str(out.get("assessment", "")).strip()]
    if out.get("risks"):
        parts.append("Risks: " + "; ".join(str(r) for r in out["risks"][:6]))
    if out.get("questions"):
        parts.append("Decide first: " + "; ".join(str(q) for q in out["questions"][:6]))
    return "\n\n".join(p for p in parts if p)


def render_md(a: Dict, author: str) -> str:
    L = [f"---", f"kind: intake", f"created: {today()}", f"by: \"{author}\"", f"lanes: {a['lanes']}", "---", "", f"# Intake: {a['text']}", ""]
    if a.get("brief"):
        L += ["## Brief", "", a["brief"], ""]
    if a.get("attachments"):
        L += ["## Attached documents", ""] + [f"- `{x['name']}` ({x['chars']} chars) — saved under `attachments/`" for x in a["attachments"]] + [""]
    if a.get("assessment"):
        L += ["## Assessment", "", a["assessment"], ""]
    L += ["## Lanes touched", ""] + ([f"- **{l}**" + (" — ⚠ two or more people active here this month" if l in a["overlap"] else "") for l in a["lanes"]] or ["- (none inferred — add `-f path` hints)"])
    L += ["", "## Collides with (decide before coding)", ""] + ([f"- [{m.category}] {m.text} `{m.id}`" for m in a["collisions"]] or ["- nothing recorded"])
    L += ["", "## Open findings in the way", ""] + ([f"- {m.meta.get('audit_id')} [{m.meta.get('severity')}] {m.text}" for m in a["findings"]] or ["- none"])
    L += ["", "## Who has been here (last 30 days)", ""] + ([f"- {p['name']} — {p['observations']} observations" for p in a["people"]] or ["- nobody recorded"])
    if a["suggested_owner"]:
        L += ["", f"Suggested owner: **{a['suggested_owner']}**"]
    L += ["", "## Related facts", ""] + ([f"- [{m.category}] {m.text}" for m in a["related"][:8]] or ["- none"])
    return "\n".join(L) + "\n"


def save(cfg: Config, a: Dict) -> Path:
    d = cfg.paths.ledger / "intake"
    d.mkdir(parents=True, exist_ok=True)
    slug = f"{today()}-{slugify(a['text'], 40)}"
    p = d / f"{slug}.md"
    if a.get("attachments"):
        ad = d / "attachments" / slug
        ad.mkdir(parents=True, exist_ok=True)
        for x in a["attachments"]:
            (ad / re.sub(r"[^A-Za-z0-9._-]", "_", x["name"])[:80]).write_text(x.get("text", ""))
    p.write_text(render_md(a, git_author(cfg.paths.root)))
    return p


def read_attachment(path: Path, limit: int = 200_000) -> Dict:
    """Read an ad-hoc file as text (utf-8, errors ignored). Binary files contribute their name only."""
    try:
        raw = path.read_bytes()[:limit]
        text = raw.decode("utf-8", errors="ignore") if b"\x00" not in raw[:4000] else ""
    except Exception:
        text = ""
    return {"name": path.name, "text": text}


def list_intakes(cfg: Config) -> List[Dict]:
    d = cfg.paths.ledger / "intake"
    out = []
    if not d.exists():
        return out
    for p in sorted(d.glob("*.md"), reverse=True):
        txt = p.read_text()
        title = re.search(r"^# Intake: (.+)$", txt, re.M)
        lanes = re.search(r"^lanes: (\[.*\])$", txt, re.M)
        out.append({"file": p.name, "title": title.group(1) if title else p.stem, "lanes": lanes.group(1) if lanes else "[]", "created": p.name[:10], "body": txt})
    return out
