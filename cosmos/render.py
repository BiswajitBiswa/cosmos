"""Write the managed blocks in CLAUDE.md / AGENTS.md and the ledger index (Obsidian MOC)."""
from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional

from .config import Config
from .store import Memory, slugify
from .retrieve import top

START = "<!-- cosmos:start -->"
END = "<!-- cosmos:end -->"


def managed_block(mems: Dict[str, Memory], k: int, cfg: Optional[Config] = None) -> str:
    lines = [START, "## Cosmos — how this team works with AI", "",
             "1. **Charter** `.cosmos/charter.md` — the team's coding style, testing and review rules. Follow it over any personal preference.",
             "2. **Ledger** `.cosmos/ledger/` — one note per fact with evidence, grouped by lane (`_index.md`). Consult before changing architecture, conventions or workflows.",
             "3. **Atlas** `.cosmos/ledger/atlas/` — architecture diagrams generated from the repo. Read `containers.md` before structural changes.",
             "4. **Gate** — before you stop: run the tests for files you touched, cite `file:line` for each change, address open findings on those files, self-review against the Charter.",
             "Explicit rules outrank inferred facts.", ""]
    if cfg is not None:
        from .charter import rules
        rs = rules(mems)
        if rs:
            lines.append("Explicit team rules:")
            lines += [f"- [{m.category}] {m.text}" for m in rs[:10]]
            lines.append("")
    ts = [m for m in top(mems, k) if m.source != "explicit"]
    if ts:
        lines.append("Key facts:")
        for m in ts:
            lines.append(f"- **{m.category}**" + (f" · {m.lane}" if m.lane else "") + f": {m.text}")
        lines.append("")
    lines.append("`cosmos why <id>` explains a fact · `remember: …` adds a rule · `flare: …` files a flare · `cosmos horizon \"…\"` maps a feature before coding")
    lines.append(END)
    return "\n".join(lines)


def upsert_block(path: Path, block: str) -> bool:
    """Insert or replace the managed block. Returns True if file changed."""
    old = path.read_text() if path.exists() else ""
    if START in old and END in old:
        new = re.sub(re.escape(START) + r".*?" + re.escape(END), lambda _: block, old, flags=re.S)
    else:
        sep = "\n\n" if old and not old.endswith("\n\n") else ("" if old.endswith("\n\n") else "")
        new = (old.rstrip("\n") + "\n\n" if old.strip() else "") + block + "\n"
    if new != old:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(new)
        return True
    return False


def write_index(cfg: Config, mems: Dict[str, Memory]) -> Path:
    by_lane: Dict[str, Dict[str, List[Memory]]] = defaultdict(lambda: defaultdict(list))
    for m in mems.values():
        by_lane[m.lane or "general"][m.category].append(m)
    lines = ["---", "tags: [\"cosmos\", \"moc\"]", "---", "", "# Ledger index", "",
             f"{len(mems)} memories · {sum(1 for m in mems.values() if m.status=='active')} active · "
             f"{sum(1 for m in mems.values() if m.status=='contradicted')} contradicted · "
             f"{sum(1 for m in mems.values() if m.status=='stale-candidate')} stale candidates · {len(by_lane)} lanes", "",
             "Charter: [[charter]] · Atlas: [[inventory]] · [[containers]] · [[deployment]] · [[api]]", ""]
    for lane in sorted(by_lane):
        lines.append(f"## Lane · {lane}")
        for cat in sorted(by_lane[lane]):
            lines.append(f"### {cat.title()}")
            for m in sorted(by_lane[lane][cat], key=lambda x: (x.status != "active", -x.confidence)):
                badge = "" if m.status == "active" else f" `{m.status}`"
                lines.append(f"- [[{m.id}-{slugify(m.text)}|{m.text}]]{badge}")
        lines.append("")
    p = cfg.paths.ledger / "_index.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(lines))
    return p


def render_all(cfg: Config, mems: Dict[str, Memory]) -> List[str]:
    changed: List[str] = []
    write_index(cfg, mems)
    changed.append(str(cfg.paths.ledger / "_index.md"))
    k = int(cfg.get("retrieval.session_start_max", 10))
    block = managed_block(mems, k, cfg)
    targets = {"CLAUDE.md": cfg.get("render.claude_md", True), "AGENTS.md": cfg.get("render.agents_md", True)}
    for extra in cfg.get("render.targets", ["GEMINI.md"]) or []:
        targets[extra] = True
    for rel, on in targets.items():
        if not on:
            continue
        path = cfg.paths.root / rel
        b = block
        if rel.endswith(".mdc"):   # Cursor rule file wants frontmatter
            b = "---\ndescription: cosmos — team charter, memory and architecture\nalwaysApply: true\n---\n" + block if not path.exists() else block
        if upsert_block(path, b):
            changed.append(rel)
    return changed
