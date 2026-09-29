"""QA / security audit findings as first-class memory.
        if len(str(item.get("title", "")).strip()) < 8:
            continue                                   # a finding without a title is not a finding

A finding is durable engineering knowledge with a lifecycle (open → fixed | withdrawn | wontfix, or regressed).
It lives in the ledger like any other fact (category `finding`), so it shows up in retrieval when someone
touches the affected files, survives across sessions, and is reviewed in the same PR flow.

Import format = the QA audit JSON already produced by Claude sessions:
  [{"id": "11", "severity": "critical", "title": "...", "area": "...", "locations": "`a.py:352` · `b.py:10`",
    "sections": [["What", "..."], ["Impact", "..."], ["Fix", "..."]]}, ...]
"""
from __future__ import annotations

import fnmatch
import hashlib
import json
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from .config import Config, git_author, git_head
from .store import Ledger, Memory, today

SEVERITIES = ["critical", "high", "medium", "low", "note", "info"]
SEV_IMPORTANCE = {"critical": 1.0, "high": 0.85, "medium": 0.65, "low": 0.45, "note": 0.3, "info": 0.3}
SEV_ICON = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🔵", "note": "🔬", "info": "⚪"}
# Lifecycle written by humans (cosmos flares fix/withdraw/...) AND by the session-driven fix loop
# (claimed → pr_open → fixed | needs_human). Import accepts every one of these verbatim - never coerces.
FINDING_STATUSES = ["open", "claimed", "pr_open", "needs_human", "fixed", "withdrawn", "wontfix", "regressed"]
OPEN_LIKE = {"open", "claimed", "pr_open", "needs_human", "regressed"}   # still needs work → shown in reports / retrieval
CLOSED = {"fixed", "wontfix", "withdrawn"}
NOTE = "note"          # severity "note" items (verification notes) carry NO lifecycle: never open, never claimable
PUBLISHABLE = OPEN_LIKE | {NOTE}

_LOC = re.compile(r"`?([\w\-./]+\.(?:py|ts|tsx|js|kt|java|go|rs|rb|sql|sh|yml|yaml|json|toml))(?::\d+(?:,\d+)*)?`?")


# Where the project is in its life, read from git: the branch first (first match wins), then whether anything was
# released. A flare keeps the stage it was found in for life; only new flares take the current one.
STAGE_BRANCHES = [("hotfix/*", "HOTFIX"), ("hotfix-*", "HOTFIX"), ("release/*", "RC"), ("release-*", "RC"), ("rc/*", "RC"),
                  ("qa/*", "QA"), ("qa-*", "QA"), ("test/*", "QA"), ("testing", "QA"), ("uat/*", "UAT"), ("uat", "UAT"),
                  ("staging", "UAT"), ("stage", "UAT")]
DEFAULT_BRANCHES = {"main", "master", "trunk"}
_RELEASE_TAG = re.compile(r"^v?\d+(\.\d+)+$")                  # v1.2.0 or 1.2 - an -rc / -beta tag is not a release
_RC_TAG = re.compile(r"^v?\d+(\.\d+)+[-.]?(rc|beta|alpha)", re.I)


def _git_lines(root: Path, *args: str) -> List[str]:
    try:
        out = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, timeout=3)
        return [l.strip() for l in out.stdout.splitlines() if l.strip()] if out.returncode == 0 else []
    except (OSError, subprocess.SubprocessError):
        return []


def lifecycle_stage(cfg: Config) -> Tuple[str, str]:
    """(stage, why) for a flare filed now: flares.stage in config.json if set, else the branch (flares.stages extends the
    branch map), else PROD on the default branch once a version tag is reachable, else DEV."""
    pinned = str(cfg.get("flares.stage") or "").strip()
    if pinned:
        return pinned.upper(), "set in .cosmos/config.json (flares.stage)"
    root = cfg.paths.root
    branch = next(iter(_git_lines(root, "symbolic-ref", "--short", "HEAD")), "")
    extra = cfg.get("flares.stages") or {}
    rules = [(str(g), str(s).upper()) for g, s in (extra.items() if isinstance(extra, dict) else [])] + STAGE_BRANCHES
    for glob, stage in rules:
        if branch and fnmatch.fnmatch(branch.lower(), glob.lower()):
            return stage, f"branch {branch}"
    if any(_RC_TAG.match(t) for t in _git_lines(root, "tag", "--points-at", "HEAD")):
        return "RC", "HEAD carries a release-candidate tag"
    if branch and branch not in DEFAULT_BRANCHES:
        return "DEV", f"branch {branch}"
    tag = next((t for t in _git_lines(root, "tag", "--merged", "HEAD", "--sort=-creatordate") if _RELEASE_TAG.match(t)), "")
    if tag:
        return "PROD", f"released ({tag} is in {branch or 'HEAD'})"
    return "DEV", "nothing released yet (no version tag)"


