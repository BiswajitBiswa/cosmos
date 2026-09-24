"""Lanes: every fact, finding and diagram is filed under the feature / module it belongs to.

A lane is inferred from the files a fact anchors to (configurable globs first, then path heuristics), so the
ledger, CLAUDE.md and the UI group knowledge the way the team thinks about the product - and so two people
working the same lane in the same month become visible instead of colliding in a merge.
"""
from __future__ import annotations

import fnmatch
import re
from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Dict, Iterable, List, Optional

from .config import Config
import json
from .store import Memory

GENERIC = {"src", "app", "apps", "lib", "libs", "main", "java", "kotlin", "python", "pkg", "internal", "cmd", "test", "tests", "spec",
           "__tests__", "packages", "modules", "core", "common", "shared", "utils", "util", "helpers", "components", "v1", "v2", "api", "endpoints", "routes"}
GENERAL = "general"
TOOLING_DIRS = {".claude", ".cosmos", ".github", ".vscode", ".cursor", ".gemini", "scripts", "ci", ".circleci", "infra", "terraform", "k8s", "helm", "deploy"}


def looks_like_path(f: str) -> bool:
    """A file reference, not a sentence that slipped into the evidence list (commit prose, CLI flags, markdown bullets)."""
    f = (f or "").strip()
    return bool(f) and len(f) <= 300 and not f.startswith("-") and not re.search(r"\s|[<>|*?\"]", f)


def clean_lane(name: str) -> str:
    """A lane name as the model or a person gave it → a short slug ("" when nothing usable is left)."""
    return re.sub(r"[^a-z0-9/._\-]+", "-", str(name or "").lower()).strip("-")[:40]
DOC_DIRS = {"docs", "doc", "references", "reference", "adr", "rfcs", "wiki"}


def configured_lane(files: Iterable[str], lane_globs: Optional[Dict[str, List[str]]]) -> str:
    """The lane the team configured for these files ("" when no configured glob matches)."""
    files = [f.replace("\\", "/") for f in files if looks_like_path(f)]
    for name, globs in (lane_globs or {}).items():
        for f in files:
            if any(fnmatch.fnmatch(f, g) or fnmatch.fnmatch(f, g.rstrip("/**") + "/*") or f.startswith(g.rstrip("*/") + "/") for g in globs):
                return name
    return ""


def infer_lane(files: Iterable[str], lane_globs: Optional[Dict[str, List[str]]] = None) -> str:
    """Config globs win; otherwise first meaningful path segment, plus the last directory when it adds information."""
    files = [f.replace("\\", "/") for f in files if looks_like_path(f)]
    for name, globs in (lane_globs or {}).items():
        for f in files:
            if any(fnmatch.fnmatch(f, g) or fnmatch.fnmatch(f, g.rstrip("/**") + "/*") or f.startswith(g.rstrip("*/") + "/") for g in globs):
                return name
    votes: Dict[str, int] = defaultdict(int)
    for f in files:
        if f.startswith(("/", "external/")):
            continue                                   # outside the repo tree: no lane from it
        parts = [p for p in f.split("/") if p and p != ".."]
        if f.startswith("../") and parts:              # sibling repo: the lane is that repo
            votes["../" + parts[0]] += 1
            continue
        dirs = parts[:-1]
        if not dirs:
            continue                                   # a root-level file says nothing about a lane
        first = dirs[0].lower()
        if first in TOOLING_DIRS or first.startswith("."):
            votes["tooling"] += 1
            continue
        if first in DOC_DIRS:
            votes["docs"] += 1
            continue
        meaningful = [d for d in dirs if d.lower() not in GENERIC and not d.startswith(".")]
        # coarse on purpose: the lane is the top-level app / package. Finer lanes are a config decision.
        votes[(meaningful[0] if meaningful else dirs[0]).lower()] += 1
    if not votes:
        return GENERAL
    return max(votes.items(), key=lambda kv: (kv[1], -len(kv[0])))[0]


_SKIP = {".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build", ".cosmos", ".next", "target"}


def _tree_index(root) -> Dict[str, List[str]]:
    """basename → repo-relative paths, for resolving partial locations like `crud/base.py`."""
    import os
    idx: Dict[str, List[str]] = defaultdict(list)
    for dp, dns, fns in os.walk(root):
        dns[:] = [d for d in dns if d not in _SKIP and not d.startswith(".")]
        rel = os.path.relpath(dp, root)
        for fn in fns:
            idx[fn].append(fn if rel == "." else f"{rel}/{fn}".replace("\\", "/"))
    return idx


_INDEX_CACHE: Dict[str, Dict[str, List[str]]] = {}


