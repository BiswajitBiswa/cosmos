"""The ledger lives on its own branch, never in yours.

`.cosmos/` is a git worktree of the `cosmos` branch, attached inside the repository and ignored by it. Feature
branches never see a ledger change; the ledger still travels with the repository (one `git push` of one branch),
merges like code, and a fresh clone attaches it on the first session start. Nothing here runs inside a hook's
critical path: commits are quick and local, network work is done in the background.
"""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple

from .config import Config

BRANCH = "cosmos"
IGNORE = "state/\n__pycache__/\n*.pyc\n"


def _git(args: List[str], cwd: Path, timeout: int = 30) -> Tuple[int, str]:
    try:
        r = subprocess.run(["git", *args], cwd=str(cwd), capture_output=True, text=True, timeout=timeout)
        return r.returncode, (r.stdout + r.stderr).strip()
    except Exception as e:
        return 1, str(e)


def is_branch_mode(cfg: Config) -> bool:
    """True when .cosmos is a worktree (its .git is a file pointing at the repository's gitdir)."""
    return (cfg.paths.cosmos / ".git").is_file()


def has_remote_branch(root: Path) -> bool:
    code, _ = _git(["rev-parse", "--verify", "-q", f"refs/remotes/origin/{BRANCH}"], root)
    return code == 0


def has_local_branch(root: Path) -> bool:
    code, _ = _git(["rev-parse", "--verify", "-q", f"refs/heads/{BRANCH}"], root)
    return code == 0


def ensure_ignored(root: Path) -> bool:
    """`.cosmos/` in the repository's .gitignore (replacing the older `.cosmos/state/` line)."""
    gi = root / ".gitignore"
    txt = gi.read_text() if gi.exists() else ""
    lines = [l for l in txt.splitlines() if l.strip() not in (".cosmos/state/", ".cosmos/state")]
    if ".cosmos/" not in [l.strip() for l in lines] and ".cosmos" not in [l.strip() for l in lines]:
        lines.append(".cosmos/")
    new = "\n".join(lines).rstrip("\n") + "\n"
    if new != txt:
        gi.write_text(new)
        return True
    return False


def linked(root: Path) -> bool:
    """.cosmos/.git names a worktree record git still has. A sandbox that sees the repo under another path (Cowork)
    can prune that record; then every ledger commit fails until it is repaired."""
    g = root / ".cosmos" / ".git"
    try:
        target = g.read_text().split("gitdir:", 1)[1].strip()
    except (OSError, IndexError):
        return False
    return Path(target).is_dir()


def repair(root: Path) -> Tuple[bool, str]:
    """Re-register .cosmos as the worktree of the cosmos branch without touching its files: a fresh worktree record
    is created next to it, its link is moved into .cosmos, and the index is reset to the branch. What .cosmos holds
    that the branch does not (the newest ledger) then shows as changes and is committed by the next sync."""
    import shutil
    import time
    cos = root / ".cosmos"
    if not (cos / ".git").is_file() or linked(root):
        return True, "linked"
    if not has_local_branch(root):
        if not has_remote_branch(root):
            return False, "no cosmos branch to attach to"
        _git(["branch", "-q", "--track", BRANCH, f"origin/{BRANCH}"], root)
    _git(["worktree", "prune"], root)
    tmp = root / f".cosmos-relink-{int(time.time())}"
    code, out = _git(["worktree", "add", "-q", "--no-checkout", str(tmp), BRANCH], root)
    if code != 0:
        return False, out
    try:
        (cos / ".git").write_text((tmp / ".git").read_text())
        shutil.rmtree(tmp, ignore_errors=True)
        _git(["worktree", "repair", str(cos)], root)
        code, out = _git(["reset", "-q"], cos)
        return (code == 0 and linked(root)), ("relinked" if code == 0 else out)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def merged_into_head(root: Path) -> str:
    """The merge commit that brought the ledger branch into the checked-out branch ("" when it is not there)."""
    code, first = _git(["rev-list", "--max-parents=0", BRANCH], root)
    first = first.strip().splitlines()[0] if code == 0 and first.strip() else ""
    if not first:
        return ""
    code, head = _git(["rev-parse", "--abbrev-ref", "HEAD"], root)
    if head.strip() == BRANCH or _git(["merge-base", "--is-ancestor", first, "HEAD"], root)[0] != 0:
        return ""
    code, out = _git(["log", "--merges", "--ancestry-path", "--format=%h", f"{first}..HEAD"], root)
    merges = out.split()
    return merges[-1] if merges else first[:8]