def flare_prefix(cfg: Config) -> str:
    """The id prefix for a flare filed now. flares.prefix in config.json pins one prefix for every flare (explicit
    outranks inferred); otherwise it is the lifecycle stage, after the project tag flares.project if there is one."""
    pinned = str(cfg.get("flares.prefix") or "").strip()
    if pinned:
        return pinned
    stage, _ = lifecycle_stage(cfg)
    project = str(cfg.get("flares.project") or "").strip()
    return f"{project}-{stage}" if project else stage


def prefix_note(cfg: Config) -> str:
    """One line saying which prefix a new flare gets here, and why."""
    pinned = str(cfg.get("flares.prefix") or "").strip()
    if pinned:
        return f"new flares get {pinned}- (pinned by flares.prefix in .cosmos/config.json; remove it to follow the lifecycle)"
    stage, why = lifecycle_stage(cfg)
    return f"new flares get {flare_prefix(cfg)}- (stage {stage}: {why})"


def finding_id(prefix: str, raw_id: str) -> str:
    return "mem_" + hashlib.sha1(f"finding:{prefix}:{raw_id}".encode()).hexdigest()[:8]


def parse_locations(text: str) -> List[str]:
    return list(dict.fromkeys(m.group(1) for m in _LOC.finditer(text or "")))


def _from_json_item(item: Dict, prefix: str, source_doc: str, author: str, commit: str) -> Memory:
    raw_id = str(item.get("id", "")).strip() or hashlib.sha1(item.get("title", "").encode()).hexdigest()[:6]
    sev = str(item.get("severity", "medium")).lower()
    sev = sev if sev in SEV_IMPORTANCE else "medium"
    status = str(item.get("status", "open")).lower().replace("-", "_") or "open"
    if sev == NOTE:
        status = NOTE
    files = [f for f in parse_locations(item.get("locations", "")) if not f.startswith("/")]
    m = Memory(
        id=finding_id(prefix, raw_id), text=str(item.get("title", "")).strip(), category="finding",
        confidence=0.9, importance=SEV_IMPORTANCE[sev], source="explicit", files=files[:8],
        authors=[author] if author else [], tags=["finding", sev] + ([re.sub(r"[^a-z0-9]+", "-", str(item["area"]).lower()).strip("-")] if item.get("area") else []),
        details=[[str(a), str(b)] for a, b in (item.get("sections") or []) if a and b],
        meta={"audit_id": f"{prefix}-{raw_id}", "raw_id": raw_id, "severity": sev, "finding_status": status,
              "area": str(item.get("area", "")), "locations": str(item.get("locations", "")), "source_doc": source_doc,
              "found_commit": commit, "status_note": str(item.get("status_note", "")), "status_at": str(item.get("status_at", ""))},
    )
    return m


def import_findings(cfg: Config, path: Path, prefix: str = "QA", source_doc: str = "") -> Tuple[List[Memory], List[Memory], List[Memory]]:
    """Returns (new, updated, regressed). Idempotent: same audit id → same memory."""
    from .lanes import _tree_index, resolve_path
    index = _tree_index(cfg.paths.root)
    data = json.loads(Path(path).read_text())
    items = data if isinstance(data, list) else next((v for v in data.values() if isinstance(v, list)), [])
    ledger = Ledger(cfg.paths)
    mems = ledger.load()
    author, commit, t = git_author(cfg.paths.root), git_head(cfg.paths.root), today()
    new, updated, regressed = [], [], []
    # a finding already filed under an earlier stage's prefix is the same finding: it keeps its id and is updated
    by_origin = {(m.meta.get("source_doc"), m.meta.get("raw_id")): m for m in mems.values() if m.category == "finding" and m.meta.get("raw_id")}
    for item in items:
        inc = _from_json_item(item, prefix, source_doc or Path(path).name, author, commit)
        inc.files = [resolve_path(f, index) for f in inc.files]
        cur = mems.get(inc.id) or by_origin.get((inc.meta["source_doc"], inc.meta["raw_id"]))
        if cur is None:
            inc.reason = f"Imported from {inc.meta['source_doc']} on {t}"
            mems[inc.id] = inc
            new.append(inc)
            continue
        was, now = cur.meta.get("finding_status", "open"), inc.meta["finding_status"]
        if now == NOTE or was == NOTE:
            cur.meta["finding_status"] = NOTE
        elif was in ("fixed", "wontfix") and now == "open":
            cur.meta["finding_status"] = "regressed"
            cur.status = "active"
            cur.reason = f"REGRESSION detected on {t}: finding was {was} and has been reported again ({inc.meta['source_doc']})"
            regressed.append(cur)
        elif now != "open":
            # the exporter (human or fix loop) moved it: take the new state verbatim
            if now != was:
                cur.meta[f"{now}_on"] = t
                cur.reason = f"Status {was} → {now} via import of {inc.meta['source_doc']} on {t}"
            cur.meta["finding_status"] = now
            cur.status = "forgotten" if now == "withdrawn" else "active"
        # else: incoming "open" never downgrades a local claimed/pr_open/needs_human/withdrawn
        cur.text, cur.details, cur.files = inc.text or cur.text, inc.details or cur.details, inc.files or cur.files
        cur.meta.update({k: v for k, v in inc.meta.items() if k not in ("finding_status", "audit_id", "raw_id") and v})
        cur.evidence_count += 1
        cur.updated = cur.last_verified = t
        if cur not in regressed:
            updated.append(cur)
    ledger.save_all(mems.values())
    return new, updated, regressed


