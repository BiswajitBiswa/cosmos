"""Repository-local configuration. JSON on purpose: stdlib only, py3.9+."""
from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

COSMOS_DIR = ".cosmos"
CONFIG_FILE = "config.json"

DEFAULT_CONFIG: Dict[str, Any] = {
    "version": 1,
    "capture": {"enabled": True, "min_score": 0.5, "max_per_batch": 40, "explicit_prefixes": ["remember:", "cosmos:"]},
    "privacy": {"redact_secrets": True, "author": "git"},  # author: git | anonymous
    "retrieval": {"session_start_max": 10, "prompt_max": 6},
    "dream": {"llm": "auto", "staleness_days": {"dependency": 45, "workflow": 120, "architecture": 240, "default": 180}},
    "llm": {"provider": "auto"},   # auto: Anthropic API key if present, else your Claude Code login (claude -p), else heuristics
    "render": {"claude_md": True, "agents_md": True},
    "ignore": [".env*", "secrets/**", "**/*.pem", "**/*.key", "node_modules/**"],
}


def find_repo_root(start: Optional[Path] = None) -> Path:
    """Git toplevel if available, else the first parent containing .cosmos, else cwd."""
    start = (start or Path.cwd()).resolve()
    try:
        out = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=start, capture_output=True, text=True, timeout=3)
        if out.returncode == 0 and out.stdout.strip():
            return Path(out.stdout.strip())
    except Exception:
        pass
    for p in [start, *start.parents]:
        if (p / COSMOS_DIR).is_dir():
            return p
    return start


def _deep_merge(base: Dict[str, Any], over: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(base)
    for k, v in over.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


@dataclass
class Paths:
    root: Path

    @property
    def cosmos(self) -> Path: return self.root / COSMOS_DIR
    @property
    def ledger(self) -> Path: return self.cosmos / "ledger"
    @property
    def observations(self) -> Path: return self.cosmos / "observations"
    @property
    def state(self) -> Path: return self.cosmos / "state"
    @property
    def config(self) -> Path: return self.cosmos / CONFIG_FILE
    @property
    def log(self) -> Path: return self.state / "hook.log"
    @property
    def claude_settings(self) -> Path: return self.root / ".claude" / "settings.json"

    def ensure(self) -> None:
        for p in (self.ledger, self.observations, self.state):
            p.mkdir(parents=True, exist_ok=True)


@dataclass
class Config:
    paths: Paths
    data: Dict[str, Any] = field(default_factory=lambda: dict(DEFAULT_CONFIG))

    def get(self, dotted: str, default: Any = None) -> Any:
        cur: Any = self.data
        for part in dotted.split("."):
            if not isinstance(cur, dict) or part not in cur:
                return default
            cur = cur[part]
        return cur

    @property
    def ignore_globs(self) -> List[str]:
        return list(self.get("ignore", []))

    def save(self) -> None:
        self.paths.cosmos.mkdir(parents=True, exist_ok=True)
        self.paths.config.write_text(json.dumps(self.data, indent=2) + "\n")


def load_config(root: Optional[Path] = None) -> Config:
    root = root or find_repo_root()
    paths = Paths(root)
    data = dict(DEFAULT_CONFIG)
    if paths.config.exists():
        try:
            data = _deep_merge(DEFAULT_CONFIG, json.loads(paths.config.read_text()))
        except Exception:
            pass
    return Config(paths=paths, data=data)


def is_initialized(root: Optional[Path] = None) -> bool:
    root = root or find_repo_root()
    return (root / COSMOS_DIR / CONFIG_FILE).exists()


def git_author(root: Path) -> str:
    try:
        out = subprocess.run(["git", "config", "user.name"], cwd=root, capture_output=True, text=True, timeout=3)
        name = out.stdout.strip()
        return name or "anonymous"
    except Exception:
        return "anonymous"


def git_head(root: Path) -> str:
    try:
        out = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=root, capture_output=True, text=True, timeout=3)
        return out.stdout.strip()
    except Exception:
        return ""


def env_flag(name: str) -> bool:
    return os.environ.get(name, "").lower() in ("1", "true", "yes")