def attach(root: Path) -> Tuple[bool, str]:
    """Attach .cosmos as a worktree of the cosmos branch: from origin/cosmos when it exists, from the local branch,
    or as a new orphan branch. Idempotent; a worktree whose record was pruned is relinked."""
    cos = root / ".cosmos"
    if (cos / ".git").is_file():
        return repair(root) if not linked(root) else (True, "already attached")
    if cos.exists() and any(cos.iterdir()):
        return False, ".cosmos exists and is not a worktree (run migration)"
    if has_local_branch(root):
        code, out = _git(["worktree", "add", "-q", str(cos), BRANCH], root)
    elif has_remote_branch(root):
        code, out = _git(["worktree", "add", "-q", "--track", "-B", BRANCH, str(cos), f"origin/{BRANCH}"], root)
    else:
        ok, out = _create_orphan_branch(root)
        if not ok:
            return False, out
        code, out = _git(["worktree", "add", "-q", str(cos), BRANCH], root)
    if code != 0:
        return False, out
    (cos / ".gitignore").write_text(IGNORE)
    ensure_ignored(root)
    return True, "attached"


def _create_orphan_branch(root: Path) -> Tuple[bool, str]:
    """An empty first commit on a new `cosmos` branch, built from a temporary index so it works on any git version
    and even in a repository that has no commits yet. Never touches HEAD or the user's index."""
    import tempfile
    env = {**os.environ, "GIT_INDEX_FILE": tempfile.mktemp(prefix="cosmos-index-"),
           "GIT_AUTHOR_NAME": "cosmos", "GIT_AUTHOR_EMAIL": "cosmos@users.noreply.github.com",
           "GIT_COMMITTER_NAME": "cosmos", "GIT_COMMITTER_EMAIL": "cosmos@users.noreply.github.com"}
    try:
        r = subprocess.run(["git", "read-tree", "--empty"], cwd=str(root), env=env, capture_output=True, text=True, timeout=15)
        if r.returncode != 0:
            return False, r.stderr.strip()
        tree = subprocess.run(["git", "write-tree"], cwd=str(root), env=env, capture_output=True, text=True, timeout=15).stdout.strip()
        commit = subprocess.run(["git", "commit-tree", tree, "-m", "cosmos: ledger branch"], cwd=str(root), env=env, capture_output=True, text=True, timeout=15).stdout.strip()
        r = subprocess.run(["git", "branch", BRANCH, commit], cwd=str(root), capture_output=True, text=True, timeout=15)
        return r.returncode == 0, r.stderr.strip()
    except Exception as e:
        return False, str(e)
    finally:
        try:
            os.unlink(env["GIT_INDEX_FILE"])
        except Exception:
            pass