def findings(mems: Dict[str, Memory], status: Optional[str] = None, severity: Optional[str] = None) -> List[Memory]:
    out = [m for m in mems.values() if m.category == "finding"]   # withdrawn (status forgotten) stays listed - it is a state
    if status:
        out = [m for m in out if m.meta.get("finding_status", "open") == status]
    if severity:
        out = [m for m in out if m.meta.get("severity") == severity]
    out.sort(key=lambda m: (SEVERITIES.index(m.meta.get("severity", "medium")) if m.meta.get("severity", "medium") in SEVERITIES else 9,
                            m.meta.get("finding_status", "open") != "open", m.meta.get("audit_id", "")))
    return out


def set_status(cfg: Config, mem: Memory, new_status: str, note: str = "", commit: str = "", branch: str = "") -> None:
    """commit / branch name where the work is when it is not this checkout (a fix made in another worktree)."""
    if mem.meta.get("finding_status") == NOTE or mem.meta.get("severity") == NOTE:
        raise SystemExit(f"{mem.meta.get('audit_id')} is a verification note — notes carry no lifecycle and cannot be {new_status}.")
    t = today()
    mem.meta["finding_status"] = new_status
    mem.meta[f"{new_status}_on"] = t
    mem.meta["status_at"] = t
    if note:
        mem.meta["status_note"] = note
    commit = commit or (git_head(cfg.paths.root) if new_status == "fixed" else "")
    if commit:
        mem.meta[f"{new_status}_commit"] = commit
    if branch:
        mem.meta[f"{new_status}_branch"] = branch
    mem.status = "forgotten" if new_status == "withdrawn" else "active"
    mem.updated = mem.last_verified = t
    mem.reason = f"Marked {new_status} on {t}" + (f": {note}" if note else "")
    Ledger(cfg.paths).save(mem)


def edit_finding(cfg: Config, mem: Memory, title: Optional[str] = None, severity: Optional[str] = None,
                 locations: Optional[str] = None, area: Optional[str] = None) -> List[str]:
    """Correct what was filed; the audit id and the lifecycle stay. Returns the fields that changed."""
    changed: List[str] = []
    if title and title.strip() != mem.text:
        mem.text = title.strip(); changed.append("title")
    if severity and severity != mem.meta.get("severity"):
        mem.meta["severity"] = severity
        mem.importance = SEV_IMPORTANCE.get(severity, mem.importance)
        mem.tags = [t for t in mem.tags if t not in SEV_IMPORTANCE] + [severity]
        changed.append("severity")
    if locations is not None and locations != mem.meta.get("locations"):
        from .lanes import _tree_index, resolve_path
        index = _tree_index(cfg.paths.root)
        mem.meta["locations"] = locations
        mem.files = [resolve_path(f, index) for f in parse_locations(locations) if not f.startswith("/")][:8] or mem.files
        changed.append("locations")
    if area is not None and area != mem.meta.get("area"):
        mem.meta["area"] = area; changed.append("area")
    if changed:
        mem.updated = today()
        mem.reason = f"Edited on {today()}: {', '.join(changed)}"
        Ledger(cfg.paths).save(mem)
    return changed


def export_json(mems: Iterable[Memory]) -> List[Dict]:
    out = []
    for m in mems:
        out.append({"id": m.meta.get("raw_id") or m.meta.get("audit_id", m.id).split("-")[-1], "audit_id": m.meta.get("audit_id", m.id), "severity": m.meta.get("severity", "medium"),
                    "status": m.meta.get("finding_status", "open"), "status_note": m.meta.get("status_note", ""), "status_at": m.meta.get("status_at", ""), "title": m.text, "area": m.meta.get("area", ""),
                    "locations": m.meta.get("locations", " · ".join(f"`{f}`" for f in m.files)), "sections": m.details,
                    "memory_id": m.id, "found_commit": m.meta.get("found_commit", ""), "fixed_commit": m.meta.get("fixed_commit", "")})
    return out


