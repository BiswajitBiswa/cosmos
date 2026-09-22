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


def score(mem: Memory, q_tokens: Set[str], q_paths: Set[str]) -> float:
    m_tokens = tokens(mem.text) | set(t.lower() for t in mem.tags)
    m_paths = path_tokens(mem.files)
    overlap = len(q_tokens & m_tokens) / (len(q_tokens) ** 0.5 + 1) if q_tokens else 0.0
    poverlap = len(q_paths & (m_paths | m_tokens)) / (len(q_paths) ** 0.5 + 1) if q_paths else 0.0
    if overlap == 0 and poverlap == 0:
        return 0.0
    return (overlap * 1.0 + poverlap * 1.4) * (0.5 + mem.confidence) * (0.5 + mem.importance) * _recency(mem)


def retrieve(mems: Dict[str, Memory], query: str = "", paths: Optional[Iterable[str]] = None, k: int = 6, include_doubtful: bool = False) -> List[Memory]:
    """Facts for a query. Only *active* facts are returned: a stale candidate or a contradicted fact is a question for
    a human on Verdicts, never something handed to an agent as knowledge (it would cite it)."""
    q_tokens = tokens(query)
    q_paths = path_tokens(paths or [])
    ranked = []
    for m in mems.values():
        if m.status != "active" and not (include_doubtful and m.status in ("stale-candidate", "contradicted")):
            continue
        s = score(m, q_tokens, q_paths)
        if s > 0:
            ranked.append((s, m))
    ranked.sort(key=lambda x: -x[0])
    return [m for _, m in ranked[:k]]


def top(mems: Dict[str, Memory], k: int = 10) -> List[Memory]:
    """Orientation set: most important active memories, explicit first."""
    live = [m for m in mems.values() if m.status == "active"]
    live.sort(key=lambda m: (-(m.source == "explicit"), -(m.importance * m.confidence), -m.evidence_count))
    return live[:k]


def format_for_agent(mems: List[Memory], header: str) -> str:
    if not mems:
        return ""
    lines = [header]
    for m in mems:
        flag = "" if m.status == "active" else f" (UNVERIFIED: {m.status} — check before relying on it)"
        files = f" — see `{m.files[0]}`" if m.files else ""
        verified = f" (verified {m.last_verified})" if m.last_verified else ""
        lines.append(f"- [{m.category}] {m.text}{files}{verified}{flag}")
    lines.append("(Details: `.cosmos/ledger/_index.md`; `cosmos why <id|text>` explains any item.)")
    return "\n".join(lines)
