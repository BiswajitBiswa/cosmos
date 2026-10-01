"""Ledger storage: one markdown note per memory (Obsidian-compatible frontmatter) + observation JSONL."""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from .config import Paths

STATUSES = ["active", "stale-candidate", "contradicted", "superseded", "forgotten"]


def today() -> str:
    return date.today().isoformat()


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def lane_file(lane: str) -> str:
    """The page name for a lane under ledger/lanes/ - always a plain file name, never a path (a sibling-repo lane
    such as ../web-app becomes repo-web-app.md)."""
    lane = str(lane or "general")
    prefix = "repo-" if lane.startswith("../") else ""
    return prefix + (re.sub(r"[^a-z0-9._-]+", "-", lane.lower()).strip("-.") or "general") + ".md"


def slugify(text: str, n: int = 48) -> str:
    s = re.sub(r"[`*_\"']", "", text.lower())
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:n].rstrip("-") or "memory"


def make_id(text: str) -> str:
    return "mem_" + hashlib.sha1(text.strip().lower().encode()).hexdigest()[:8]


@dataclass
class Memory:
    id: str
    text: str
    category: str
    status: str = "active"
    confidence: float = 0.6
    importance: float = 0.6
    source: str = "observed"           # observed | explicit | llm
    created: str = field(default_factory=today)
    updated: str = field(default_factory=today)
    last_verified: str = field(default_factory=today)
    evidence_count: int = 1
    files: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    authors: List[str] = field(default_factory=list)
    sessions: List[str] = field(default_factory=list)
    supersedes: Optional[str] = None
    superseded_by: Optional[str] = None
    contradicts: List[str] = field(default_factory=list)
    reason: str = ""
    related: List[str] = field(default_factory=list)
    lane: str = ""                                               # feature / module this fact belongs to (see lanes.py)
    meta: Dict[str, str] = field(default_factory=dict)          # small typed extras (e.g. audit severity)
    valid_from: str = ""                                         # when this became true for the team (defaults to created)
    valid_to: str = ""                                           # when it stopped being true (set on supersede / retire)
    details: List[List[str]] = field(default_factory=list)      # [[label, text], ...] rendered as sections

    # ----- markdown (Obsidian-compatible, OKF v0.2-conformant) -----
    OKF_STATUS = {"active": "stable", "stale-candidate": "draft", "contradicted": "draft", "superseded": "deprecated", "forgotten": "deprecated"}

    def okf_frontmatter(self, stale_days: int = 180) -> Dict:
        """The Open Knowledge Format view of this note: type, title, description, provenance, trust and freshness signals.
        Any OKF consumer (Google's Knowledge Catalog, okf-agent-memory, a static viewer) can read the ledger as a bundle."""
        from datetime import datetime, timedelta
        by = f"human:{self.authors[0]}" if self.source == "explicit" and self.authors else f"cosmos/{self.source}"
        verified = []
        v = self.meta.get("verified", "")
        if v.startswith("llm:"):
            verified.append({"by": "cosmos-dream/model", "at": v[4:] + "T00:00:00Z"})
        if self.meta.get("reviewed_by"):
            verified.append({"by": f"human:{self.meta['reviewed_by']}", "at": (self.meta.get("reviewed_at") or self.updated) + "T00:00:00Z"})
        try:
            stale_after = (datetime.fromisoformat(self.last_verified) + timedelta(days=stale_days)).strftime("%Y-%m-%dT00:00:00Z")
        except Exception:
            stale_after = ""
        fm = {"type": self.category.replace("-", " ").title(), "title": self.text[:120], "description": self.text,
              "status": self.OKF_STATUS.get(self.status, "stable"),
              "generated": {"by": by, "at": self.created + "T00:00:00Z"},
              "sources": [{"resource": f, "title": f.rsplit("/", 1)[-1]} for f in self.files[:8]]}
        if verified:
            fm["verified"] = verified
        if stale_after and self.status == "active":
            fm["stale_after"] = stale_after
        return fm

    def link_targets(self) -> List[str]:
        """Ids this note relates to, in link order: supersedes, superseded_by, contradicts, related."""
        out: List[str] = []
        for i in [self.supersedes, self.superseded_by, *self.contradicts, *self.related]:
            if i and i not in out and i != self.id:
                out.append(i)
        return out

    def to_markdown(self, paths: Optional[Dict[str, str]] = None) -> str:
        """`paths` maps memory ids to bundle-relative note paths, so relationships become real OKF links."""
        paths = paths or {}
        okf = self.okf_frontmatter(self.meta_stale_days if hasattr(self, "meta_stale_days") else 180)
        links = ([f"/lanes/{lane_file(self.lane)}"] if self.lane and self.lane != "general" else []) + [paths[i] for i in self.link_targets() if i in paths]
        if links:
            okf["links"] = links
        fm = {**okf,
            "id": self.id, "aliases": [self.id], "category": self.category, "lane": self.lane, "cosmos_status": self.status,
            "confidence": round(self.confidence, 2), "importance": round(self.importance, 2),
            "source": self.source, "created": self.created, "updated": self.updated,
            "last_verified": self.last_verified, "evidence_count": self.evidence_count,
            "files": self.files, "tags": self.tags, "authors": self.authors, "sessions": self.sessions,
            "supersedes": self.supersedes, "superseded_by": self.superseded_by, "contradicts": self.contradicts,
            "valid_from": self.valid_from or self.created, "valid_to": self.valid_to or None,
        }
        for k, v in sorted(self.meta.items()):
            fm[f"meta_{k}"] = v
        lines = ["---"]
        for k, v in fm.items():
            if v is None or v == [] or v == "":
                continue
            lines.append(f"{k}: {json.dumps(v)}" if isinstance(v, (list, str, dict)) else f"{k}: {v}")
        lines.append("---")
        lines.append("")
        lines.append(f"# {self.text}")
        lines.append("")
        lines.append(f"**Category:** {self.category} · **Status:** {self.status} · **Confidence:** {int(self.confidence*100)}%")
        lines.append("")
        if self.details:
            lines.append("## Details")
            for label, text in self.details:
                lines.append(f"**{label}** — {text}")
                lines.append("")
        lines.append("## Why we believe this")
        lines.append(f"- Observed {self.evidence_count}× (first {self.created}, last {self.updated}); source: {self.source}")
        for f in self.files:
            lines.append(f"- Evidence file: `{f}`")
        if self.reason:
            lines.append(f"- {self.reason}")
        if self.supersedes:
            lines.append(f"- Supersedes [[{self.supersedes}]]")
        if self.superseded_by:
            lines.append(f"- Superseded by [[{self.superseded_by}]]")
        for c in self.contradicts:
            lines.append(f"- Contradicts [[{c}]]")
        if self.related:
            lines.append("")
            lines.append("## Related")
            lines.extend(f"- [[{r}]]" for r in self.related)
        rel = []
        if self.lane and self.lane != "general":
            rel.append(f"- lane: [{self.lane}](/lanes/{lane_file(self.lane)})")
        for label, ids in (("supersedes", [self.supersedes] if self.supersedes else []), ("superseded by", [self.superseded_by] if self.superseded_by else []),
                           ("contradicts", self.contradicts), ("related", self.related)):
            for i in ids:
                if i in paths:
                    rel.append(f"- {label}: [{i}]({paths[i]})")
        if rel:
            lines.append("")
            lines.append("## Links")
            lines.extend(rel)
        if self.tags:
            lines.append("")
            lines.append(" ".join(f"#{t}" for t in self.tags))
        return "\n".join(lines) + "\n"

    @staticmethod
    def from_markdown(md: str) -> Optional["Memory"]:
        m = re.match(r"^---\n(.*?)\n---\n(.*)$", md, re.S)
        if not m:
            return None
        fm: Dict = {}
        for line in m.group(1).splitlines():
            if ":" not in line:
                continue
            k, v = line.split(":", 1)
            v = v.strip()
            try:
                fm[k.strip()] = json.loads(v)
            except Exception:
                fm[k.strip()] = v
        body = m.group(2)
        title = re.search(r"^# (.+)$", body, re.M)
        reason = ""
        why = re.search(r"^## Why we believe this\n(.*?)(?=^## |^#\w|\Z)", body, re.M | re.S)
        for line in (why.group(1) if why else "").splitlines():
            if line.startswith("- ") and not line.startswith(("- Observed", "- Evidence file", "- Supersedes", "- Superseded", "- Contradicts", "- [[")) \
                    and not re.match(r"- (lane|supersedes|superseded by|contradicts|related): \[", line):   # a link a save once copied here
                reason = line[2:].strip()
                break
        if not title or "id" not in fm:
            return None
        mem = Memory(
            id=str(fm["id"]), text=title.group(1).strip(), category=str(fm.get("category", "domain")),
            status=str(fm.get("cosmos_status") or (fm.get("status") if fm.get("status") in ("active", "stale-candidate", "contradicted", "superseded", "forgotten") else "active")),
            confidence=float(fm.get("confidence", 0.6)),
            importance=float(fm.get("importance", 0.6)), source=str(fm.get("source", "observed")),
            created=str(fm.get("created", today())), updated=str(fm.get("updated", today())),
            last_verified=str(fm.get("last_verified", today())), evidence_count=int(fm.get("evidence_count", 1)),
            files=list(fm.get("files", []) or []), tags=list(fm.get("tags", []) or []),
            authors=list(fm.get("authors", []) or []), sessions=list(fm.get("sessions", []) or []),
            supersedes=fm.get("supersedes"), superseded_by=fm.get("superseded_by"),
            contradicts=list(fm.get("contradicts", []) or []), reason=reason,
            meta={k[5:]: str(v) for k, v in fm.items() if k.startswith("meta_")}, lane=str(fm.get("lane", "") or ""),
            valid_from=str(fm.get("valid_from") or ""), valid_to=str(fm.get("valid_to") or ""),
        )
        det = re.search(r"^## Details\n(.*?)(?=^## )", body, re.M | re.S)
        if det:
            mem.details = [[m.group(1), m.group(2).strip()] for m in re.finditer(r"^\*\*(.+?)\*\* — (.+?)(?=\n\*\*|\Z)", det.group(1), re.M | re.S)]
        mem.related = re.findall(r"^- \[\[(mem_[0-9a-f]+)\]\]$", body, re.M)
        return mem


