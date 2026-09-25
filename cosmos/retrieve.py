"""Context-aware retrieval: rank memories for a prompt / set of files. Pure token overlap; no vectors."""
from __future__ import annotations

import re
from datetime import date
from typing import Dict, Iterable, List, Optional, Set

from .store import Memory

STOP = set("""a an the and or but if then else of to in on at for from by with without into over under is are was were be been
being do does did done have has had this that these those it its as not no yes we you they i he she our your their can could
should would will shall may might must also just only very more most less least than so such via per each any all some""".split())

_TOKEN = re.compile(r"[a-zA-Z][a-zA-Z0-9_\-]{2,}")


def _stem(t: str) -> str:
    """Tiny plural/verb normaliser: webhooks→webhook, retries→retry, locking→lock."""
    if len(t) > 5 and t.endswith("ies"):
        return t[:-3] + "y"
    if len(t) > 5 and t.endswith("ing"):
        return t[:-3]
    if len(t) > 4 and t.endswith("s") and not t.endswith("ss"):
        return t[:-1]
    return t


def tokens(text: str) -> Set[str]:
    out: Set[str] = set()
    for t in _TOKEN.findall(text.lower()):
        if t in STOP:
            continue
        out.add(_stem(t))
        for part in re.split(r"[_\-]", t):     # snake_case / kebab parts
            if len(part) > 2 and part not in STOP:
                out.add(_stem(part))
    return out


def path_tokens(paths: Iterable[str]) -> Set[str]:
    out: Set[str] = set()
    for p in paths:
        for seg in re.split(r"[/\\.]", p.lower()):
            if len(seg) > 2 and seg not in STOP:
                out.add(_stem(seg))
    return out


def _recency(mem: Memory) -> float:
    try:
        days = (date.today() - date.fromisoformat(mem.updated)).days
    except Exception:
        days = 365
    return max(0.3, 1.0 - days / 365.0)


_IDF_CACHE: Dict[int, Dict[str, float]] = {}


def _doc_terms(mem: Memory) -> Dict[str, int]:
    """Term frequencies of a note: its text, tags, lane and the path segments of its evidence files. Kept on the note
    and recomputed only when one of those changes (a query scores every note; tokenising them each time dominated)."""
    key = (mem.text, tuple(mem.tags), tuple(mem.files), mem.lane)
    cached = mem.__dict__.get("_terms")
    if cached and cached[0] == key:
        return cached[1]
    counts: Dict[str, int] = {}
    for t in list(tokens(mem.text)) + [t.lower() for t in mem.tags] + list(path_tokens(mem.files)) + ([mem.lane] if mem.lane else []):
        counts[t] = counts.get(t, 0) + 1
    mem.__dict__["_terms"] = (key, counts)
    return counts


def _idf(mems: Dict[str, Memory]) -> Dict[str, float]:
    """Inverse document frequency over the live ledger (BM25 flavour), cached per ledger identity."""
    import math
    key = id(mems)
    if key in _IDF_CACHE and _IDF_CACHE[key].get("__n__") == float(len(mems)):
        return _IDF_CACHE[key]
    df: Dict[str, int] = {}
    for m in mems.values():
        for t in _doc_terms(m):
            df[t] = df.get(t, 0) + 1
    n = max(1, len(mems))
    idf = {t: math.log(1 + (n - d + 0.5) / (d + 0.5)) for t, d in df.items()}
    idf["__n__"] = float(len(mems))
    idf["__avgdl__"] = max(1.0, sum(sum(_doc_terms(m).values()) for m in mems.values()) / n)
    _IDF_CACHE.clear(); _IDF_CACHE[key] = idf
    return idf


def score(mem: Memory, q_tokens: Set[str], q_paths: Set[str], idf: Optional[Dict[str, float]] = None, avgdl: float = 12.0) -> float:
    """BM25 over note terms with a stronger weight on evidence-path matches, then scaled by confidence, importance and recency."""
    terms = _doc_terms(mem)
    if not terms:
        return 0.0
    dl = sum(terms.values())
    k1, b = 1.2, 0.5
    def bm25(q: Set[str], weight: float) -> float:
        s = 0.0
        for t in q:
            f = terms.get(t, 0)
            if not f:
                continue
            w = (idf or {}).get(t, 1.0)
            s += w * (f * (k1 + 1)) / (f + k1 * (1 - b + b * dl / avgdl)) * weight
        return s
    raw = bm25(q_tokens, 1.0) + bm25(q_paths, 1.6)
    if raw == 0:
        return 0.0
    return raw * (0.5 + mem.confidence) * (0.5 + mem.importance) * _recency(mem)


def retrieve(mems: Dict[str, Memory], query: str = "", paths: Optional[Iterable[str]] = None, k: int = 6, include_doubtful: bool = False) -> List[Memory]:
    """Facts for a query. Only *active* facts are returned: a stale candidate or a contradicted fact is a question for
    a human on Verdicts, never something handed to an agent as knowledge (it would cite it)."""
    q_tokens = tokens(query)
    q_paths = path_tokens(paths or [])
    idf = _idf(mems)
    avgdl = idf.get("__avgdl__") or max(1.0, sum(sum(_doc_terms(m).values()) for m in mems.values()) / max(1, len(mems)))
    ranked = []
    for m in mems.values():
        if m.status != "active" and not (include_doubtful and m.status in ("stale-candidate", "contradicted")):
            continue
        s = score(m, q_tokens, q_paths, idf, avgdl)
        if s > 0:
            ranked.append((s, m))
    ranked.sort(key=lambda x: -x[0])
    return [m for _, m in ranked[:k]]


def top(mems: Dict[str, Memory], k: int = 10) -> List[Memory]:
    """Orientation set: most important active memories, explicit first."""
    live = [m for m in mems.values() if m.status == "active"]
    live.sort(key=lambda m: (-(m.source == "explicit"), -(m.importance * m.confidence), -m.evidence_count))
    return live[:k]


def brief(text: str, n: int = 140) -> str:
    """One line of a fact, cut at a word boundary. The full note is always one call away."""
    t = " ".join(text.split())
    if len(t) <= n:
        return t
    cut = t[:n].rsplit(" ", 1)[0]
    return cut + " …"


def format_for_agent(mems: List[Memory], header: str, compact: bool = True) -> str:
    """Progressive disclosure: ~30 tokens per fact (category · lane · one line · first file · id). An agent that
    needs the reasoning, the evidence and the history asks cosmos_why / `cosmos why <id>` for that one fact."""
    if not mems:
        return ""
    lines = [header]
    for m in mems:
        flag = "" if m.status == "active" else f" (UNVERIFIED: {m.status} — check before relying on it)"
        files = f" — `{m.files[0]}`" if m.files else ""
        lane = f" · {m.lane}" if m.lane and m.lane != "general" else ""
        text = brief(m.text) if compact else m.text
        lines.append(f"- [{m.category}{lane}] {text}{files} · {m.id}{flag}")
    lines.append("(One line each. Full note with evidence and history: cosmos_why <id>, or `cosmos why <id>`.)")
    return "\n".join(lines)
