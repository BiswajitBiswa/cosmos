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
    from collections import Counter
    out: List[Tuple[str, str, List[str]]] = []
    per_file = Counter(f for m in mems.values() if m.status == "active" and m.category != "finding" for f in m.files[:1])
    for m in sorted(mems.values(), key=lambda m: -m.importance):
        if m.status != "active" or m.category == "finding":
            continue
        # a file with more facts than fit in the answer cannot rank any one of them first: those are measured by
        # run_edits, which asks with the code being changed instead of the file name
        if m.files and per_file[m.files[0]] <= 5:
            out.append((m.id, m.files[0].rsplit("/", 1)[-1], [m.files[0]]))
        q = m.meta.get("eval_q")
        if q:
            out.append((m.id, q, []))
        if len(out) >= limit:
            break
    return out


def edit_cases(cfg: Config, mems: Dict[str, Memory], limit: int = 200) -> List[Tuple[str, str, str]]:
    """(fact id, file, edit text): the lines of the fact's file around an identifier the fact names — an agent
    changing exactly that code should be shown the fact."""
    import re
    out: List[Tuple[str, str, str]] = []
    for m in sorted(mems.values(), key=lambda m: m.id):
        if m.status != "active" or m.category == "finding" or not m.files:
            continue
        p = cfg.paths.root / m.files[0]
        idents = [i for i in re.findall(r"`([A-Za-z_][\w.]{3,})`", m.text) if "/" not in i and "." not in i[-4:]]
        if not idents or not p.is_file():
            continue
        try:
            lines = p.read_text(errors="ignore").splitlines()
        except OSError:
            continue
        at = next((n for n, l in enumerate(lines) if idents[0] in l), None)
        if at is None:
            continue
        out.append((m.id, m.files[0], "\n".join(lines[max(0, at - 3):at + 4])))
        if len(out) >= limit:
            break
    return out


def run_edits(cfg: Config) -> Dict:
    """How often the fact about the code being changed is among those shown before the edit."""
    from . import hooks
    mems = Ledger(cfg.paths).load()
    cs = edit_cases(cfg, mems)
    hits = 0
    for n, (mid, f, text) in enumerate(cs):
        sid = f"eval-{n}"
        out = hooks.file_context(cfg, {"session_id": sid, "tool_input": {"file_path": str(cfg.paths.root / f), "old_string": text, "new_string": text}})
        hits += mems[mid].text[:60] in out
    from .store import State
    st = State(cfg.paths)                              # eval sessions leave no trace
    for n in range(len(cs)):
        st.data.get("shown_facts", {}).pop(f"eval-{n}", None)
    st.save()
    return {"cases": len(cs), "hit_rate": round(hits / len(cs), 3) if cs else None}


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
