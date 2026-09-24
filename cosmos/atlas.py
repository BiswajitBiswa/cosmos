"""Atlas: architecture diagrams generated from the repository itself and kept in sync.

Deterministic pass (no LLM): read manifests, docker-compose, k8s, Terraform, OpenAPI, README and .env.example;
write an inventory, a dependency index and Mermaid diagrams into `.cosmos/ledger/atlas/`, each with its sources
and the HEAD commit. `check()` hashes the sources so a later dream (or `cosmos atlas --check`) reports drift the
moment the code moves and the picture does not. A `/atlas` Claude Code command adds the deeper, LLM-driven pass.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .config import Config, git_head
from .store import today

MANIFESTS = ["package.json", "pyproject.toml", "requirements.txt", "requirements-*.txt", "requirements/*.txt", "pom.xml", "build.gradle", "build.gradle.kts", "go.mod", "Cargo.toml", "Gemfile",
             "setup.py", "**/package.json", "**/pyproject.toml", "**/requirements.txt", "**/setup.py", "**/go.mod", "**/Cargo.toml"]
COMPOSE = ["docker-compose*.yml", "docker-compose*.yaml", "compose*.yml", "compose*.yaml", "**/docker-compose*.yml"]
K8S_DIRS = ["k8s", "kubernetes", "deploy", "deployment", "helm", "charts", "manifests"]
TF = ["**/*.tf"]
OPENAPI = ["openapi*.json", "openapi*.y*ml", "swagger*.json", "swagger*.y*ml", "**/openapi*.json", "**/openapi*.y*ml", "**/swagger*.json", "**/swagger*.y*ml", "docs/api*.y*ml"]
STORE_IMAGES = {"postgres": "database", "postgresql": "database", "mysql": "database", "mariadb": "database", "mongo": "database", "clickhouse": "database", "sqlite": "database",
                "redis": "cache", "memcached": "cache", "kafka": "queue", "rabbitmq": "queue", "nats": "queue", "sqs": "queue", "elasticsearch": "search", "opensearch": "search",
                "minio": "object storage", "localstack": "cloud emulator", "authentik": "identity", "keycloak": "identity", "nginx": "gateway", "traefik": "gateway"}
SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build", ".cosmos", ".next", "target", ".idea", ".terraform"}


def _walk(root: Path, patterns: List[str], limit: int = 400) -> List[Path]:
    out: List[Path] = []
    for pat in patterns:
        for p in root.glob(pat):
            if any(part in SKIP_DIRS for part in p.relative_to(root).parts):
                continue
            if p.is_file() and p not in out:
                out.append(p)
            if len(out) >= limit:
                return out
    return out


def _sha(p: Path) -> str:
    try:
        return hashlib.sha1(p.read_bytes()).hexdigest()[:12]
    except Exception:
        return ""


# ---------------------------------------------------------------- tiny YAML (mappings + scalar lists + inline lists), enough for compose/k8s
def parse_yaml_subset(text: str) -> Any:
    lines = [l.rstrip() for l in text.splitlines() if l.strip() and not l.strip().startswith("#")]

    def parse_block(i: int, indent: int):
        items: Any = None
        while i < len(lines):
            raw = lines[i]
            ind = len(raw) - len(raw.lstrip(" "))
            if ind < indent:
                break
            s = raw.strip()
            if s.startswith("- "):
                if items is None:
                    items = []
                val = s[2:].strip()
                if ":" in val and not val.startswith(("'", '"', "[", "{")):
                    k, _, v = val.partition(":")
                    d = {k.strip(): _scalar(v.strip())}
                    j = i + 1
                    sub, j2 = parse_block(j, ind + 2)
                    if isinstance(sub, dict):
                        d.update(sub)
                    items.append(d)
                    i = j2 if sub is not None else i + 1
                else:
                    items.append(_scalar(val))
                    i += 1
                continue
            if items is None:
                items = {}
            k, _, v = s.partition(":")
            v = v.strip()
            if v == "":
                sub, j = parse_block(i + 1, ind + 1)
                items[k.strip()] = sub if sub is not None else {}
                i = j
            else:
                items[k.strip()] = _scalar(v)
                i += 1
        return items, i

    def _scalar(v: str):
        if v.startswith("[") and v.endswith("]"):
            return [x.strip().strip("'\"") for x in v[1:-1].split(",") if x.strip()]
        return v.strip().strip("'\"")

    data, _ = parse_block(0, 0)
    return data if data is not None else {}


def load_yaml(text: str, where: str) -> Any:
    """Parse YAML with PyYAML when it is installed, else the subset parser above.

    parse_yaml_subset cannot read a block sequence written at the same indent as its
    parent key ("volumes:" followed by "- data:/var/lib" at equal indent), which is
    valid YAML and common in docker-compose. Preferring PyYAML keeps those files
    readable; the subset parser stays as the no-dependency fallback.
    """
    try:
        import yaml
    except ImportError:
        return parse_yaml_subset(text)
    try:
        return yaml.safe_load(text) or {}
    except Exception as exc:
        warn(f"{where}: PyYAML could not read it ({exc.__class__.__name__}); falling back to the subset parser")
        return parse_yaml_subset(text)


def warn(msg: str) -> None:
    print(f"cosmos atlas: {msg}", file=sys.stderr)


# ---------------------------------------------------------------- inventory
def inventory(cfg: Config) -> Dict[str, Any]:
    root = cfg.paths.root
    inv: Dict[str, Any] = {"repo": root.name, "commit": git_head(root), "generated": today(), "sources": [], "apps": [], "services": [], "stores": [],
                           "k8s": [], "terraform": {}, "api": [], "env_keys": [], "readme_title": ""}

    def src(p: Path) -> str:
        rel = str(p.relative_to(root))
        inv["sources"].append({"file": rel, "sha": _sha(p)})
        return rel

    for p in _walk(root, MANIFESTS, 60):
        rel = src(p)
        app = {"path": rel, "dir": str(p.parent.relative_to(root)) or ".", "kind": p.name, "name": p.parent.name if p.parent != root else root.name, "deps": 0, "scripts": []}
        try:
            txt = p.read_text(errors="ignore")
            if p.name == "package.json":
                d = json.loads(txt)
                app.update({"name": d.get("name", app["name"]), "language": "javascript/typescript", "deps": len(d.get("dependencies", {})) + len(d.get("devDependencies", {})), "scripts": list(d.get("scripts", {}))[:8]})
            elif p.name == "pyproject.toml":
                m = re.search(r'^name\s*=\s*"([^"]+)"', txt, re.M)
                app.update({"name": m.group(1) if m else app["name"], "language": "python", "deps": len(re.findall(r'^\s*"[A-Za-z0-9_.\-\[\]]+[><=~!]', txt, re.M))})
            elif p.name.startswith("requirements"):
                app.update({"language": "python", "deps": len([l for l in txt.splitlines() if l.strip() and not l.startswith(("#", "-"))])})
            elif p.name == "pom.xml":
                m = re.search(r"<artifactId>([^<]+)</artifactId>", txt)
                app.update({"name": m.group(1) if m else app["name"], "language": "java", "deps": txt.count("<dependency>")})
            elif p.name.startswith("build.gradle"):
                app.update({"language": "kotlin/java", "deps": len(re.findall(r"implementation\(|implementation ", txt))})
            elif p.name == "go.mod":
                m = re.search(r"^module\s+(\S+)", txt, re.M)
                app.update({"name": m.group(1) if m else app["name"], "language": "go", "deps": txt.count("\n\t")})
            elif p.name == "Cargo.toml":
                app.update({"language": "rust", "deps": len(re.findall(r"^\[dependencies\]", txt, re.M))})
            elif p.name == "Gemfile":
                app.update({"language": "ruby", "deps": txt.count("gem ")})
        except Exception:
            pass
        inv["apps"].append(app)

    for p in _walk(root, COMPOSE, 10):
        rel = src(p)
        try:
            data = load_yaml(p.read_text(errors="ignore"), rel)
        except Exception as exc:
            warn(f"{rel}: unreadable ({exc.__class__.__name__}: {exc}); its services are missing from the Atlas")
            continue
        if not isinstance(data, dict):
            warn(f"{rel}: parsed to {type(data).__name__}, not a mapping; skipped")
            continue
        for name, svc in (data.get("services") or {}).items():
            if not isinstance(svc, dict):
                continue
            image = str(svc.get("image", "")) if not isinstance(svc.get("image"), dict) else ""
            build = svc.get("build")
            ports = svc.get("ports") or []
            dep = svc.get("depends_on") or []
            if isinstance(dep, dict):
                dep = list(dep.keys())
            kind = next((v for k, v in STORE_IMAGES.items() if k in image.lower()), None)
            rec = {"name": name, "image": image, "build": (build.get("context") if isinstance(build, dict) else build) or "", "ports": [str(x) for x in ports][:4],
                   "depends_on": [str(x) for x in dep], "compose": rel, "kind": kind or "service"}
            (inv["stores"] if kind else inv["services"]).append(rec)

    for d in K8S_DIRS:
        for p in _walk(root / d, ["**/*.y*ml"], 80) if (root / d).exists() else []:
            rel = src(p)
            txt = p.read_text(errors="ignore")
            for kind, name in re.findall(r"^kind:\s*(\w+)\s*$[\s\S]*?^\s*name:\s*([\w\-.]+)", txt, re.M):
                inv["k8s"].append({"kind": kind, "name": name, "file": rel})
    for p in _walk(root, TF, 200):
        rel = src(p)
        for rtype in re.findall(r'^resource\s+"([\w\-]+)"', p.read_text(errors="ignore"), re.M):
            inv["terraform"][rtype] = inv["terraform"].get(rtype, 0) + 1
    for p in _walk(root, OPENAPI, 6):
        rel = src(p)
        txt = p.read_text(errors="ignore")
        paths: List[Tuple[str, str]] = []
        try:
            if p.suffix == ".json":
                for path, ops in (json.loads(txt).get("paths") or {}).items():
                    for method in ops:
                        if method.lower() in ("get", "post", "put", "patch", "delete"):
                            paths.append((method.upper(), path))
            else:
                cur = None
                for line in txt.splitlines():
                    m = re.match(r"^  (/[^:\s]*):\s*$", line)
                    if m:
                        cur = m.group(1); continue
                    m2 = re.match(r"^    (get|post|put|patch|delete):", line)
                    if m2 and cur:
                        paths.append((m2.group(1).upper(), cur))
        except Exception:
            pass
        inv["api"].append({"spec": rel, "endpoints": paths[:300]})
    env = root / ".env.example"
    if env.exists():
        src(env)
        inv["env_keys"] = [l.split("=", 1)[0].strip() for l in env.read_text(errors="ignore").splitlines() if "=" in l and not l.strip().startswith("#")][:200]
    for name in ("README.md", "README.rst", "README"):
        if (root / name).exists():
            src(root / name)
            m = re.search(r"^#\s+(.+)$", (root / name).read_text(errors="ignore"), re.M)
            inv["readme_title"] = m.group(1).strip() if m else ""
            break
    return inv


# ---------------------------------------------------------------- diagrams
def _id(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]", "_", s)


def _unique_by_name(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """First record wins per name, order preserved.

    A service defined in several compose files (docker-compose.yml and
    docker-compose.local.yml both declare rms_postgresql) is one box in the picture.
    inventory.md still lists every row, with its compose file, so the overlap stays visible.
    """
    seen: Dict[str, Dict[str, Any]] = {}
    for r in records:
        seen.setdefault(r["name"], r)
    return list(seen.values())


def mermaid_containers(inv: Dict[str, Any]) -> str:
    L = ["flowchart LR"]
    services, stores = _unique_by_name(inv["services"]), _unique_by_name(inv["stores"])
    for s in services:
        port = f"<br/>:{s['ports'][0].split(':')[0]}" if s["ports"] else ""
        L.append(f'  {_id(s["name"])}["{s["name"]}{port}"]')
    for s in stores:
        L.append(f'  {_id(s["name"])}[("{s["name"]}<br/><i>{s["kind"]}</i>")]')
    edges = []
    for s in services + stores:
        for d in s["depends_on"]:
            edge = f"  {_id(s['name'])} --> {_id(d)}"
            if edge not in edges:
                edges.append(edge)
    L += edges
    if len(L) == 1:
        for a in inv["apps"]:
            L.append(f'  {_id(a["name"])}["{a["name"]}<br/><i>{a.get("language","")}</i>"]')
    if stores:
        L.append("  classDef store fill:#f3ead3,stroke:#b8923c,color:#1b2a4a")
        L.append("  class " + ",".join(_id(s["name"]) for s in stores) + " store")
    return "\n".join(L)


def mermaid_deployment(inv: Dict[str, Any]) -> str:
    L = ["flowchart TB"]
    by_kind: Dict[str, List[str]] = defaultdict(list)
    for k in inv["k8s"]:
        by_kind[k["kind"]].append(k["name"])
    for kind, names in by_kind.items():
        L.append(f'  subgraph {_id(kind)}["{kind} ({len(names)})"]')
        for n in names[:25]:
            L.append(f'    {_id(kind+n)}["{n}"]')
        L.append("  end")
    if inv["terraform"]:
        L.append('  subgraph TF["Terraform resources"]')
        for rtype, n in sorted(inv["terraform"].items(), key=lambda kv: -kv[1])[:20]:
            L.append(f'    {_id(rtype)}["{rtype} ×{n}"]')
        L.append("  end")
    if len(L) == 1:
        L.append('  none["no k8s / terraform found — deployment described by docker-compose only"]')
    return "\n".join(L)


def build(cfg: Config) -> Dict[str, Any]:
    inv = inventory(cfg)
    d = cfg.paths.ledger / "atlas"
    d.mkdir(parents=True, exist_ok=True)
    head = f"_Generated by cosmos atlas on {inv['generated']} at commit `{inv['commit'] or '?'}`. Sources are listed at the bottom; run `cosmos atlas --check` to detect drift._"
    srcs = "\n".join(f"- `{s['file']}`" for s in inv["sources"]) or "- (none found)"
    # inventory.md
    L = ["---", 'tags: ["atlas"]', "---", f"# Atlas · Inventory — {inv['repo']}", "", head, ""]
    if inv["readme_title"]:
        L += [f"README: **{inv['readme_title']}**", ""]
    L += ["## Apps and packages", "", "| name | language | manifest | dependencies | scripts |", "|---|---|---|---|---|"]
    L += [f"| {a['name']} | {a.get('language','?')} | `{a['path']}` | {a['deps']} | {', '.join(a['scripts'])} |" for a in inv["apps"]] or ["| — | | | | |"]
    L += ["", "## Services (docker-compose)", "", "| service | image / build | ports | depends on | defined in |", "|---|---|---|---|---|"]
    L += [f"| {s['name']} | {s['image'] or s['build']} | {', '.join(s['ports'])} | {', '.join(s['depends_on'])} | `{s['compose']}` |" for s in inv["services"]] or ["| — | | | | |"]
    L += ["", "## Data stores, queues, infrastructure containers", "", "| name | kind | image | defined in |", "|---|---|---|---|"]
    L += [f"| {s['name']} | {s['kind']} | {s['image']} | `{s['compose']}` |" for s in inv["stores"]] or ["| — | | | |"]
    if inv["env_keys"]:
        L += ["", f"## Configuration keys (.env.example, {len(inv['env_keys'])})", "", ", ".join(f"`{k}`" for k in inv["env_keys"])]
    L += ["", "## Sources", "", srcs]
    (d / "inventory.md").write_text("\n".join(L) + "\n")
    # containers.md
    (d / "containers.md").write_text("\n".join(["---", "type: Diagram", 'tags: ["atlas","diagram"]', "---", f"# Atlas · Containers — {inv['repo']}", "", head, "", "```mermaid", mermaid_containers(inv), "```", "", "## Sources", "", srcs]) + "\n")
    # deployment.md
    (d / "deployment.md").write_text("\n".join(["---", "type: Diagram", 'tags: ["atlas","diagram"]', "---", f"# Atlas · Deployment — {inv['repo']}", "", head, "", "```mermaid", mermaid_deployment(inv), "```", "", "## Sources", "", srcs]) + "\n")
    # api.md
    A = ["---", 'tags: ["atlas"]', "---", f"# Atlas · API surface — {inv['repo']}", "", head, ""]
    for spec in inv["api"]:
        A += [f"## `{spec['spec']}` — {len(spec['endpoints'])} endpoints", "", "| method | path |", "|---|---|"] + [f"| {m} | `{p}` |" for m, p in spec["endpoints"]] + [""]
    if not inv["api"]:
        A += ["No OpenAPI / Swagger spec found. Run `/atlas` in Claude Code for a code-derived API index.", ""]
    (d / "api.md").write_text("\n".join(A))
    (d / "atlas.json").write_text(json.dumps(inv, indent=1))
    return inv


def check(cfg: Config) -> Dict[str, Any]:
    """Compare recorded source hashes with the working tree. Returns {"exists", "drift": [files], "missing": [files], "generated", "commit"}."""
    p = cfg.paths.ledger / "atlas" / "atlas.json"
    if not p.exists():
        return {"exists": False, "drift": [], "missing": [], "generated": "", "commit": ""}
    inv = json.loads(p.read_text())
    drift, missing = [], []
    for s in inv.get("sources", []):
        f = cfg.paths.root / s["file"]
        if not f.exists():
            missing.append(s["file"])
        elif _sha(f) != s["sha"]:
            drift.append(s["file"])
    return {"exists": True, "drift": drift, "missing": missing, "generated": inv.get("generated", ""), "commit": inv.get("commit", ""),
            "counts": {"apps": len(inv.get("apps", [])), "services": len(inv.get("services", [])), "stores": len(inv.get("stores", [])), "k8s": len(inv.get("k8s", [])), "endpoints": sum(len(a["endpoints"]) for a in inv.get("api", []))}}


COMMAND_MD = """---
description: Build or refresh the Atlas — inventory, dependency index and architecture diagrams — into .cosmos/ledger/atlas
---
You are building the **Atlas** for this repository: a living architecture record that cosmos keeps in sync with the code. `cosmos atlas` has already produced a deterministic inventory (`.cosmos/ledger/atlas/inventory.md`, `containers.md`, `deployment.md`, `api.md`) — read those first, then deepen them in three passes and WRITE files; do not just answer in chat.

