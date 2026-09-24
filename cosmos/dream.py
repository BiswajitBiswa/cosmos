"""The dream cycle: observations + existing ledger -> deduplicated, contradiction-checked, time-aware ledger.

Deterministic by default. An LLM provider, when configured and reachable, refines the result; its
output is validated and merged - never trusted blindly.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import date
from typing import Dict, List, Optional, Set, Tuple

from .config import Config
from .providers import get_provider
from .retrieve import tokens
from .store import Ledger, Memory, Observations, State, make_id, today

NEGATION = re.compile(r"\b(never|not|don't|do not|shouldn't|should not|no longer|avoid|deprecated|removed)\b", re.I)
_PATHISH = re.compile(r"`[^`]+`|[\w\-/]+\.(?:py|ts|tsx|js|kt|java|go|rs|rb|md|json|ya?ml|toml|sql|sh)\b")


def _negated_predicate(text: str) -> bool:
    """Negation in the predicate position (first ~8 words) - tail-clause negation is usually a reason, not a flip."""
    head = " ".join(text.split()[:8])
    return bool(NEGATION.search(head))
TECH = re.compile(r"\b(Redis|Postgres(?:QL)?|MySQL|SQLite|Kafka|RabbitMQ|SQS|Snowflake|ClickHouse|BigQuery|Mongo\w*|DynamoDB|Docker|Kubernetes|Stripe|GraphQL|gRPC|REST|Authentik|Auth0|Keycloak|Celery|Spark|Airflow|Kestra|Dagster|React|Vue|Django|FastAPI|Flask|Express|Kotlin|Ktor|Gradle|Maven|npm|pnpm|yarn|pip|uv|poetry|pytest|jest|vitest)\b")


@dataclass
class DreamReport:
    new: List[Memory] = field(default_factory=list)
    merged: List[Tuple[str, str]] = field(default_factory=list)        # (obs text, into id)
    contradictions: List[Tuple[str, str]] = field(default_factory=list)  # (older id, newer id)
    superseded: List[Tuple[str, str]] = field(default_factory=list)
    stale: List[str] = field(default_factory=list)
    revived: List[str] = field(default_factory=list)
    llm_used: bool = False
    llm_available: bool = False
    observations_processed: int = 0
    dropped: int = 0
    recurated: int = 0
    recurated_dropped: int = 0
    journal_entries: int = 0
    windows_read: int = 0
    turns_read: int = 0
    windows_waiting: int = 0
    auto_memory_notes: int = 0
    atlas_deep: bool = False
    fallback_windows: int = 0
    flares_closed: int = 0
    verified: int = 0
    retired: int = 0
    git_commits: int = 0
    review_comments: int = 0
    recall_at_5: Optional[float] = None

    def to_dict(self) -> Dict:
        return {"new": [{"id": m.id, "text": m.text, "category": m.category} for m in self.new],
                "merged": [{"text": t, "into": i} for t, i in self.merged],
                "contradictions": [{"older": a, "newer": b} for a, b in self.contradictions],
                "superseded": [{"old": a, "by": b} for a, b in self.superseded],
                "stale": list(self.stale), "revived": list(self.revived), "llm_used": self.llm_used,
                "observations_processed": self.observations_processed, "dropped": self.dropped, "recurated": self.recurated, "recurated_dropped": self.recurated_dropped, "journal_entries": self.journal_entries, "recall_at_5": self.recall_at_5, "git_commits": self.git_commits, "review_comments": self.review_comments, "windows_read": self.windows_read, "turns_read": self.turns_read, "windows_waiting": self.windows_waiting, "auto_memory_notes": self.auto_memory_notes, "fallback_windows": self.fallback_windows, "llm_available": self.llm_available, "summary": self.summary()}

    def summary(self) -> str:
        return (f"{self.observations_processed} observations → {len(self.new)} new, {len(self.merged)} merged, "
                f"{len(self.contradictions)} contradictions, {len(self.superseded)} superseded, {len(self.stale)} stale"
                + (f" · LLM curated, {self.dropped} dropped as noise" if self.llm_used and self.observations_processed else "")
                + (f" · re-curated {self.recurated} existing facts, {self.recurated_dropped} retired" if self.recurated else "")
                + (f" · {self.journal_entries} journal entries written" if self.journal_entries else "")
                + (f" · model read {self.turns_read} turns" if self.turns_read else "")
                + (f" · {self.auto_memory_notes} auto memory notes offered" if self.auto_memory_notes else "")
                + (" · atlas deep pass started" if self.atlas_deep else "")
                + (f" · {self.windows_waiting} session ranges still waiting for a model" if self.windows_waiting else "")
                + (f" · {self.fallback_windows} ranges read heuristically (no model for days)" if self.fallback_windows else "")
                + (f" · {self.flares_closed} flares marked fixed by commit messages" if self.flares_closed else "")
                + (f" · model verified {self.verified} doubtful facts still true, retired {self.retired}" if (self.verified or self.retired) else "")
                + (f" · recall@5 {self.recall_at_5:.2f}" if isinstance(self.recall_at_5, float) else "")
                + (f" · {self.git_commits} commits from git history" if self.git_commits else "")
                + (f" · {self.review_comments} review comments offered" if self.review_comments else "")
                + (f" · {len(self.revived)} came back with fresh evidence" if self.revived else "")
                + ("" if self.llm_available else " · heuristics only — no LLM available (cosmos doctor)"))


def jaccard(a: Set[str], b: Set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _subject(text: str) -> Set[str]:
    """First few content tokens ≈ what the sentence is about."""
    toks = [t for t in re.findall(r"[a-zA-Z][a-zA-Z0-9_\-]{2,}", text.lower()) if t not in ("the", "this", "that", "with", "for", "and")]
    return set(toks[:4])


def _choices(text: str) -> Set[str]:
    """Technology entities named in the sentence (plus non-initial Capitalized words)."""
    ents = {m.group(1).lower() for m in TECH.finditer(text)}
    for m in re.finditer(r"(?<![.!?]\s)(?<!^)\b([A-Z][a-z]{2,})\b", text):
        if m.start() > 0:
            ents.add(m.group(1).lower())
    return ents


def looks_contradictory(a: Memory, b: Memory) -> bool:
    """Conservative: same category, clearly the same subject, and either a different technology choice or a negated predicate."""
    if a.category != b.category or a.category not in ("decision", "architecture", "constraint", "convention", "workflow", "dependency"):
        return False
    ta, tb = tokens(a.text), tokens(b.text)
    j = jaccard(ta, tb)
    if j >= 0.6:            # near-duplicate, handled by merge
        return False
    if len(ta & tb) < 3 or j < 0.25:
        return False        # not about the same thing
    # statements anchored on the same file / code identifier describe the same thing, not a conflict
    if set(_PATHISH.findall(a.text)) & set(_PATHISH.findall(b.text)):
        return False
    ca = {m.group(1).lower() for m in TECH.finditer(a.text)}
    cb = {m.group(1).lower() for m in TECH.finditer(b.text)}
    neg_flip = _negated_predicate(a.text) != _negated_predicate(b.text)
    if ca and cb:
        return neg_flip if (ca & cb) else True      # same tech + one negated, or different tech for the same subject
    return neg_flip and j >= 0.4


_IDENT = re.compile(r"`([A-Za-z_][A-Za-z0-9_./-]{4,})`|\b([A-Za-z_]*[a-z][A-Za-z0-9]*_[A-Za-z0-9_]{2,}|[A-Z_]{2,}[A-Z0-9_]{4,}|[a-z]+[A-Z][A-Za-z0-9]{3,})\b")


def _missing_identifiers(root, m: Memory) -> List[str]:
    """Code identifiers named by the fact (snake_case, CONSTANTS, camelCase, backticked names) that appear in none of
    its evidence files any more. Cheap, deterministic, and the reason most facts go wrong: the code moved on."""
    if not m.files:
        return []
    names = []
    for a, b in _IDENT.findall(m.text):
        n = (a or b).strip()
        if n and n not in names and "/" not in n and "." not in n.strip(".") and len(n) >= 5:
            names.append(n)
    if not names:
        return []
    blobs = []
    for f in m.files[:8]:
        p = root / f
        try:
            if p.is_file() and p.stat().st_size < 2_000_000:
                blobs.append(p.read_text(errors="ignore"))
        except Exception:
            continue
    if not blobs:
        return []
    return [n for n in names if not any(n in b for b in blobs)]


_TREE_CACHE: Dict[str, Set[str]] = {}


def _repo_paths(root) -> Set[str]:
    """Every tracked path across all worktrees of this repository (a fact recorded on the aura branch keeps its
    evidence even while you sit on another branch). Cached per process."""
    key = str(root)
    if key in _TREE_CACHE:
        return _TREE_CACHE[key]
    import subprocess
    from .transcript import worktrees
    paths: Set[str] = set()
    for wt in worktrees(root):
        try:
            out = subprocess.run(["git", "ls-files", "-z"], cwd=wt, capture_output=True, text=True, timeout=20).stdout
            paths.update(p for p in out.split("\0") if p)
        except Exception:
            continue
    _TREE_CACHE[key] = paths
    return paths


def _files_exist(root, files: List[str]) -> Optional[bool]:
    """None when the fact cites no files; True when any cited file exists in this checkout or is tracked in any
    worktree of the repository; False only when the evidence is gone everywhere."""
    if not files:
        return None
    if any((root / f).exists() for f in files):
        return True
    tracked = _repo_paths(root)
    return any(f in tracked or f.lstrip("./") in tracked for f in files)


def _present_in_repo(root, idents: List[str]) -> Set[str]:
    """Which of these identifiers appear anywhere in the repository (any worktree), in one git grep per worktree."""
    if not idents:
        return set()
    import subprocess, tempfile
    from .transcript import worktrees
    found: Set[str] = set()
    with tempfile.NamedTemporaryFile("w", delete=False) as fh:
        fh.write("\n".join(idents) + "\n"); pat = fh.name
    try:
        for wt in worktrees(root):
            try:
                out = subprocess.run(["git", "grep", "-h", "-o", "-I", "-F", "-f", pat], cwd=wt, capture_output=True, text=True, timeout=60).stdout
                found.update(l.strip() for l in out.splitlines() if l.strip())
            except Exception:
                continue
            if found >= set(idents):
                break
    finally:
        import os
        os.unlink(pat)
    return found


def dream(cfg: Config, use_llm: Optional[bool] = None, verbose: bool = False, recurate_all: bool = False) -> DreamReport:
    import time
    started = time.time()
    root = cfg.paths.root
    ledger, obs_store, state = Ledger(cfg.paths), Observations(cfg.paths), State(cfg.paths)
    mems = ledger.load()
    report = DreamReport()
    t = today()

    # ---- 1. gather un-dreamed observations
    pending = [o for o in obs_store.iter_all() if o.get("id") and not state.is_dreamed(o["id"])]
    # ---- 1a. the journal (what was done) is written down first, always; entries with commits or edits are also
    #          offered to the model - a commit message often carries a decision worth keeping as a fact
    from . import journal as _journal
    want_llm = cfg.get("dream.llm", "auto") if use_llm is None else use_llm
    prov = get_provider(cfg.get("llm", {}) or {}) if want_llm else None
    report.llm_available = prov is not None
    from . import sources as _sources
    try:   # git history and PR reviews: the whole team, no agent required on their side
        known_msgs = {c for o in pending if o.get("kind") == "journal" for c in (o.get("commits") or [])} | {c for o in obs_store.iter_all() if o.get("kind") == "journal" for c in (o.get("commits") or [])}
        n_git, git_cands = _sources.ingest_git(cfg, state, obs_store, known_msgs)
        rev_cands = _sources.ingest_reviews(cfg, state, obs_store) if prov is not None else []
        if git_cands or rev_cands:
            obs_store.append(git_cands + rev_cands)
        pending = [o for o in obs_store.iter_all() if o.get("id") and not state.is_dreamed(o["id"])]
        report.git_commits, report.review_comments = n_git, len(rev_cands)
    except Exception as e:
        if verbose:
            print(f"  sources skipped: {str(e)[:160]}")
    journals = [o for o in pending if o.get("kind") == "journal"]
    report.journal_entries = _journal.persist(cfg, journals, mems)
    report.flares_closed = _flares_from_commits(cfg, journals, mems)
    pending = [o for o in pending if o.get("kind") != "journal"] + [dict(o, text="Work done: " + o["text"]) for o in journals if o.get("commits")]
    state.mark_dreamed(o["id"] for o in journals)

    # ---- 1b. LLM curation: the model decides what is worth keeping, rewrites it, names category + lane.
    from . import reader as _reader
    if prov is not None:
        try:   # the model reads the session ranges the hooks marked, and this developer's own Claude Code notes
            rr = _reader.read_windows(cfg, prov, mems, state, obs_store, int(cfg.get("dream.read_budget", 30)), verbose)
            report.windows_read, report.turns_read = rr.windows_read, rr.turns_read
            pending += rr.new
            am = _reader.auto_memory_candidates(cfg, state)
            if am:
                obs_store.append(am)
                pending += am
                report.auto_memory_notes = len(am)
            report.llm_used = report.llm_used or bool(rr.chunks_read or am)
        except Exception as e:
            if verbose:
                print(f"  reading skipped: {str(e)[:160]}")
    else:
        fb = _reader.fallback_windows(cfg, state, obs_store, int(cfg.get("capture.fallback_days", 3)))
        report.fallback_windows = fb.fallback
        pending += fb.new
    report.windows_waiting = _reader.windows_waiting(state)
    seen_ids = [o["id"] for o in pending]
    report.observations_processed = len(pending)
    if prov is not None and pending:
        try:
            todo = [o for o in pending if not o.get("curated")]
            kept, dropped = _llm_curate(prov, cfg, todo, mems, verbose)
            kept_ids = {o["id"] for o in kept}
            state.mark_dreamed(o["id"] for o in todo if o["id"] not in kept_ids)   # dropped as noise: done, never offered again
            pending = [o for o in pending if o.get("curated") and o not in todo] + kept
            report.dropped = dropped
            report.llm_used = True
        except Exception as e:  # the deterministic path still runs
            if verbose:
                print(f"  llm curation skipped: {str(e)[:160]}")
            prov = None
    # ---- 1c. facts built before a model was available get the same treatment, once
    if prov is not None:
        stale_facts = [m for m in mems.values() if m.category != "finding" and m.status in ("active", "stale-candidate", "contradicted")
                       and m.source != "explicit" and (recurate_all or not m.meta.get("curated"))]
        if stale_facts:
            try:
                n, d = _llm_recurate(prov, cfg, stale_facts, mems, verbose)
                report.recurated, report.recurated_dropped, report.llm_used = n, d, True
            except Exception as e:
                if verbose:
                    print(f"  llm re-curation skipped: {str(e)[:160]}")

    # ---- 2. normalize + dedupe into memories (deterministic)
    index: List[Tuple[Set[str], Memory]] = [(tokens(m.text), m) for m in mems.values()]
    for o in pending:
        if o.get("kind") == "journal" and not o.get("curated"):
            continue   # raw work log without a model's rewrite is not a fact
        text = " ".join(str(o.get("text", "")).split())
        if len(text) < 12:
            continue
        otoks = tokens(text)
        best, best_j = None, 0.0
        for mt, m in index:
            if m.category != o.get("category") and o.get("source") != "explicit":
                continue
            j = jaccard(otoks, mt)
            if j > best_j:
                best, best_j = m, j
        if best is not None and best_j >= 0.6:
            best.evidence_count += 1
            best.updated = t
            best.last_verified = t
            best.confidence = min(0.98, best.confidence + 0.05)
            if o.get("source") == "explicit":
                best.source, best.importance = "explicit", max(best.importance, 0.9)
            for f in o.get("files", []):
                if f not in best.files and len(best.files) < 8:
                    best.files.append(f)
            for a in ([o.get("author")] if o.get("author") else []):
                if a not in best.authors:
                    best.authors.append(a)
            if best.status == "stale-candidate":
                best.status = "active"
                report.revived.append(best.id)
            report.merged.append((text, best.id))
            continue
        mem = Memory(
            id=make_id(text), text=text, category=o.get("category", "domain"),
            confidence=0.9 if o.get("source") == "explicit" else min(0.85, 0.45 + float(o.get("score", 0.5)) * 0.4),
            importance=0.9 if o.get("source") == "explicit" else float(o.get("score", 0.5)),
            source=o.get("source", "observed"), created=str(o.get("ts", t))[:10] or t, updated=t, last_verified=t,
            files=list(o.get("files", []))[:8], authors=[o["author"]] if o.get("author") else [],
            sessions=[o["session"]] if o.get("session") else [],
        )
        mem.tags = sorted(_auto_tags(mem))[:6]
        from .lanes import clean_lane
        if clean_lane(o.get("lane") or ""):
            mem.lane = clean_lane(o["lane"])
            mem.meta["lane_by"] = "model"
        if o.get("curated"):
            mem.meta["curated"] = f"llm:{t}"
            mem.source = "llm"
        mems[mem.id] = mem
        index.append((otoks, mem))
        if o.get("eval_q"):
            mem.meta["eval_q"] = str(o["eval_q"])[:200]
        report.new.append(mem)

    # ---- 3. contradictions (deterministic candidates; supersession only with evidence)
    live = [m for m in mems.values() if m.status in ("active", "contradicted", "stale-candidate")]
    for i in range(len(live)):
        for j in range(i + 1, len(live)):
            a, b = live[i], live[j]
            if a.status == "superseded" or b.status == "superseded":
                continue
            if not looks_contradictory(a, b):
                continue
            older, newer = sorted((a, b), key=lambda m: (m.updated, m.created))
            if newer.id in older.contradicts:
                continue
            a_exists, b_exists = _files_exist(root, older.files), _files_exist(root, newer.files)
            if a_exists is False and b_exists:
                # evidence for the old fact is gone and the new fact's evidence is present
                older.status, older.superseded_by, older.updated = "superseded", newer.id, t
                older.reason = f"Superseded on {t}: evidence files no longer exist; see [[{newer.id}]]"
                newer.supersedes = older.id
                report.superseded.append((older.id, newer.id))
            elif newer.source == "explicit" and older.source != "explicit":
                older.status, older.superseded_by, older.updated = "superseded", newer.id, t
                older.reason = f"Superseded on {t} by an explicit developer rule [[{newer.id}]]"
                newer.supersedes = older.id
                report.superseded.append((older.id, newer.id))
            else:
                for m, other in ((older, newer), (newer, older)):
                    if other.id not in m.contradicts:
                        m.contradicts.append(other.id)
                    m.status = "contradicted"
                    m.updated = t
                report.contradictions.append((older.id, newer.id))

    # ---- 4. temporal: stale candidates + missing evidence
    thresholds = cfg.get("dream.staleness_days", {}) or {}
    # identifiers missing from evidence files are checked against the whole repository in one pass, so a name that
    # merely moved to another file (or lives on another branch) does not make a fact stale
    candidates = {m.id: _missing_identifiers(root, m) for m in mems.values()
                  if m.status in ("active", "stale-candidate") and m.source != "explicit" and m.files and cfg.get("dream.verify_identifiers", True)}
    all_idents = sorted({i for v in candidates.values() for i in v})
    present = _present_in_repo(root, all_idents) if all_idents else set()
    from .lanes import resolve_evidence
    for m in mems.values():
        if m.status in ("active", "stale-candidate") and m.files and _files_exist(root, m.files) is False:
            fixed = [r for r in (resolve_evidence(root, f) for f in m.files) if r]
            if fixed:                                  # the path was partial, or points into a sibling repo
                m.files = list(dict.fromkeys(fixed))[:8]
        if m.status == "stale-candidate" and (m.reason or "").startswith("Stale candidate since") and m.files \
                and ("evidence files" in (m.reason or "") or "no longer appears" in (m.reason or "")):
            # evidence-based doubt only: an age-based doubt is not answered by the files merely existing
            # automatically flagged earlier: if the evidence checks out again, the fact comes back by itself
            gone = [i for i in candidates.get(m.id, []) if i not in present]
            if _files_exist(root, m.files) is not False and not gone:
                m.status, m.updated, m.last_verified = "active", t, t
                m.reason = f"Evidence verified again on {t}"
                report.revived.append(m.id)
            continue
        if m.status != "active":
            continue
        limit = int(thresholds.get(m.category, thresholds.get("default", 180)))
        try:
            age = (date.fromisoformat(t) - date.fromisoformat(m.last_verified)).days
        except Exception:
            age = 0
        gone = [i for i in candidates.get(m.id, []) if i not in present]
        if _files_exist(root, m.files) is False:
            m.status, m.updated = "stale-candidate", t
            m.reason = f"Stale candidate since {t}: none of the evidence files exist anymore, in any worktree"
            report.stale.append(m.id)
        elif gone:
            m.status, m.updated = "stale-candidate", t
            m.reason = f"Stale candidate since {t}: `{gone[0]}` no longer appears in the evidence files or anywhere in the repository"
            report.stale.append(m.id)
        elif age > limit and m.source != "explicit" and m.category != "finding":
            m.status, m.updated = "stale-candidate", t
            m.reason = f"Stale candidate since {t}: not re-observed for {age} days (limit {limit}d for {m.category})"
            report.stale.append(m.id)
    # ---- 4c. the model settles what it can: it reads the evidence and says still true / outdated / unclear
    if prov is not None and cfg.get("dream.verify_stale", True):
        doubtful = [m for m in mems.values() if m.status == "stale-candidate" and m.category != "finding"
                    and any((root / f).is_file() for f in m.files)]   # nothing to show the model → a human decides
        if doubtful:
            try:
                v, r = _llm_verify_stale(prov, cfg, doubtful[: int(cfg.get("dream.verify_budget", 40))], t, verbose)
                report.verified, report.retired = v, r
                report.llm_used = report.llm_used or bool(v or r)
            except Exception as e:
                if verbose:
                    print(f"  stale verification skipped: {str(e)[:160]}")

    # ---- 4b. flares: an open flare whose anchor files no longer exist cannot be worked on — a human decides
    try:
        from .audit import OPEN_LIKE, set_status
        for m in list(mems.values()):
            if m.category == "finding" and m.files and m.meta.get("finding_status", "open") in OPEN_LIKE - {"needs_human"} \
                    and m.meta.get("severity") != "note" and _files_exist(root, m.files) is False:
                set_status(cfg, m, "needs_human", "anchor files no longer exist")
                report.flares_needs_human = getattr(report, "flares_needs_human", 0) + 1
    except Exception:
        pass

    # ---- 5. LLM refinement of merges / contradictions (validated)
    if want_llm and (report.new or report.contradictions):
        prov = prov or get_provider(cfg.get("llm", {}) or {})
        if prov is not None:
            try:
                _llm_refine(prov, mems, report, t)
                report.llm_used = True
            except Exception as e:  # never fail the dream because of the LLM
                if verbose:
                    print(f"  llm refinement skipped: {e}")

    # ---- 6. lanes (LLM-assigned lanes win; paths fill the rest), related links + persist
    _restore_model_lanes(mems, obs_store)
    from .lanes import assign_lanes
    assign_lanes(mems, cfg, only_missing=bool(report.llm_used))
    _link_related(mems)
    ledger.save_all(mems.values())
    state.mark_dreamed(seen_ids)
    state.save()
    try:   # the number that tells whether retrieval got better or worse
        from .eval import run as eval_run
        report.recall_at_5 = eval_run(cfg).get("recall_at_k")
    except Exception:
        pass
    _okf_conform(cfg)
    _persist_run(cfg, report, started)
    try:   # OKF log.md: chronological history of the bundle, newest first
        lp = cfg.paths.ledger / "log.md"
        old = lp.read_text() if lp.exists() else "# Log\n\n"
        entry = f"## {t}\n\n**Update**: {report.summary()[:300]}\n\n"
        body = old.split("\n", 2)[2] if old.startswith("# Log") else old
        lp.write_text("# Log\n\n" + entry + body)
    except Exception:
        pass
    try:   # the Atlas deep pass: the model follows the /atlas prompt in the background when the map is missing or has moved
        if want_llm is not False:
            from .atlas import deep_due, run_deep
            if deep_due(cfg) and run_deep(cfg):
                report.atlas_deep = True
    except Exception:
        pass
    try:
        from .sync import sync_background
        sync_background(cfg, "cosmos: dream — " + report.summary()[:100])
    except Exception:
        pass
    return report


def _flares_from_commits(cfg: Config, journals: List[Dict], mems: Dict[str, Memory]) -> int:
    """A commit message that names an open flare id closes it: `fix(auth): QA-12 …` → QA-12 fixed, note = the message."""
    from .audit import OPEN_LIKE, set_status
    open_ = {m.meta.get("audit_id"): m for m in mems.values() if m.category == "finding" and m.meta.get("audit_id")
             and m.meta.get("finding_status", "open") in OPEN_LIKE and m.meta.get("severity") != "note"}
    if not open_:
        return 0
    n = 0
    for j in journals:
        for msg in j.get("commits") or []:
            for aid in re.findall(r"\b[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*-\d+\b", msg):
                m = open_.pop(aid, None)
                if m is not None:
                    try:
                        set_status(cfg, m, "fixed", f"commit: {msg[:100]}")
                        n += 1
                    except SystemExit:
                        pass
    return n


def _restore_model_lanes(mems: Dict[str, Memory], obs_store) -> int:
    """A fact sitting in `general` whose source observation carried a model-chosen lane gets that lane back (earlier
    heuristic dreams re-inferred lanes from paths and lost it). Idempotent."""
    gen = {m.id: m for m in mems.values() if m.status != "forgotten" and (not m.lane or m.lane == "general") and m.meta.get("lane_by") != "model"}
    if not gen:
        return 0
    n = 0
    for o in obs_store.iter_all():
        lane = o.get("lane")
        if not lane or lane == "general":
            continue
        mid = make_id(" ".join(str(o.get("text", "")).split()))
        m = gen.pop(mid, None)
        if m is not None:
            m.lane, m.meta["lane_by"] = str(lane), "model"
            n += 1
    return n


def _okf_conform(cfg: Config) -> int:
    """Older notes written before the ledger became an OKF bundle get a `type` in their frontmatter (journal days,
    handoffs, horizon notes, atlas pages). Idempotent; returns how many files were touched."""
    kinds = {"journal": "Journal", "handoffs": "Handoff", "horizon": "Horizon", "intake": "Horizon", "atlas": "Diagram"}
    n = 0
    for p in cfg.paths.ledger.rglob("*.md"):
        if p.name in ("index.md", "log.md") or ".obsidian" in p.parts or p.name.startswith("mem_"):
            continue
        try:
            text = p.read_text(errors="ignore")
        except Exception:
            continue
        head = text[:600]
        if head.startswith("---") and re.search(r"^type:\s*\S", head, re.M):
            continue
        typ = next((kinds[part] for part in reversed(p.relative_to(cfg.paths.ledger).parts[:-1]) if part in kinds), "Note")
        if text.startswith("---\n"):
            text = "---\ntype: " + typ + "\n" + text[4:]
        else:
            title = next((l[2:].strip() for l in text.splitlines() if l.startswith("# ")), p.stem)
            text = f"---\ntype: {typ}\ntitle: {json.dumps(title[:120], ensure_ascii=False)}\n---\n\n" + text
        p.write_text(text); n += 1
    return n


def _persist_run(cfg: Config, report: DreamReport, started: float) -> None:
    import json, time
    if not (report.observations_processed or report.new or report.merged or report.contradictions or report.superseded
            or report.stale or report.revived or report.recurated):
        return   # a no-op dream is not an event worth a history entry
    from datetime import datetime, timezone
    d = cfg.paths.state / "dreams"
    d.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    rec = report.to_dict()
    rec.update({"at": ts, "duration_ms": int((time.time() - started) * 1000), "memories_total": len(Ledger(cfg.paths).load())})
    (d / f"{ts}.json").write_text(json.dumps(rec, ensure_ascii=False, indent=1))


def _llm_curate(prov, cfg: Config, pending: List[Dict], mems: Dict[str, Memory], verbose: bool, batch: int = 40) -> Tuple[List[Dict], int]:
    """Batch the pending observations through the model. Returns (kept observations with rewritten fields, dropped count).
    Anything the model does not answer for is kept unchanged - the model can only improve, never lose, data."""
    from .providers import CURATE_SCHEMA, CURATE_SYSTEM
    existing_lanes = sorted({m.lane for m in mems.values() if m.lane and m.lane not in ("general",)})
    atlas_apps = []
    aj = cfg.paths.ledger / "atlas" / "atlas.json"
    if aj.exists():
        try:
            import json as _j
            atlas_apps = [a.get("name") for a in _j.loads(aj.read_text()).get("apps", [])]
        except Exception:
            pass
    kept: List[Dict] = []
    dropped = 0
    for i in range(0, len(pending), batch):
        chunk = pending[i:i + batch]
        payload = {"existing_lanes": existing_lanes[:40], "repo_apps": atlas_apps[:20],
                   "candidates": [{"id": o["id"], "text": o.get("text", ""), "category_guess": o.get("category"), "files": o.get("files", [])[:4]} for o in chunk]}
        import json as _j
        res = prov.complete(CURATE_SYSTEM.format(today=today()), _j.dumps(payload, ensure_ascii=False), CURATE_SCHEMA)
        answers = {it.get("id"): it for it in (res or {}).get("items", []) if isinstance(it, dict)}
        for o in chunk:
            a = answers.get(o["id"])
            if a is None:
                kept.append(o)
                continue
            if not a.get("keep", True):
                dropped += 1
                continue
            text = " ".join(str(a.get("text") or o.get("text", "")).split())
            if 12 <= len(text) <= 400:
                o["text"] = text
            if a.get("category") in ("architecture", "decision", "convention", "constraint", "bug", "dependency", "workflow", "domain", "rejected"):
                o["category"] = a["category"]
            if a.get("lane"):
                o["lane"] = re.sub(r"[^a-z0-9/._\-]+", "-", str(a["lane"]).lower()).strip("-")[:40]
            if isinstance(a.get("importance"), (int, float)):
                o["score"] = max(float(o.get("score", 0.5)), min(1.0, float(a["importance"])))
            if isinstance(a.get("question"), str) and 8 <= len(a["question"]) <= 200:
                o["eval_q"] = " ".join(a["question"].split())
            o["curated"] = True
            kept.append(o)
        if verbose:
            print(f"  llm curated {min(i + batch, len(pending))}/{len(pending)}")
    return kept, dropped


def _evidence_excerpt(root, m: Memory, limit: int = 1400) -> str:
    """Lines of the evidence files around the identifiers the fact names (or the head of the file)."""
    idents = [n for a, b in _IDENT.findall(m.text) for n in [(a or b).strip()] if len(n) >= 5]
    out: List[str] = []
    for f in m.files[:2]:
        p = root / f
        if not p.is_file():
            out.append(f"[{f}: missing in this checkout]")
            continue
        try:
            lines = p.read_text(errors="ignore").splitlines()
        except Exception:
            continue
        hits = [i for i, l in enumerate(lines) if any(n in l for n in idents)] if idents else []
        picked: List[int] = []
        for i in hits[:4]:
            picked += [j for j in range(max(0, i - 2), min(len(lines), i + 3)) if j not in picked]
        if not picked:
            picked = list(range(min(30, len(lines))))
        out.append(f"[{f}]\n" + "\n".join(f"{j+1}: {lines[j][:160]}" for j in sorted(picked)))
    text = "\n".join(out)
    return text[:limit]


def _llm_verify_stale(prov, cfg: Config, facts: List[Memory], t: str, verbose: bool, batch: int = 12) -> Tuple[int, int]:
    """Doubtful facts, with the current evidence in front of the model: still_true → active and verified today;
    outdated → retired with the reason; unclear → stays for a human. Returns (verified, retired)."""
    from .providers import VERIFY_SCHEMA, VERIFY_SYSTEM
    import json as _j
    root = cfg.paths.root
    verified = retired = 0
    for i in range(0, len(facts), batch):
        chunk = facts[i:i + batch]
        payload = {"today": t, "facts": [{"id": m.id, "text": m.text, "category": m.category, "doubt": (m.reason or "")[:200],
                                          "evidence": _evidence_excerpt(root, m)} for m in chunk]}
        res = prov.complete(VERIFY_SYSTEM.format(today=t), _j.dumps(payload, ensure_ascii=False), VERIFY_SCHEMA)
        answers = {it.get("id"): it for it in (res or {}).get("items", []) if isinstance(it, dict)}
        for m in chunk:
            a = answers.get(m.id)
            if not a:
                continue
            v = a.get("verdict")
            if v == "still_true":
                m.status, m.updated, m.last_verified = "active", t, t
                text = " ".join(str(a.get("text") or "").split())
                if 12 <= len(text) <= 400:
                    m.text = text
                m.meta["verified"] = f"llm:{t}"
                m.reason = f"Verified against the evidence on {t}" + (f": {str(a.get('reason'))[:160]}" if a.get("reason") else "")
                verified += 1
            elif v == "outdated":
                m.status, m.updated = "forgotten", t
                m.reason = f"Retired on {t} — outdated per the evidence: {str(a.get('reason') or '')[:200]}"
                retired += 1
        if verbose:
            print(f"  verified {min(i + batch, len(facts))}/{len(facts)} doubtful facts")
    return verified, retired


def _llm_recurate(prov, cfg: Config, facts: List[Memory], mems: Dict[str, Memory], verbose: bool, batch: int = 40) -> Tuple[int, int]:
    """Run existing facts through the same curation. Drops become `forgotten` (reversible), never deletions."""
    from .providers import CURATE_SCHEMA, CURATE_SYSTEM
    import json as _j
    existing_lanes = sorted({m.lane for m in mems.values() if m.lane and m.lane != "general"})
    t = today()
    done = dropped = 0
    for i in range(0, len(facts), batch):
        chunk = facts[i:i + batch]
        payload = {"existing_lanes": existing_lanes[:40],
                   "candidates": [{"id": m.id, "text": m.text, "category_guess": m.category, "files": m.files[:4]} for m in chunk]}
        res = prov.complete(CURATE_SYSTEM.format(today=t), _j.dumps(payload, ensure_ascii=False), CURATE_SCHEMA)
        answers = {it.get("id"): it for it in (res or {}).get("items", []) if isinstance(it, dict)}
        for m in chunk:
            a = answers.get(m.id)
            if a is None:
                continue
            m.meta["curated"] = f"llm:{t}"
            done += 1
            if not a.get("keep", True):
                m.status, m.updated = "forgotten", t
                m.reason = "Retired by LLM curation on " + t + (f": {a.get('why_dropped')}" if a.get("why_dropped") else "")
                dropped += 1
                continue
            text = " ".join(str(a.get("text") or m.text).split())
            if 12 <= len(text) <= 400:
                m.text = text
            if a.get("category") in ("architecture", "decision", "convention", "constraint", "bug", "dependency", "workflow", "domain", "rejected"):
                m.category = a["category"]
            if a.get("lane"):
                m.lane = re.sub(r"[^a-z0-9/._\-]+", "-", str(a["lane"]).lower()).strip("-")[:40]
            if isinstance(a.get("importance"), (int, float)):
                m.importance = max(0.1, min(1.0, float(a["importance"])))
            m.source = "llm" if m.source == "observed" else m.source
        if verbose:
            print(f"  llm re-curated {min(i + batch, len(facts))}/{len(facts)}")
    return done, dropped


def _auto_tags(m: Memory) -> Set[str]:
    tags = {m.category}
    for f in m.files:
        parts = [p for p in re.split(r"[/\\]", f) if p and p not in ("src", "app", "lib", "main", "test", "tests")]
        if len(parts) >= 2:
            tags.add(re.sub(r"[^a-z0-9\-]", "", parts[-2].lower()))
    for w in re.findall(r"\b(Redis|Postgres(?:QL)?|Kafka|Snowflake|ClickHouse|Mongo\w*|Docker|Kubernetes|Stripe|GraphQL|gRPC|Authentik|Celery|Spark|Airflow|Kestra|React|Django|FastAPI|Kotlin|Ktor|Gradle)\b", m.text):
        tags.add(w.lower())
    return {t for t in tags if t}


def _link_related(mems: Dict[str, Memory]) -> None:
    items = list(mems.values())
    for m in items:
        rel = []
        for o in items:
            if o.id == m.id:
                continue
            shared_files = set(m.files) & set(o.files)
            shared_tags = (set(m.tags) & set(o.tags)) - {m.category}
            if shared_files or len(shared_tags) >= 1:
                rel.append(o.id)
        m.related = rel[:5]


def _llm_refine(prov, mems: Dict[str, Memory], report: DreamReport, t: str, batch: int = 30) -> None:
    """Merge / contradiction pass over this run's new facts, in batches small enough for one model call each;
    each batch sees only the existing facts from its own lanes (most important first)."""
    new_ids = {m.id for m in report.new}
    contra = [{"older": a, "newer": b, "older_text": mems[a].text, "newer_text": mems[b].text} for a, b in report.contradictions if a in mems and b in mems]
    for i in range(0, max(len(report.new), 1), batch):
        chunk = report.new[i:i + batch]
        lanes = {m.lane for m in chunk if m.lane}
        existing = sorted((m for m in mems.values() if m.id not in new_ids and m.status == "active" and (not lanes or m.lane in lanes)),
                          key=lambda m: -m.importance)[:80]
        payload = {"candidates": [{"id": m.id, "text": m.text, "category": m.category, "files": m.files} for m in chunk],
                   "existing": [{"id": m.id, "text": m.text, "category": m.category, "status": m.status} for m in existing],
                   "contradictions": contra if i == 0 else []}
        if not payload["candidates"] and not payload["contradictions"]:
            return
        out = prov.consolidate(payload, t)
        if out:
            _apply_refinement(out, mems, t)


def _apply_refinement(out: Dict, mems: Dict[str, Memory], t: str) -> None:
    # validated merge: only touch ids we know; only shorten/clarify texts; never invent evidence
    for item in out.get("memories", []):
        ids = [i for i in item.get("merge_of", []) if i in mems]
        if not ids:
            continue
        keep = mems[ids[0]]
        text = " ".join(str(item.get("text", "")).split())
        if 12 <= len(text) <= 400:
            keep.text = text
        if item.get("category") in ("architecture", "decision", "convention", "constraint", "bug", "dependency", "workflow", "domain", "rejected", "finding"):
            keep.category = item["category"]
        keep.importance = max(0.1, min(1.0, float(item.get("importance", keep.importance))))
        keep.source = "llm" if keep.source == "observed" else keep.source
        for dup in ids[1:]:
            d = mems.get(dup)
            if not d or d.source == "explicit":
                continue
            keep.evidence_count += d.evidence_count
            keep.files = list(dict.fromkeys(keep.files + d.files))[:8]
            d.status, d.superseded_by, d.updated = "superseded", keep.id, t
            d.reason = f"Merged into [[{keep.id}]] during dream on {t}"
    for c in out.get("contradictions", []):
        a, b = mems.get(c.get("older")), mems.get(c.get("newer"))
        if not a or not b:
            continue
        reason = str(c.get("reason", ""))[:300]
        if c.get("verdict") == "newer_supersedes" and a.source != "explicit":
            a.status, a.superseded_by, a.updated, a.reason = "superseded", b.id, t, f"Superseded on {t}: {reason}"
            b.supersedes, b.status = a.id, "active"
            b.contradicts = [x for x in b.contradicts if x != a.id]
        elif c.get("verdict") == "older_stands" and b.source != "explicit":
            b.status, b.superseded_by, b.updated, b.reason = "superseded", a.id, t, f"Rejected on {t}: {reason}"
            a.status = "active"
            a.contradicts = [x for x in a.contradicts if x != b.id]
        elif c.get("verdict") == "both_valid":
            for m, other in ((a, b), (b, a)):
                m.status = "active"
                m.contradicts = [x for x in m.contradicts if x != other.id]
                m.reason = f"Reviewed {t}: both valid — {reason}"
