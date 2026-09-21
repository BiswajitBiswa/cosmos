"""Make the ledger a first-class Obsidian vault (it already is plain markdown with wikilinks)."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.parse
from pathlib import Path
from typing import Optional

from .config import Config

_COLORS = {"architecture": (110, 168, 254), "decision": (192, 132, 252), "convention": (52, 211, 153), "constraint": (248, 113, 113),
           "bug": (251, 146, 60), "dependency": (250, 204, 21), "workflow": (34, 211, 238), "domain": (163, 230, 53), "rejected": (156, 163, 175), "finding": (239, 68, 68)}


def _rgb(t):  # Obsidian stores colors as packed int
    return (t[0] << 16) | (t[1] << 8) | t[2]


def prepare_vault(cfg: Config) -> Path:
    vault = cfg.paths.ledger
    ob = vault / ".obsidian"
    ob.mkdir(parents=True, exist_ok=True)
    app = ob / "app.json"
    if not app.exists():
        app.write_text(json.dumps({"alwaysUpdateLinks": True, "newLinkFormat": "shortest", "useMarkdownLinks": False, "showFrontmatter": True}, indent=2))
    graph = ob / "graph.json"
    if not graph.exists():
        groups = [{"query": f"path:{cat}", "color": {"a": 1, "rgb": _rgb(rgb)}} for cat, rgb in _COLORS.items()]
        groups.append({"query": "[status:superseded]", "color": {"a": 0.4, "rgb": _rgb((120, 120, 120))}})
        graph.write_text(json.dumps({"collapse-color-groups": False, "colorGroups": groups, "showTags": False, "showAttachments": False,
                                     "showOrphans": True, "nodeSizeMultiplier": 1.2, "lineSizeMultiplier": 1}, indent=2))
    # keep per-user Obsidian UI state out of git
    gi = cfg.paths.root / ".gitignore"
    line = ".cosmos/ledger/.obsidian/workspace*.json"
    txt = gi.read_text() if gi.exists() else ""
    if line not in txt:
        gi.write_text(txt.rstrip("\n") + ("\n" if txt else "") + line + "\n")
    return vault


def link_into_vault(cfg: Config, vault_path: Path) -> Path:
    """Symlink the ledger into an existing personal/team Obsidian vault as cosmos/<repo>."""
    target = vault_path.expanduser().resolve() / "cosmos" / cfg.paths.root.name
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.is_symlink() or target.exists():
        if target.is_symlink() and Path(os.readlink(target)).resolve() == cfg.paths.ledger.resolve():
            return target
        raise SystemExit(f"{target} already exists and is not a link to this ledger.")
    target.symlink_to(cfg.paths.ledger.resolve(), target_is_directory=True)
    return target


def open_in_obsidian(path: Path) -> Optional[str]:
    uri = "obsidian://open?path=" + urllib.parse.quote(str(path.resolve()))
    try:
        if sys.platform == "darwin":
            subprocess.Popen(["open", uri])
        elif sys.platform.startswith("linux"):
            subprocess.Popen(["xdg-open", uri])
        elif sys.platform == "win32":
            os.startfile(uri)  # type: ignore[attr-defined]
        return uri
    except Exception:
        return None