def _ledger_cache(ledger_dir: Path) -> Optional[Path]:
    """Machine-local, never in the repository: ~/.cache/cosmos/<repository>-<hash>.ledger. COSMOS_LEDGER_CACHE=0 turns it off."""
    import os
    if os.environ.get("COSMOS_LEDGER_CACHE") == "0":
        return None
    base = Path(os.environ.get("COSMOS_CACHE_DIR") or Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache") / "cosmos")
    key = hashlib.sha1(str(ledger_dir.resolve()).encode()).hexdigest()[:12]
    return base / f"{ledger_dir.parent.parent.name}-{key}.ledger"


def _read_cache(path: Optional[Path]) -> Dict[str, tuple]:
    import pickle
    if path is None or not path.exists():
        return {}
    try:
        with path.open("rb") as fh:
            data = pickle.load(fh)                    # written by this machine's cosmos only (see _ledger_cache)
        return data if isinstance(data, dict) and data.get("_v") == CACHE_VERSION and data.pop("_v") else {}
    except Exception:
        return {}


def _write_cache(path: Path, entries: Dict[str, tuple]) -> None:
    import os
    import pickle
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(f".{os.getpid()}.tmp")
        with tmp.open("wb") as fh:
            pickle.dump({**entries, "_v": CACHE_VERSION}, fh, protocol=pickle.HIGHEST_PROTOCOL)
        tmp.replace(path)
    except OSError:
        pass                                           # a cache that cannot be written only costs time


CACHE_VERSION = 1


def _remember_base(mem: "Memory", text: str) -> None:
    """What the note was when this process read or wrote it: the base of a three-way save (Ledger.save)."""
    mem._base = asdict(mem)
    mem._base_text = text


def _merge_into(mem: "Memory", base: Dict, mine: Dict, disk: Dict) -> None:
    """Another process saved the note after this one read it. Keep what this process changed (field by field, and
    key by key inside meta) and take everything else from the file, so a dream that ran for minutes cannot put back
    a flare's older lifecycle state, and a status set meanwhile survives the dream's rewrite."""
    for k, now in disk.items():
        if k == "meta":
            merged = dict(now)
            for mk in set(base.get("meta", {})) | set(mine.get("meta", {})):
                if mine["meta"].get(mk) != base["meta"].get(mk):
                    if mk in mine["meta"]:
                        merged[mk] = mine["meta"][mk]
                    else:
                        merged.pop(mk, None)
            setattr(mem, k, merged)
        elif mine.get(k) == base.get(k):
            setattr(mem, k, now)


class Ledger:
    """Directory of memory notes: ledger/<category>/<id>-<slug>.md"""

    def __init__(self, paths: Paths):
        self.paths = paths
        self.dir = paths.ledger

    def _path_for(self, mem: Memory) -> Path:
        return self.dir / mem.category / f"{mem.id}-{slugify(mem.text)}.md"

    def load(self) -> Dict[str, Memory]:
        """Every note, parsed. Parsing thousands of markdown notes is most of a hook's time (702 ms of ~750 for 2,925
        notes, measured 2026-10-01), so the parsed notes are kept per machine and only a note whose file changed
        (modification time or size) is read again."""
        out: Dict[str, Memory] = {}
        if not self.dir.exists():
            return out
        cache_file = _ledger_cache(self.dir)
        cached = _read_cache(cache_file)
        fresh: Dict[str, tuple] = {}
        for p in sorted(self.dir.rglob("mem_*.md")):
            try:
                st = p.stat()
            except OSError:
                continue
            key, hit = (st.st_mtime_ns, st.st_size), cached.get(str(p))
            if hit and hit[0] == key:
                mem = hit[1]
            else:
                try:
                    text = p.read_text()
                    mem = Memory.from_markdown(text)
                except Exception:
                    mem = None
                if mem:
                    _remember_base(mem, text)
            if mem:
                fresh[str(p)] = (key, mem)
                out[mem.id] = mem
        changed = fresh.keys() != cached.keys() or any(fresh[k][0] != cached[k][0] for k in fresh if k in cached)
        if cache_file and changed:
            _write_cache(cache_file, fresh)
        return out                                     # unpickled for this call: no other caller holds these objects

    def paths_by_id(self, mems: Optional[Iterable[Memory]] = None) -> Dict[str, str]:
        """Bundle-relative path of every note, for OKF links (e.g. /constraint/mem_ab12-slug.md)."""
        if mems is not None:
            return {m.id: "/" + str(self._path_for(m).relative_to(self.dir)) for m in mems}
        out: Dict[str, str] = {}
        for p in self.dir.rglob("mem_*.md"):
            out[p.name.split("-", 1)[0]] = "/" + str(p.relative_to(self.dir))
        return out

    def save(self, mem: Memory, paths: Optional[Dict[str, str]] = None) -> Path:
        # validity window follows the lifecycle: closed when a fact stops being true, reopened if it comes back
        if mem.status in ("superseded", "forgotten") and not mem.valid_to:
            mem.valid_to = today()
        elif mem.status == "active" and mem.valid_to:
            mem.valid_to = ""
        if not mem.valid_from:
            mem.valid_from = mem.created
        base = getattr(mem, "_base", None)
        if base is not None:                         # loaded earlier by this process: someone may have saved it since
            on_disk = next(iter(sorted(self.dir.rglob(f"{mem.id}-*.md"))), None)
            disk_text = on_disk.read_text() if on_disk else None
            if disk_text is not None and disk_text != getattr(mem, "_base_text", None):
                disk = Memory.from_markdown(disk_text)
                if disk is not None:
                    mine = asdict(mem)
                    if mine == base:
                        return on_disk               # nothing changed here, and the file is newer: it stays
                    _merge_into(mem, base, mine, asdict(disk))
        # remove old file if slug/category changed
        for old in self.dir.rglob(f"{mem.id}-*.md"):
            if old != self._path_for(mem):
                old.unlink()
        p = self._path_for(mem)
        p.parent.mkdir(parents=True, exist_ok=True)
        text = mem.to_markdown(paths if paths is not None else (self.paths_by_id() if mem.link_targets() else {}))
        p.write_text(text)
        _remember_base(mem, text)
        return p

    def save_all(self, mems: Iterable[Memory]) -> None:
        mems = list(mems)
        paths = self.paths_by_id(mems)
        for m in mems:
            self.save(m, paths)

    def delete(self, mem_id: str) -> bool:
        ok = False
        for old in self.dir.rglob(f"{mem_id}-*.md"):
            old.unlink()
            ok = True
        return ok


class Observations:
    """Append-only, sanitized, day-partitioned JSONL. Small enough to commit."""

    def __init__(self, paths: Paths):
        self.dir = paths.observations

    def append(self, records: List[Dict]) -> Path:
        self.dir.mkdir(parents=True, exist_ok=True)
        p = self.dir / f"{today()}.jsonl"
        with p.open("a") as fh:
            for r in records:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
        return p

    def iter_all(self) -> Iterable[Dict]:
        if not self.dir.exists():
            return
        for p in sorted(self.dir.glob("*.jsonl")):
            for line in p.read_text().splitlines():
                try:
                    yield json.loads(line)
                except Exception:
                    continue

    def count(self) -> int:
        return sum(1 for _ in self.iter_all())


class State:
    """Machine-local state (gitignored): per-session transcript offsets, processed observation ids."""

    def __init__(self, paths: Paths):
        self.path = paths.state / "state.json"
        self.data: Dict = {"sessions": {}, "dreamed": {}}
        if self.path.exists():
            try:
                self.data = json.loads(self.path.read_text())
            except Exception:
                pass

    def offset(self, session_id: str) -> int:
        return int(self.data.get("sessions", {}).get(session_id, {}).get("offset", 0))

    def set_offset(self, session_id: str, offset: int) -> None:
        self.data.setdefault("sessions", {})[session_id] = {"offset": offset, "updated": now_iso()}

    def is_dreamed(self, obs_id: str) -> bool:
        return obs_id in self.data.get("dreamed", {})

    def mark_dreamed(self, obs_ids: Iterable[str]) -> None:
        d = self.data.setdefault("dreamed", {})
        for o in obs_ids:
            d[o] = today()

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.data, indent=1))
