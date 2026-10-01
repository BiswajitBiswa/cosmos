"""Zero-install onboarding: `cosmos init` writes .cosmos/cosmosw (committed) and vendors the package next to it.

Hooks call `python3 .cosmos/cosmosw hook`, so a developer who clones the repo needs nothing installed:
the wrapper uses an installed `cosmos` if present, else the vendored copy in .cosmos/vendor/.
Same idea as gradlew / mvnw. `cosmos init` (or `cosmos update`) refreshes the vendored copy.
"""
from __future__ import annotations

import shutil
from pathlib import Path

HOOK_CMD = ('d="${CLAUDE_PROJECT_DIR:-.}"; if [ ! -f "$d/.cosmos/cosmosw" ]; then g="$(git -C "$d" rev-parse --path-format=absolute '
            '--git-common-dir 2>/dev/null)" && d="$(dirname "$g")"; fi; '   # only a real git root: "." would be whatever folder the hook ran in
            '[ -f "$d/.cosmos/cosmosw" ] && exec python3 "$d/.cosmos/cosmosw" hook; '
            # a session opened in a folder above the repositories (a workspace of several projects): each child repository
            # with cosmos gets the event and keeps only what touched it; the Gate's exit 2 from any of them is kept
            'p="${CLAUDE_PROJECT_DIR:-.}"; set -- "$p"/*/.cosmos/cosmosw; [ -f "$1" ] || exit 0; e="$(cat)"; r=0; '
            'for w in "$@"; do printf "%s" "$e" | COSMOS_PARENT_SESSION=1 python3 "$w" hook; [ $? -eq 2 ] && r=2; done; exit $r')

WRAPPER = r'''#!/usr/bin/env python3
"""cosmosw - runs cosmos without requiring an install (see .cosmos/vendor). Committed on purpose."""
import os, sys
here = os.path.dirname(os.path.abspath(__file__))
repo = os.path.dirname(here)
cwd = os.path.realpath(os.getcwd())
if cwd != os.path.realpath(repo) and not cwd.startswith(os.path.realpath(repo) + os.sep):
    os.chdir(repo)  # started from elsewhere (Claude Desktop, Cowork, a cron): this wrapper belongs to this repository
import importlib.util, re
def _ver(init):
    try:
        m = re.search(r'__version__\s*=\s*["\']([^"\']+)', open(init).read())
    except (OSError, TypeError):
        return ()
    return tuple(int(x) for x in re.findall(r"\d+", m.group(1))[:4]) if m else ()
vendor = os.path.join(here, "vendor")
spec = importlib.util.find_spec("cosmos")
if _ver(os.path.join(vendor, "cosmos", "__init__.py")) > _ver(spec.origin if spec else None):
    sys.path.insert(0, vendor)  # the repository's copy is newer than the installed one (or there is none): it wins
try:
    import cosmos  # otherwise the installed version
except ImportError:
    sys.path.insert(0, vendor)
    try:
        import cosmos  # vendored copy shipped with the repo
    except ImportError:
        if "hook" in sys.argv[1:]:
            sys.exit(0)  # never block a Claude Code session
        sys.exit("cosmos is not installed and .cosmos/vendor is missing: python3 -m pip install cosmos-dev")
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
