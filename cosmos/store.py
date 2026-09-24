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

    def to_markdown(self) -> str:
        okf = self.okf_frontmatter(self.meta_stale_days if hasattr(self, "meta_stale_days") else 180)
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
        for line in body.splitlines():
            if line.startswith("- ") and not line.startswith(("- Observed", "- Evidence file", "- Supersedes", "- Superseded", "- Contradicts", "- [[")):
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


class Ledger:
    """Directory of memory notes: ledger/<category>/<id>-<slug>.md"""

    def __init__(self, paths: Paths):
        self.paths = paths
        self.dir = paths.ledger

    def _path_for(self, mem: Memory) -> Path:
        return self.dir / mem.category / f"{mem.id}-{slugify(mem.text)}.md"

    def load(self) -> Dict[str, Memory]:
        out: Dict[str, Memory] = {}
        if not self.dir.exists():
            return out
        for p in sorted(self.dir.rglob("mem_*.md")):
            try:
                mem = Memory.from_markdown(p.read_text())
            except Exception:
                mem = None
            if mem:
                out[mem.id] = mem
        return out

    def save(self, mem: Memory) -> Path:
        # validity window follows the lifecycle: closed when a fact stops being true, reopened if it comes back
        if mem.status in ("superseded", "forgotten") and not mem.valid_to:
            mem.valid_to = today()
        elif mem.status == "active" and mem.valid_to:
            mem.valid_to = ""
        if not mem.valid_from:
            mem.valid_from = mem.created
        # remove old file if slug/category changed
        for old in self.dir.rglob(f"{mem.id}-*.md"):
            if old != self._path_for(mem):
                old.unlink()
        p = self._path_for(mem)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(mem.to_markdown())
        return p

    def save_all(self, mems: Iterable[Memory]) -> None:
        for m in mems:
            self.save(m)

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
