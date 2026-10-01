"""`cosmos connect`: one store, every agent.

Read side - the managed block is written to each agent's instruction file (CLAUDE.md, AGENTS.md, GEMINI.md,
.cursor/rules, .github/copilot-instructions.md, .clinerules, .windsurfrules). Tool side - project-scoped MCP
configs point every agent at `cosmos mcp`; the same slash commands (/recall, /flare, /qa …) are written for every
agent that reads project commands (cosmos/commands.py). Capture side - Claude Code via hooks; Codex, Gemini and others via
`cosmos capture --agent …` reading their session logs.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from .config import Config

MCP_CMD = ["python3", ".cosmos/cosmosw", "mcp"]


DESKTOP_CONFIG = Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"


def desktop_pins(root: Path, config: Path = None) -> List[str]:
    """A Claude Desktop MCP entry named `cosmos` that serves another repository: in every Desktop session it takes the
    name of the project's own server, so cosmos_remember / cosmos_flare land in that other repository's ledger."""
    p = config or DESKTOP_CONFIG
    try:
        servers = json.loads(p.read_text()).get("mcpServers", {}) if p.exists() else {}
    except (OSError, ValueError):
        return []
    entry = servers.get("cosmos") or {}
    target = next((a for a in entry.get("args", []) if a.endswith("cosmosw")), "")
    if not target or Path(target).resolve().parent.parent == root.resolve():
        return []
    return [f"Claude Desktop's MCP entry `cosmos` serves {Path(target).parent.parent}: in Desktop sessions here, cosmos tools write there. "
            f"Rename it in {p} (e.g. cosmos-{Path(target).parent.parent.name})"]


def mcp_server_entry(root: Path, absolute: bool = False) -> Dict:
    args = [str(root / ".cosmos" / "cosmosw"), "mcp"] if absolute else [".cosmos/cosmosw", "mcp"]
    return {"command": "python3", "args": args}


def _merge_json(path: Path, key: str, name: str, entry: Dict, extra_keys: Dict = None) -> bool:
    data: Dict = {}
    if path.exists():
        try:
            data = json.loads(path.read_text() or "{}")
        except Exception:
            raise SystemExit(f"{path} is not valid JSON; fix it and re-run")
    servers = data.setdefault(key, {})
    if servers.get(name) == {**entry, **(extra_keys or {})}:
        return False
    servers[name] = {**entry, **(extra_keys or {})}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")
    return True


def connect(cfg: Config, agents: List[str]) -> List[str]:
    root = cfg.paths.root
    done: List[str] = []
    entry = mcp_server_entry(root)
    if "claude" in agents:
        if _merge_json(root / ".mcp.json", "mcpServers", "cosmos", entry):
            done.append(".mcp.json (Claude Code project MCP)")
    if "cursor" in agents:
        if _merge_json(root / ".cursor" / "mcp.json", "mcpServers", "cosmos", entry):
            done.append(".cursor/mcp.json")
    if "gemini" in agents:
        if _merge_json(root / ".gemini" / "settings.json", "mcpServers", "cosmos", entry):
            done.append(".gemini/settings.json")
    if "copilot" in agents:
        if _merge_json(root / ".vscode" / "mcp.json", "servers", "cosmos", {**entry, "type": "stdio"}):
            done.append(".vscode/mcp.json (Copilot)")
    done += connect_idx(cfg)
    from .commands import write_commands
    write_commands(root, agents, cfg)                 # the catalogue and the repository's playbooks; reported by commands.status()
    return done


def connect_idx(cfg: Config) -> List[str]:
    """Firebase Studio (formerly Project IDX; no new workspaces since 2026-06-22, shut down 2027-03-22): a workspace
    with .idx/ gets the cosmos MCP server in .idx/mcp.json. Its Gemini reads GEMINI.md and AGENTS.md, which cosmos
    already writes, and .idx/airules.md first, which gets the same block when the team has one (render_all)."""
    root = cfg.paths.root
    if not (root / ".idx").is_dir():
        return []
    return [".idx/mcp.json (Firebase Studio)"] if _merge_json(root / ".idx" / "mcp.json", "mcpServers", "cosmos", mcp_server_entry(root)) else []


def codex_snippet(root: Path) -> str:
    e = mcp_server_entry(root, absolute=True)
    return f'[mcp_servers.cosmos]\ncommand = "{e["command"]}"\nargs = {json.dumps(e["args"])}\n'


def write_codex_user_config(root: Path, home: Path = None) -> Path:
    p = (home or Path.home()) / ".codex" / "config.toml"
    txt = p.read_text() if p.exists() else ""
    if "[mcp_servers.cosmos]" in txt:
        return p
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(txt.rstrip("\n") + ("\n\n" if txt else "") + codex_snippet(root))
    return p
