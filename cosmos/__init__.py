"""cosmos - git-native shared engineering memory for AI coding agents."""
__version__ = "0.1.0"


def code_stamp() -> float:
    """Newest modification time of cosmos's own source. Long-running processes (watcher, console, MCP server)
    compare it to the value they started with, so an update never leaves them mixing old and new modules."""
    from pathlib import Path
    try:
        return max(p.stat().st_mtime for p in Path(__file__).parent.glob("*.py"))
    except (OSError, ValueError):
        return 0.0


def restart_process() -> None:
    """Replace this process with a fresh copy of itself (same interpreter, same arguments, same pid)."""
    import os
    import sys
    os.environ["COSMOS_REEXEC"] = "1"
    argv = list(getattr(sys, "orig_argv", None) or [sys.executable] + sys.argv)
    sys.stdout.flush()
    os.execv(sys.executable, [sys.executable] + argv[1:])


def fresh_modules() -> None:
    """Drop every loaded cosmos module so the next import reads the current source."""
    import sys
    for k in [k for k in sys.modules if k == "cosmos" or k.startswith("cosmos.")]:
        del sys.modules[k]