# ---------------------------------------------------------------- reports
def report_markdown(cfg: Config, fs: List[Memory], title: str = "QA / Security Audit") -> str:
    open_ = [m for m in fs if m.meta.get("finding_status", "open") in OPEN_LIKE]
    notes = [m for m in fs if m.meta.get("finding_status") == NOTE]
    closed = [m for m in fs if m.meta.get("finding_status") in CLOSED]
    c = Counter(m.meta.get("severity", "medium") for m in open_)
    lines = [f"# {cfg.paths.root.name} — {title}", "", f"_Generated by cosmos on {today()} · branch state `{git_head(cfg.paths.root)}`_", "",
             "## Summary", "", f"**{len(open_)} open findings** — " + " · ".join(f"{SEV_ICON[s]} {c[s]} {s}" for s in SEVERITIES if c[s] and s != NOTE),
             f"{len(closed)} closed (" + " · ".join(f"{k} {v}" for k, v in sorted(Counter(m.meta.get('finding_status') for m in closed).items())) + f") · {len(notes)} verification notes", ""]
    by_area: Dict[str, List[Memory]] = defaultdict(list)
    for m in open_:
        by_area[m.meta.get("area") or "general"].append(m)
    lines.append("**By area**")
    for area, ms in sorted(by_area.items()):
        lines.append(f"- {area} — " + ", ".join(f"#{m.meta.get('audit_id','').split('-')[-1]}" for m in ms))
    lines += ["", "## Index", ""]
    for m in fs:
        st = m.meta.get("finding_status", "open")
        lines.append(f"- {SEV_ICON[m.meta.get('severity','medium')]} **{m.meta.get('audit_id')}** [{m.meta.get('severity','').upper()}] {m.text}" + ("" if st == "open" else f" — _{st}_"))
    lines.append("")
    for m in fs:
        st = m.meta.get("finding_status", "open")
        lines += [f"## {m.meta.get('audit_id')} · [{m.meta.get('severity','').upper()}] {m.text}", ""]
        if st != "open":
            lines += [f"> Status: **{st}**" + (f" on {m.meta.get(st + '_on')}" if m.meta.get(st + "_on") else "") + (f" · commit `{m.meta['fixed_commit']}`" if m.meta.get("fixed_commit") else ""), ""]
        if m.meta.get("locations"):
            lines += [f"**Where:** {m.meta['locations']}", ""]
        for label, text in m.details:
            lines += [f"### {label}", "", text, ""]
        lines += [f"_memory `{m.id}` · found at `{m.meta.get('found_commit','?')}` · last verified {m.last_verified}_", ""]
    return "\n".join(lines)


def report_slack(cfg: Config, fs: List[Memory], title: str = "QA / Security Audit") -> Dict:
    """Slack payload: one parent message + one threaded reply per open finding. mrkdwn, no Block Kit needed."""
    open_ = [m for m in fs if m.meta.get("finding_status", "open") in OPEN_LIKE]
    c = Counter(m.meta.get("severity", "medium") for m in open_)
    parent = (f"🐛 *{cfg.paths.root.name} — {title}* · `{git_head(cfg.paths.root)}`\n\n"
              f"*{len(open_)} open findings* — " + " · ".join(f"{SEV_ICON[s]} {c[s]} {s}" for s in SEVERITIES if c[s]) + "\n\n"
              + "\n".join(f"{SEV_ICON[m.meta.get('severity','medium')]} *{m.meta.get('audit_id')}* — {m.text}" for m in open_[:8])
              + ("\n…" if len(open_) > 8 else "") + f"\n\n_Full detail per finding in thread · tracked in `.cosmos/ledger/finding/` · `cosmos flares list`_")
    replies = []
    for m in open_:
        body = f"{SEV_ICON[m.meta.get('severity','medium')]} *{m.meta.get('audit_id')} · {m.meta.get('severity','').upper()}* — *{m.text}*\n"
        if m.meta.get("locations"):
            body += f"📍 {m.meta['locations']}\n"
        for label, text in m.details[:4]:
            body += f"\n*{label}*\n{text[:900]}{'…' if len(text) > 900 else ''}\n"
        if m.meta.get("finding_status") == "regressed":
            body += f"\n⚠️ *REGRESSION* — was fixed, reported again. {m.reason}\n"
        body += f"\n_ack with 👀 / ✅ / 🚫 · `cosmos flares fix {m.meta.get('audit_id')}`_"
        replies.append({"audit_id": m.meta.get("audit_id"), "text": body})
    return {"parent": parent, "replies": replies}
