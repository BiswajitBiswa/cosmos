"""Gate: the Stop hook that holds the AI's turn until the team's checklist is met.

The calls that repeat on every project - "did you run the tests?", "point at the exact file", "review your own
change" - become a rule the machine applies. When a turn edited code but ran no tests, or made claims without
file:line references, the Gate returns exit 2 with a precise list of what is missing; Claude continues and fixes
it. `stop_hook_active` guarantees we never loop: a turn that already continued once is let through.
"""
from __future__ import annotations

import fnmatch
import re
from pathlib import Path
from typing import Any, Dict, List

from .charter import gate_config
from .config import Config
from .store import Ledger, State
from .transcript import Turn, iter_turns, relativize

REF = re.compile(r"[\w\-./]+\.(?:py|ts|tsx|js|jsx|kt|java|go|rs|rb|sql|sh|yml|yaml|toml|json|md):\d+")


def _matches(path: str, globs: List[str]) -> bool:
    return any(fnmatch.fnmatch(path, g) or fnmatch.fnmatch(path.split("/")[-1], g) for g in globs)


def current_turn(turns: List[Turn]) -> List[Turn]:
    """Everything after the last human message = the assistant's current turn."""
    for i in range(len(turns) - 1, -1, -1):
        if turns[i].role == "user":
            return turns[i + 1:]
    return turns


def evaluate(cfg: Config, event: Dict[str, Any]) -> Dict[str, Any]:
    """Returns {"block": bool, "reasons": [...], "edited": [...], "findings": [...]}."""
    gc = gate_config(cfg)
    result = {"block": False, "reasons": [], "edited": [], "findings": []}
    if not gc.get("enabled", True) or event.get("stop_hook_active"):
        return result
    tp = event.get("transcript_path")
    if not tp or not Path(tp).exists():
        return result
    state = State(cfg.paths)
    sid = event.get("session_id", "")
    # gate keeps its own offset so it never disturbs capture; it re-reads the whole turn each time
    turns, _ = iter_turns(Path(tp), 0)
    turn = current_turn(turns)
    if not turn:
        return result
    root = cfg.paths.root
    edited = []
    for t in turn:
        for f in t.files:
            rel = relativize(f, root)
            if _matches(rel, gc.get("skip_globs", [])) or not _matches(rel, gc.get("code_globs", ["**/*"])):
                continue
            if rel not in edited:
                edited.append(rel)
    result["edited"] = edited
    if not edited:
        return result
    commands = [c for t in turn for c in t.commands]
    tests_ran = any(any(p in c for p in gc.get("test_patterns", [])) for c in commands)
    last_text = next((t.text for t in reversed(turn) if t.role == "assistant" and t.text.strip()), "")
    has_refs = bool(REF.search(last_text))
    if gc.get("require_tests", True) and not tests_ran:
        result["reasons"].append(f"You edited {len(edited)} code file(s) but ran no tests this turn. Run the tests that cover: " + ", ".join(edited[:6]) + ". If none exist, say so explicitly and state what was NOT tested.")
    if gc.get("require_refs", True) and not has_refs:
        result["reasons"].append("Point precisely: your summary has no `path/to/file.ext:line` references. Cite the exact location of each change you made.")
    # open findings on the edited files must not be silently ignored
    mems = Ledger(cfg.paths).load()
    from .audit import OPEN_LIKE
    hits = [m for m in mems.values() if m.category == "finding" and m.meta.get("finding_status", "open") in OPEN_LIKE
            and any(any(ef.endswith(mf) or mf.endswith(ef) for ef in edited) for mf in m.files)]
    result["findings"] = [f"{m.meta.get('audit_id')} — {m.text}" for m in hits[:5]]
    if hits and not any((m.meta.get("audit_id") or "") in last_text for m in hits):
        result["reasons"].append("Open findings exist on files you touched — address or explicitly defer each: " + "; ".join(result["findings"]))
    if result["reasons"]:
        result["block"] = True
        result["reasons"].append("Then re-read your diff against .cosmos/charter.md (self-review) and stop.")
    return result


def message(res: Dict[str, Any]) -> str:
    lines = ["GATE (.cosmos/charter.md) — before you stop:"]
    lines += [f"{i}. {r}" for i, r in enumerate(res["reasons"], 1)]
    return "\n".join(lines)
