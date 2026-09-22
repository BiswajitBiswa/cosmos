"""Zero-install onboarding: `cosmos init` writes .cosmos/cosmosw (committed) and vendors the package next to it.

Hooks call `python3 .cosmos/cosmosw hook`, so a developer who clones the repo needs nothing installed:
the wrapper uses an installed `cosmos` if present, else the vendored copy in .cosmos/vendor/.
Same idea as gradlew / mvnw. `cosmos init` (or `cosmos update`) refreshes the vendored copy.
"""
from __future__ import annotations

import shutil
from pathlib import Path

HOOK_CMD = ('d="${CLAUDE_PROJECT_DIR:-.}"; [ -f "$d/.cosmos/cosmosw" ] || d="$(dirname "$(git -C "$d" rev-parse --path-format=absolute '
            '--git-common-dir 2>/dev/null)")"; [ -f "$d/.cosmos/cosmosw" ] && exec python3 "$d/.cosmos/cosmosw" hook; exit 0')

WRAPPER = '''#!/usr/bin/env python3
"""cosmosw - runs cosmos without requiring an install (see .cosmos/vendor). Committed on purpose."""
import os, sys
here = os.path.dirname(os.path.abspath(__file__))
try:
    import cosmos  # installed version wins
except ImportError:
    sys.path.insert(0, os.path.join(here, "vendor"))
    try:
        import cosmos  # vendored copy shipped with the repo
    except ImportError:
        if "hook" in sys.argv[1:]:
            sys.exit(0)  # never block a Claude Code session
        sys.exit("cosmos is not installed and .cosmos/vendor is missing: pip install cosmos-dev")
from cosmos.cli import main
sys.exit(main())
'''


def write_wrapper(cosmos_dir: Path) -> Path:
    p = cosmos_dir / "cosmosw"
    p.write_text(WRAPPER)
    p.chmod(0o755)
    return p


def vendor(cosmos_dir: Path) -> Path:
    """Copy this package's source into .cosmos/vendor/cosmos (stdlib only, ~150 KB)."""
    src = Path(__file__).resolve().parent
    dst = cosmos_dir / "vendor" / "cosmos"
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    return dst


def hook_command(root: Path) -> str:
    """Anchored to $CLAUDE_PROJECT_DIR (Claude Code sets it for hooks), so a session that cd's into a sibling repo still
    reaches this repo's wrapper - and a repo without .cosmos exits 0 instead of printing an error. `exec` keeps the
    Gate's exit code 2 intact."""
    return HOOK_CMD