## Pass 1 — Inventory (no diagrams yet)
Read, in this order, whatever exists: repository root listing · monorepo workspaces · `package.json` / `pom.xml` / `build.gradle*` / `pyproject.toml` / `requirements*.txt` / `go.mod` · `docker-compose*.yml` · `k8s/**`, `helm/**` · `terraform/**` · `README*` · `.env.example` · OpenAPI / Swagger specs · CI workflows.
Update `inventory.md`: services and apps (name, language, entry point, port), data stores, queues/topics, external APIs, environments, and every config key from `.env.example` with which service reads it. Cite the file for each row. Never read `.env`, secrets or credentials.

## Pass 2 — Dependency index
Write `.cosmos/ledger/atlas/dependencies.md`: service → service calls, service → store, service → queue, and the public API surface (method, path, handler file, auth). Prefer facts found in code and specs over README claims; where they disagree record both and mark `DRIFT`.

## Pass 3 — Diagrams (Mermaid, one per file, each ending with a `## Sources` list and the HEAD commit)
1. `system-context.md` — actors, apps, external systems
2. `containers.md` — refine the generated one: protocols on edges, missing services
3. `data-flow.md` — the 2–3 flows that matter most to this product, end to end
4. `deployment.md` — from compose / k8s / Terraform: what runs where
5. `lanes.md` — group modules into feature lanes; propose a `lanes` mapping (lane → path globs) for `.cosmos/config.json`

Rules: every node must exist in the inventory; every edge must have a source file; use the team's own names; keep each diagram under 40 nodes (split if bigger). Finish with `cosmos atlas --check` and print a 5-line summary of what changed since the previous Atlas.
"""
