"""The dream cycle: observations + existing ledger -> deduplicated, contradiction-checked, time-aware ledger.

Deterministic by default. An LLM provider, when configured and reachable, refines the result; its
output is validated and merged - never trusted blindly.
"""
from __future__ import annotations

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
    fallback_windows: int = 0
    flares_closed: int = 0

    def to_dict(self) -> Dict:
        return {"new": [{"id": m.id, "text": m.text, "category": m.category} for m in self.new],
                "merged": [{"text": t, "into": i} for t, i in self.merged],
                "contradictions": [{"older": a, "newer": b} for a, b in self.contradictions],
                "superseded": [{"old": a, "by": b} for a, b in self.superseded],
                "stale": list(self.stale), "revived": list(self.revived), "llm_used": self.llm_used,
                "observations_processed": self.observations_processed, "dropped": self.dropped, "recurated": self.recurated, "recurated_dropped": self.recurated_dropped, "journal_entries": self.journal_entries, "windows_read": self.windows_read, "turns_read": self.turns_read, "windows_waiting": self.windows_waiting, "auto_memory_notes": self.auto_memory_notes, "fallback_windows": self.fallback_windows, "llm_available": self.llm_available, "summary": self.summary()}

    def summary(self) -> str:
        return (f"{self.observations_processed} observations → {len(self.new)} new, {len(self.merged)} merged, "
                f"{len(self.contradictions)} contradictions, {len(self.superseded)} superseded, {len(self.stale)} stale"
                + (f" · LLM curated, {self.dropped} dropped as noise" if self.llm_used and self.observations_processed else "")
                + (f" · re-curated {self.recurated} existing facts, {self.recurated_dropped} retired" if self.recurated else "")
                + (f" · {self.journal_entries} journal entries written" if self.journal_entries else "")
                + (f" · model read {self.turns_read} turns" if self.turns_read else "")
                + (f" · {self.auto_memory_notes} auto memory notes offered" if self.auto_memory_notes else "")
                + (f" · {self.windows_waiting} session ranges still waiting for a model" if self.windows_waiting else "")
                + (f" · {self.fallback_windows} ranges read heuristically (no model for days)" if self.fallback_windows else "")
                + (f" · {self.flares_closed} flares marked fixed by commit messages" if self.flares_closed else "")
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


def _files_exist(root, files: List[str]) -> Optional[bool]:
    if not files:
        return None
    return any((root / f).exists() for f in files)


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
    journals = [o for o in pending if o.get("kind") == "journal"]
    report.journal_entries = _journal.persist(cfg, journals, mems)
    report.flares_closed = _flares_from_commits(cfg, journals, mems)
    pending = [o for o in pending if o.get("kind") != "journal"] + [dict(o, text="Work done: " + o["text"]) for o in journals if o.get("commits")]
    state.mark_dreamed(o["id"] for o in journals)

    # ---- 1b. LLM curation: the model decides what is worth keeping, rewrites it, names category + lane.
    want_llm = cfg.get("dream.llm", "auto") if use_llm is None else use_llm
    prov = get_provider(cfg.get("llm", {}) or {}) if want_llm else None
    report.llm_available = prov is not None
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
        if o.get("lane"):
            mem.lane = str(o["lane"])
        if o.get("curated"):
            mem.meta["curated"] = f"llm:{t}"
            mem.source = "llm"
        mems[mem.id] = mem
        index.append((otoks, mem))
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
    for m in mems.values():
        if m.status != "active":
            continue
        limit = int(thresholds.get(m.category, thresholds.get("default", 180)))
        try:
            age = (date.fromisoformat(t) - date.fromisoformat(m.last_verified)).days
        except Exception:
            age = 0
        if _files_exist(root, m.files) is False:
            m.status, m.updated = "stale-candidate", t
            m.reason = f"Stale candidate since {t}: none of the evidence files exist anymore"
            report.stale.append(m.id)
        elif age > limit and m.source != "explicit" and m.category != "finding":
            m.status, m.updated = "stale-candidate", t
            m.reason = f"Stale candidate since {t}: not re-observed for {age} days (limit {limit}d for {m.category})"
            report.stale.append(m.id)

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
    from .lanes import assign_lanes
    assign_lanes(mems, cfg, only_missing=bool(report.llm_used))
    _link_related(mems)
    ledger.save_all(mems.values())
    state.mark_dreamed(seen_ids)
    state.save()
    _persist_run(cfg, report, started)
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
            o["curated"] = True
            kept.append(o)
        if verbose:
            print(f"  llm curated {min(i + batch, len(pending))}/{len(pending)}")
    return kept, dropped


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