def migrate(root: Path) -> Tuple[bool, str]:
    """A repository that tracks .cosmos/ in its main tree: move that content to the cosmos branch, leave the working
    files in place, and stage the removal from the current branch (one path-limited commit, nothing else touched)."""
    cos = root / ".cosmos"
    if (cos / ".git").is_file():
        return True, "already on the cosmos branch"
    code, tracked = _git(["ls-files", ".cosmos"], root)
    keep = root / ".cosmos.migrating"
    if keep.exists():
        shutil.rmtree(keep)
    if cos.exists():
        cos.rename(keep)
    ok, msg = attach(root)
    if not ok:
        if keep.exists():
            keep.rename(cos)
        return False, msg
    if keep.exists():
        for p in keep.iterdir():
            dst = cos / p.name
            if p.name == ".git":
                continue
            if dst.exists():
                shutil.rmtree(dst) if dst.is_dir() else dst.unlink()
            shutil.move(str(p), str(dst))
        shutil.rmtree(keep, ignore_errors=True)
    (cos / ".gitignore").write_text(IGNORE)
    commit(root, "cosmos: ledger moved to its own branch")
    if tracked.strip():
        _git(["rm", "-r", "-q", "--cached", ".cosmos"], root)
    ensure_ignored(root)
    return True, "migrated"


def commit(root: Path, message: str) -> bool:
    """Commit whatever changed in the ledger worktree. Local and quick; safe to call often."""
    if not linked(root):
        repair(root)
    cos = root / ".cosmos"
    if not (cos / ".git").is_file():
        return False
    _git(["add", "-A"], cos)
    code, out = _git(["diff", "--cached", "--quiet"], cos)
    if code == 0:
        return False
    code, out = _git(["-c", "user.name=cosmos", "-c", "user.email=cosmos@users.noreply.github.com", "commit", "-q", "-m", message], cos)
    return code == 0


def push(root: Path, timeout: int = 60) -> Tuple[bool, str]:
    """Bring the branch up to date and publish it. Concurrent teammates are the normal case: rebase first; if two
    people changed the same note, keep both sides' files (ours on conflict) and let the next dream reconcile."""
    cos = root / ".cosmos"
    if not (cos / ".git").is_file():
        return False, "not attached"
    code, _ = _git(["remote", "get-url", "origin"], root)
    if code != 0:
        return False, "no origin"
    _git(["fetch", "-q", "origin", BRANCH], cos, timeout)
    if has_remote_branch(root):
        code, out = _git(["rebase", "-q", f"origin/{BRANCH}"], cos, timeout)
        if code != 0:
            _git(["rebase", "--abort"], cos)
            code, out = _git(["merge", "-q", "-X", "ours", "--no-edit", f"origin/{BRANCH}"], cos, timeout)
            if code != 0:
                return False, "merge failed: " + out[:200]
    code, out = _git(["push", "-q", "-u", "origin", f"{BRANCH}:{BRANCH}"], cos, timeout)
    return code == 0, out[:200]


def sync_background(cfg: Config, message: str = "cosmos: dream") -> bool:
    """Commit now (local), publish in a detached process (network). Used at the end of a dream and by the watcher."""
    if not is_branch_mode(cfg):
        return False
    commit(cfg.paths.root, message)
    if os.environ.get("COSMOS_NO_BACKGROUND") or not cfg.get("sync.auto_push", True):
        return False
    try:
        import sys
        wrapper = cfg.paths.cosmos / "cosmosw"
        cmd = [sys.executable, str(wrapper), "sync", "--push"] if wrapper.exists() else [sys.executable, "-m", "cosmos", "sync", "--push"]
        log = (cfg.paths.state / "sync.log").open("a")
        subprocess.Popen(cmd, cwd=str(cfg.paths.root), stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        return True
    except Exception:
        return False


def status(cfg: Config) -> dict:
    root = cfg.paths.root
    cos = cfg.paths.cosmos
    out = {"branch_mode": is_branch_mode(cfg), "remote": has_remote_branch(root)}
    if out["branch_mode"]:
        code, ahead = _git(["rev-list", "--count", f"origin/{BRANCH}..HEAD"], cos)
        out["unpushed"] = int(ahead) if code == 0 and ahead.isdigit() else None
        code, dirty = _git(["status", "--porcelain"], cos)
        out["uncommitted"] = len([l for l in dirty.splitlines() if l.strip()]) if code == 0 else None
    return out