def resolve_evidence(root, fragment: str) -> str:
    """Best effort from a cited path to evidence that exists: repo-relative as given, a unique tree match for a
    partial path, a sibling repository (`../name/...`, also when cited as `name/...`), or "" when nothing matches."""
    from pathlib import Path
    frag = str(fragment).strip().lstrip("./")
    if not frag:
        return ""
    if (Path(root) / frag).exists():
        return frag
    if frag.startswith("../") and (Path(root) / frag).resolve().exists():
        return frag
    key = str(root)
    if key not in _INDEX_CACHE:
        _INDEX_CACHE[key] = _tree_index(root)
    r = resolve_path(frag, _INDEX_CACHE[key])
    if r != frag and (Path(root) / r).exists():
        return r
    parent = Path(root).resolve().parent
    if (parent / frag).exists() and frag.split("/")[0] != Path(root).resolve().name:
        return "../" + frag                       # cited as `frontend/src/x.ts` from the backend repo
    from .transcript import worktrees
    wts = worktrees(Path(root))
    for wt in wts:
        if (wt / frag).exists():
            return frag                           # exists on another worktree of this repo
    # a sibling repository the session also touched, cited relative to *its* root (or as a bare file name)
    for sib in _sibling_repos(Path(root)):
        if sib in wts:
            continue
        if (sib / frag).exists():
            return f"../{sib.name}/{frag}"
        skey = str(sib)
        if skey not in _INDEX_CACHE:
            _INDEX_CACHE[skey] = _tree_index(sib)
        r = resolve_path(frag, _INDEX_CACHE[skey])
        if r != frag and (sib / r).exists():
            return f"../{sib.name}/{r}"
    return ""


def _sibling_repos(root):
    """Other git repositories next to this one (the frontend beside the backend, typically), most recently touched first."""
    from pathlib import Path
    try:
        parent = Path(root).resolve().parent
        sibs = [d for d in parent.iterdir() if d.is_dir() and d != Path(root).resolve() and (d / ".git").exists()]
        return sorted(sibs, key=lambda d: -d.stat().st_mtime)[:12]
    except Exception:
        return []


def resolve_path(fragment: str, index: Dict[str, List[str]]) -> str:
    """`crud/base.py` → `packages/core/crud/base.py` when exactly one tree path ends with it; else unchanged."""
    frag = fragment.strip().lstrip("./")
    if not frag or frag.startswith(("/", "../", "external/")):
        return fragment
    cands = [p for p in index.get(frag.rsplit("/", 1)[-1], []) if p == frag or p.endswith("/" + frag)]
    if len(cands) == 1:
        return cands[0]
    if cands:   # several: prefer the shortest (least nested) unambiguous one only if all share the same top-level dir
        tops = {c.split("/")[0] for c in cands}
        if len(tops) == 1:
            return min(cands, key=len)
    return fragment


def assign_lanes(mems: Dict[str, Memory], cfg: Config, only_missing: bool = True) -> int:
    from .transcript import relativize
    globs = cfg.get("lanes", {}) or {}
    n = 0
    index = None
    for m in mems.values():
        # normalise evidence paths: absolute → relative; partial fragments → resolved against the tree
        fixed = [relativize(f, cfg.paths.root) if f.startswith("/") else f for f in m.files if looks_like_path(f)]
        if any(not (cfg.paths.root / f).exists() and not f.startswith(("../", "external/")) for f in fixed):
            index = index if index is not None else _tree_index(cfg.paths.root)
            fixed = [f if (cfg.paths.root / f).exists() or f.startswith(("../", "external/")) else resolve_path(f, index) for f in fixed]
        recompute = not only_missing or not m.lane
        if fixed != m.files:
            m.files, recompute = fixed, True
            n += 1
        team = configured_lane(m.files, globs)
        if team:                                       # a lane the team configured outranks one the model named
            if team != m.lane:
                m.lane = team
                n += 1
            continue
        if m.meta.get("lane_by") == "model" and m.lane:
            cleaned = clean_lane(m.lane)
            if cleaned and cleaned != m.lane:
                m.lane = cleaned
                n += 1
            if cleaned:
                continue                               # the model named this lane; paths never overrule it
        if m.lane and clean_lane(m.lane) != m.lane:
            recompute = True                           # a lane that is not a slug came from bad evidence: infer it again
        if not recompute:
            continue
        lane = infer_lane(m.files, globs)
        if lane == GENERAL and m.category == "finding" and m.meta.get("area"):
            lane = re.sub(r"[^a-z0-9]+", "-", m.meta["area"].lower()).strip("-") or GENERAL
        if lane != m.lane:
            m.lane = lane
            n += 1
    return n


