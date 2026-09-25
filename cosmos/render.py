"""Write the managed blocks in CLAUDE.md / AGENTS.md and the ledger index (Obsidian MOC)."""
from __future__ import annotations

import json

import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional

from .config import Config
from .store import Ledger, Memory, lane_file, slugify
from .retrieve import top

START = "<!-- cosmos:start -->"
END = "<!-- cosmos:end -->"


def managed_block(mems: Dict[str, Memory], k: int, cfg: Optional[Config] = None) -> str:
    lines = [START, "## Cosmos — how this team works with AI", "",
             "1. **Charter** `.cosmos/charter.md` — the team's coding style, testing and review rules. Follow it over any personal preference.",
             "2. **Ledger** `.cosmos/ledger/` — one note per fact with evidence, grouped by lane (`_index.md`). Consult before changing architecture, conventions or workflows.",
             "3. **Atlas** `.cosmos/ledger/atlas/` — architecture diagrams generated from the repo. Read `containers.md` before structural changes.",
             "4. **Gate** — before you stop: run the tests for files you touched, cite `file:line` for each change, address open flares on those files, self-review against the Charter, and record what the team learned (cosmos_remember kind=fact; cosmos_flare for bugs found - fixed or open - without asking).",
             "Explicit rules outrank inferred facts.", ""]
    branch = cfg is not None and (cfg.paths.cosmos / ".git").is_file()
    lines.append("The rules are in `.cosmos/charter.md` and the facts, by lane, in `.cosmos/ledger/_index.md`"
                 + (" (a git worktree of the `cosmos` branch). Never merge, rebase or cherry-pick the `cosmos` branch into another branch, "
                    "and leave it out when syncing a branch with the latest changes: it holds the team memory, not code."
                    if branch else ". `.cosmos/` is committed in this branch like code and travels with every branch made from it; cosmos "
                    "commits it by itself (never stage or revert its files, and keep them when resolving a merge).")
                 + " Claude Code receives the relevant ones through hooks; any other agent "
                 "reads those two files or calls `cosmos_recall` before changing code it did not write.")
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
    lines = ["---", "type: Index", "title: Ledger index", "okf_version: \"0.2\"", "tags: [\"cosmos\", \"moc\"]", "---", "", "# Ledger index", "",
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
    # OKF reserves index.md at the bundle root: a plain directory listing with descriptions, progressive disclosure
    root_lines = ["---", "okf_version: \"0.2\"", "---", "", f"# {cfg.paths.root.name} · team knowledge (cosmos)", "",
                  "- [Ledger index by lane](_index.md) — every fact, grouped by feature lane",
                  "- [Charter](../charter.md) — the team's working agreement",
                  "- [Atlas](atlas/) — architecture drawn from the repository",
                  "- [Lanes](lanes/) — one concept per feature: its facts, flares, horizon notes, services and people",
                  "- [Services](atlas/services/) — apps, services and stores from the Atlas, linked to lanes and facts",
                  "- [Journal](journal/) — what the team did, one line per agent turn; handoffs per branch",
                  "- [Horizon](horizon/) — features mapped before coding", ""]
    for cat in sorted({m.category for m in mems.values()}):
        n = sum(1 for m in mems.values() if m.category == cat and m.status == "active")
        root_lines.append(f"- [{cat}/]({cat}/) — {n} active {cat} note{'s' if n != 1 else ''}")
    (cfg.paths.ledger / "index.md").write_text("\n".join(root_lines) + "\n")
    return p


def _fm(d: Dict) -> str:
    import json as _j
    return "---\n" + "\n".join(f"{k}: {_j.dumps(v, ensure_ascii=False)}" for k, v in d.items() if v not in (None, "", [], {})) + "\n---\n"


def write_lane_pages(cfg: Config, mems: Dict[str, Memory]) -> int:
    """One OKF concept per lane: ledger/lanes/<lane>.md. The page is the hub of the graph for that feature — it links the
    facts, the open flares, the horizon notes, the services whose code it touches, and who has been active there.
    Nothing here is computed twice: it renders what lanes.lane_report and the ledger already know."""
    from .lanes import lane_report
    from .store import Observations
    ledger = Ledger(cfg.paths)
    paths = ledger.paths_by_id(mems.values())
    report = {r["lane"]: r for r in lane_report(cfg, mems, list(Observations(cfg.paths).iter_all()))}
    by_lane: Dict[str, List[Memory]] = defaultdict(list)
    for m in mems.values():
        by_lane[m.lane or "general"].append(m)
    # horizon notes and atlas apps, for cross-links
    horizons = []
    hdir = cfg.paths.ledger / "horizon"
    if hdir.exists():
        for p in sorted(hdir.glob("*.md")):
            txt = p.read_text(errors="ignore")[:800]
            import re as _re
            ln = _re.search(r"^lanes: (\[.*\])$", txt, _re.M)
            try:
                lanes = json.loads(ln.group(1).replace("'", '"')) if ln else []
            except Exception:
                lanes = []
            horizons.append((p.name, lanes))
    apps = []
    aj = cfg.paths.ledger / "atlas" / "atlas.json"
    if aj.exists():
        try:
            apps = [(a.get("name"), a.get("dir") or "") for a in json.loads(aj.read_text()).get("apps", []) if a.get("dir")]
        except Exception:
            apps = []
    d = cfg.paths.ledger / "lanes"
    d.mkdir(parents=True, exist_ok=True)
    written = 0
    index_lines = ["---", "type: Index", "title: Lanes", "---", "", "# Lanes", "", "Each lane is one feature or module, the way the team talks about the product. Every fact, flare, horizon note and service links back here.", ""]
    kept = {"index.md"}
    for lane in sorted(by_lane):
        ms = by_lane[lane]
        active = [m for m in ms if m.status == "active" and m.category != "finding"]
        flares = [m for m in ms if m.category == "finding" and m.meta.get("finding_status", "open") in ("open", "claimed", "pr_open", "needs_human", "regressed")]
        if not active and not flares:
            continue                                   # only forgotten or closed items: no page
        files = sorted({f for m in active for f in m.files})
        dirs = sorted({f.split("/")[0] for f in files if "/" in f})[:6]
        r = report.get(lane, {})
        people = [c["name"] for c in r.get("contributors", [])][:6]
        lane_apps = [(n, dd) for n, dd in apps if any(f.startswith(dd.rstrip("/") + "/") for f in files)]
        lane_h = [name for name, lanes in horizons if lane in lanes]
        fm = {"type": "Lane", "title": lane, "description": f"{len(active)} active fact{'s' if len(active) != 1 else ''}, {len(flares)} open flare{'s' if len(flares) != 1 else ''}, {len(people)} people active in the last 30 days",
              "status": "stable", "sources": [{"resource": f"/../../{dd}", "title": dd} for dd in dirs],
              "links": [paths[m.id] for m in active[:200] if m.id in paths] + [f"/atlas/services/{slugify(n)}.md" for n, _ in lane_apps] + [f"/horizon/{h}" for h in lane_h],
              "tags": ["lane", lane]}
        L = [_fm(fm), "", f"# Lane · {lane}", "", fm["description"] + ".", ""]
        if r.get("overlap"):
            L += [f"**Overlap:** {len(people)} people active here this month: {', '.join(people)}.", ""]
        if lane_apps:
            L += ["## Services and apps", ""] + [f"- [{n}](/atlas/services/{slugify(n)}.md) — `{dd}`" for n, dd in lane_apps] + [""]
        if flares:
            L += ["## Open flares", ""] + [f"- [{m.meta.get('audit_id', m.id)}]({paths.get(m.id, '')}) [{m.meta.get('severity', '')}] {m.text[:120]}" for m in flares] + [""]
        if lane_h:
            L += ["## Horizon", ""] + [f"- [{h[:-3]}](/horizon/{h})" for h in lane_h] + [""]
        if active:
            L += ["## Facts", ""]
            for cat in sorted({m.category for m in active}):
                L.append(f"### {cat.title()}")
                L += [f"- [{m.text[:140]}]({paths.get(m.id, '')})" for m in sorted((m for m in active if m.category == cat), key=lambda x: -x.importance)]
                L.append("")
        if people:
            L += ["## People", ""] + [f"- {p}" for p in people] + [""]
        (d / lane_file(lane)).write_text("\n".join(L))
        kept.add(lane_file(lane))
        index_lines.append(f"- [{lane}]({lane_file(lane)}) — {fm['description']}")
        written += 1
    (d / "index.md").write_text("\n".join(index_lines) + "\n")
    def lane_page(text: str) -> bool:
        head = text.split("\n---", 1)[0] if text.startswith("---\n") else ""
        return bool(re.search(r'^type: "?Lane"?$', head, re.M))
    for p in list(d.glob("*.md")) + list(d.parent.glob("*.md")):   # d.parent: pages an old unsafe lane name wrote one level up
        if (p.parent != d or p.name not in kept) and lane_page(p.read_text(errors="ignore")):
            p.unlink()                                 # the lane is gone (renamed, emptied, or was never a real lane)
    return written


def write_service_pages(cfg: Config, mems: Dict[str, Memory]) -> int:
    """One OKF concept per app, service and store the Atlas found: ledger/atlas/services/<name>.md, with `resource`
    pointing at the code or compose file and links to the lanes and facts that touch it."""
    aj = cfg.paths.ledger / "atlas" / "atlas.json"
    if not aj.exists():
        return 0
    try:
        inv = json.loads(aj.read_text())
    except Exception:
        return 0
    paths = Ledger(cfg.paths).paths_by_id(mems.values())
    d = cfg.paths.ledger / "atlas" / "services"
    d.mkdir(parents=True, exist_ok=True)
    n = 0
    idx = ["---", "type: Index", "title: Services", "---", "", "# Services, apps and stores", ""]
    for kind, items in (("App", inv.get("apps", [])), ("Service", inv.get("services", [])), ("Database", inv.get("stores", []))):
        for it in items:
            name = it.get("name") or it.get("dir")
            if not name:
                continue
            res = it.get("dir") or it.get("compose") or it.get("path") or ""
            facts = [m for m in mems.values() if m.status == "active" and res and any(f.startswith(res.rstrip("/") + "/") for f in m.files)] if kind == "App" else []
            lanes = sorted({m.lane for m in facts if m.lane and m.lane != "general"})
            fm = {"type": kind, "title": name, "description": (f"{it.get('language', '')} app in {res}" if kind == "App" else f"{kind.lower()} from {res}" + (f" · image {it.get('image')}" if it.get("image") else "")).strip(),
                  "resource": f"/../../{res}" if res else None, "status": "stable",
                  "links": [f"/lanes/{lane_file(l)}" for l in lanes] + [paths[m.id] for m in facts[:100] if m.id in paths], "tags": ["atlas", kind.lower()]}
            L = [_fm(fm), "", f"# {name}", "", fm["description"] or "", ""]
            if kind == "Service" and it.get("ports"):
                L += [f"Ports: {', '.join(str(p) for p in it.get('ports') or [])}", ""]
            if lanes:
                L += ["## Lanes", ""] + [f"- [{l}](/lanes/{lane_file(l)})" for l in lanes] + [""]
            if facts:
                L += ["## Facts about this code", ""] + [f"- [{m.text[:140]}]({paths.get(m.id, '')})" for m in sorted(facts, key=lambda x: -x.importance)[:40]] + [""]
            (d / f"{slugify(name)}.md").write_text("\n".join(L))
            idx.append(f"- [{name}]({slugify(name)}.md) — {fm['description']}")
            n += 1
    (d / "index.md").write_text("\n".join(idx) + "\n")
    return n


def render_all(cfg: Config, mems: Dict[str, Memory]) -> List[str]:
    changed: List[str] = []
    write_index(cfg, mems)
    changed.append(str(cfg.paths.ledger / "_index.md"))
    try:
        write_lane_pages(cfg, mems)
        write_service_pages(cfg, mems)
    except Exception:
        pass
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
