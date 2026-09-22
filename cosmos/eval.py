"""Recall eval: for facts with evidence, ask "would this fact reach an agent working on that file / asking a
new developer's question?" and measure recall@k. Run at will (`cosmos eval`) and recorded by each dream, so a change
to retrieval or to the reading prompt shows up as a number, not an impression.

Questions come from two places: the fact's own evidence files (a developer opening that file should see it), and
questions the model wrote for the fact at dream time (`meta.eval_q`), when a model is available.
"""
from __future__ import annotations

from typing import Dict, List, Tuple

from .config import Config
from .retrieve import retrieve
from .store import Ledger, Memory


def cases(mems: Dict[str, Memory], limit: int = 300) -> List[Tuple[str, str, List[str]]]:
    """(fact id, question, paths) — the fact should be in the top k for that question."""
    out: List[Tuple[str, str, List[str]]] = []
    for m in sorted(mems.values(), key=lambda m: -m.importance):
        if m.status != "active" or m.category == "finding":
            continue
        if m.files:
            out.append((m.id, m.files[0].rsplit("/", 1)[-1], [m.files[0]]))
        q = m.meta.get("eval_q")
        if q:
            out.append((m.id, q, []))
        if len(out) >= limit:
            break
    return out


def run(cfg: Config, k: int = 5) -> Dict:
    mems = Ledger(cfg.paths).load()
    cs = cases(mems)
    hits = 0
    misses: List[Tuple[str, str]] = []
    by_kind = {"file": [0, 0], "question": [0, 0]}
    for mid, q, paths in cs:
        got = [m.id for m in retrieve(mems, q, paths=paths or None, k=k)]
        kind = "file" if paths else "question"
        by_kind[kind][1] += 1
        if mid in got:
            hits += 1; by_kind[kind][0] += 1
        else:
            misses.append((mid, q))
    return {"cases": len(cs), "recall_at_k": round(hits / len(cs), 3) if cs else None, "k": k,
            "by_kind": {kk: (round(v[0] / v[1], 3) if v[1] else None) for kk, v in by_kind.items()},
            "misses": misses[:20]}