def propose(cfg: Config, mems: Dict[str, Memory], observations: Iterable[Dict], use_llm: bool = True) -> Dict:
    """Suggest a `lanes` mapping for config.json. Deterministic: top-level dirs with counts. With an LLM provider
    configured, the model groups the paths into 5-12 product-shaped lanes with globs; the result is validated
    (every glob must match at least one seen path) before it is returned."""
    from collections import Counter
    paths: Counter = Counter()
    for m in mems.values():
        for f in m.files:
            paths[f] += 1
    for o in observations:
        for f in norm_files(o.get("files", []), cfg):
            paths[f] += 1
    seen = [p for p, _ in paths.most_common(400) if not p.startswith(("/", "external/"))]
    top: Counter = Counter()
    for p in seen:
        top[infer_lane([p])] += paths[p]
    det = {lane: [f"{lane}/**"] for lane in top if lane not in (GENERAL, "tooling", "docs") and not lane.startswith("../")}
    out = {"source": "paths", "lanes": det, "counts": dict(top.most_common())}
    if not use_llm:
        return out
    from .providers import get_provider
    prov = get_provider(cfg.get("llm", {}) or {})
    if prov is None:
        out["note"] = "no LLM provider configured — showing the path-derived proposal; set llm.provider in .cosmos/config.json for a product-shaped one"
        return out
    import json
    try:
        import anthropic  # noqa
    except Exception:
        pass
    try:
        schema = {"type": "object", "properties": {"lanes": {"type": "object", "additionalProperties": {"type": "array", "items": {"type": "string"}}}}, "required": ["lanes"], "additionalProperties": False}
        res = prov.complete("You organise a codebase into feature lanes a product manager would recognise (payments, billing, auth, universe-import…). "
                            "Group the given file paths into 5-12 lanes. Each lane: kebab-case name → 1-4 path globs. Every glob must match at least one given path. Prefer product features over technical layers.",
                            json.dumps({"paths": seen}), schema)
        lanes = (res or {}).get("lanes") if isinstance(res, dict) else None
        if isinstance(lanes, dict) and lanes:
            import fnmatch
            valid = {k: [g for g in v if isinstance(g, str) and any(fnmatch.fnmatch(pth, g) or pth.startswith(g.rstrip("*/") + "/") for pth in seen)] for k, v in lanes.items() if isinstance(v, list)}
            valid = {k: v for k, v in valid.items() if v}
            if valid:
                out.update({"source": "llm", "lanes": valid})
    except Exception as e:
        out["note"] = f"LLM proposal failed ({e}); showing the path-derived one"
    return out


def norm_files(files: Iterable[str], cfg: Config) -> List[str]:
    """Observation paths as they should have been stored: repo-relative, sibling repos as ../<repo>, nothing absolute."""
    from .transcript import relativize
    out = []
    for f in files or []:
        f = relativize(f, cfg.paths.root) if str(f).startswith("/") else str(f)
        if not f.startswith(("external/",)):
            out.append(f)
    return out


def lane_report(cfg: Config, mems: Dict[str, Memory], observations: Iterable[Dict], days: int = 30) -> List[Dict]:
    """Per lane: facts, open findings, contributors in the window, and whether people overlap."""
    globs = cfg.get("lanes", {}) or {}
    since = datetime.utcnow() - timedelta(days=days)
    lanes: Dict[str, Dict] = defaultdict(lambda: {"facts": 0, "findings_open": 0, "findings": 0, "contributors": defaultdict(int), "files": set(), "last": ""})
    from .audit import OPEN_LIKE
    for m in mems.values():
        if m.status in ("superseded", "forgotten"):
            continue
        L = lanes[m.lane or GENERAL]
        if m.category == "finding":
            L["findings"] += 1
            if m.meta.get("finding_status", "open") in OPEN_LIKE:
                L["findings_open"] += 1
        else:
            L["facts"] += 1
        L["files"].update(f for f in m.files[:3] if not f.startswith(("external/", "/")))
        L["last"] = max(L["last"], m.updated)
    for o in observations:
        try:
            ts = datetime.strptime(str(o.get("ts", ""))[:19], "%Y-%m-%dT%H:%M:%S")
        except Exception:
            continue
        if ts < since or not o.get("author"):
            continue
        lane = infer_lane(norm_files(o.get("files", []), cfg), globs)
        lanes[lane]["contributors"][o["author"]] += 1
        lanes[lane]["last"] = max(lanes[lane]["last"], str(o.get("ts", ""))[:10])
    out = []
    for name, L in lanes.items():
        contrib = sorted(L["contributors"].items(), key=lambda kv: -kv[1])
        out.append({"lane": name, "facts": L["facts"], "findings": L["findings"], "findings_open": L["findings_open"],
                    "contributors": [{"name": a, "observations": n} for a, n in contrib], "overlap": len(contrib) >= 2,
                    "files": sorted({"/".join(f.split("/")[-2:]) for f in L["files"]})[:4], "last": L["last"], "window_days": days})
    out.sort(key=lambda r: (-r["overlap"], -(r["facts"] + r["findings"]), r["lane"]))
    return out
