"""Sources the whole team already writes to, read at dream time. No agent, hook or install on their side.

  * git history   - every commit by anyone becomes a journal line (who, when, what, which files); a commit body that
                    explains itself is offered to the model as a candidate fact.
  * PR reviews    - review comments on merged pull requests (via the GitHub CLI, when it is logged in) are offered as
                    candidate rules and flares: "never do X" said in a review is a Charter rule in the making.
Both are incremental (state remembers where they stopped) and idempotent (deterministic ids).
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

from .config import Config
from .privacy import redact
from .store import Observations, State, now_iso

_SEP = "\x1f"
_REC = "\x1e"
_BOT = re.compile(r"\[bot\]$|dependabot|renovate|github-actions", re.I)


# ---------------------------------------------------------------- git history
def git_commits(cfg: Config, state: State, first_days: int = 30, limit: int = 400) -> List[Dict[str, Any]]:
    """New commits on any branch since the last pass, oldest first: sha, author, ts, subject, body, files."""
    root = cfg.paths.root
    since = state.data.get("gitlog_since") or (datetime.now(timezone.utc) - timedelta(days=first_days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    fmt = _REC + _SEP.join(["%H", "%an", "%aI", "%s", "%b"])
    try:
        out = subprocess.run(["git", "log", "--all", f"--since={since}", "--no-merges", f"--max-count={limit}", "--reverse",
                              "--name-only", f"--format={fmt}"], cwd=root, capture_output=True, text=True, timeout=60).stdout
    except Exception:
        return []
    commits: List[Dict[str, Any]] = []
    for chunk in out.split(_REC):
        if not chunk.strip():
            continue
        head, _, rest = chunk.partition("\n")
        parts = head.split(_SEP)
        if len(parts) < 5:
            continue
        sha, author, ts, subject, body = parts[0], parts[1], parts[2], parts[3], _SEP.join(parts[4:])
        files = [l.strip() for l in rest.splitlines() if l.strip() and not l.startswith(_REC)]
        # the body ends where the file list starts: git prints body then a blank line then files
        if "\n\n" in body:
            body = body.split("\n\n")[0]
        commits.append({"sha": sha, "author": author, "ts": ts, "subject": subject.strip(), "body": body.strip(), "files": files[:12]})
    return commits


def ingest_git(cfg: Config, state: State, store: Observations, existing_commit_msgs: set) -> Tuple[int, List[Dict]]:
    """Commits → journal records (skipping ones the transcripts already recorded) and candidate facts from bodies.
    Returns (journal_lines_added, candidate_observations)."""
    if not cfg.get("sources.git_log", True):
        return 0, []
    commits = git_commits(cfg, state)
    if not commits:
        return 0, []
    have = {o.get("id") for o in store.iter_all()}
    journal: List[Dict] = []
    cands: List[Dict] = []
    newest = state.data.get("gitlog_since", "")
    for c in commits:
        try:
            ts = datetime.fromisoformat(c["ts"]).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        except Exception:
            ts = now_iso()
        newest = max(newest, ts)
        if _BOT.search(c["author"] or ""):
            continue
        if c["subject"] in existing_commit_msgs:
            continue                                   # a session already journaled this commit
        oid = "obs_" + hashlib.sha1(("git:" + c["sha"]).encode()).hexdigest()[:10]
        if oid in have:
            continue
        text, _ = redact(f'commit "{c["subject"]}"' + (f" · {len(c['files'])} file{'s' if len(c['files']) != 1 else ''}" if c["files"] else ""))
        journal.append({"id": oid, "kind": "journal", "category": "workflow", "source": "git", "score": 1.0, "text": text, "ask": "",
                        "files": c["files"], "commits": [c["subject"][:120]], "tests": False, "pushes": 0, "prs": 0, "turns": 0,
                        "branch": "", "turn_uuid": "", "signals": ["git"], "ts": ts, "author": c["author"], "agent": "git",
                        "session": "", "commit": c["sha"][:8], "event": "git"})
        body = " ".join(c["body"].split())
        if len(body) >= 60 and not body.lower().startswith(("co-authored-by", "signed-off-by")):
            btext, fired = redact(f"Commit note by {c['author']}: {c['subject']} — {body}"[:700])
            if not fired:
                cands.append({"id": "obs_" + hashlib.sha1(("gitbody:" + c["sha"]).encode()).hexdigest()[:10], "text": btext, "category": "decision",
                              "score": 0.6, "source": "git", "files": c["files"][:6], "signals": ["git", "commit-body"], "turn_uuid": "", "ts": ts,
                              "author": c["author"], "agent": "git", "session": "", "commit": c["sha"][:8], "event": "git", "kind": "candidate"})
    if journal:
        store.append(journal)
    if newest:
        state.data["gitlog_since"] = newest
    return len(journal), cands


# ---------------------------------------------------------------- pull request reviews (GitHub CLI)
def gh_ready(cfg: Config) -> bool:
    if not cfg.get("sources.github_reviews", "auto"):
        return False
    if not shutil.which("gh"):
        return False
    try:
        r = subprocess.run(["gh", "auth", "status"], cwd=cfg.paths.root, capture_output=True, text=True, timeout=10)
        if r.returncode != 0:
            return False
        r = subprocess.run(["gh", "repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"], cwd=cfg.paths.root, capture_output=True, text=True, timeout=15)
        return r.returncode == 0 and bool(r.stdout.strip())
    except Exception:
        return False


def review_comments(cfg: Config, state: State, first_days: int = 30, pages: int = 3) -> List[Dict[str, Any]]:
    """Review comments across the repository's pull requests since the last pass (GitHub REST, via gh)."""
    since = state.data.get("reviews_since") or (datetime.now(timezone.utc) - timedelta(days=first_days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    out: List[Dict[str, Any]] = []
    for page in range(1, pages + 1):
        try:
            r = subprocess.run(["gh", "api", f"repos/{{owner}}/{{repo}}/pulls/comments?since={since}&per_page=100&page={page}&sort=updated&direction=asc"],
                               cwd=cfg.paths.root, capture_output=True, text=True, timeout=60)
            if r.returncode != 0:
                break
            rows = json.loads(r.stdout or "[]")
        except Exception:
            break
        if not rows:
            break
        for c in rows:
            out.append({"id": str(c.get("id")), "body": str(c.get("body") or ""), "path": str(c.get("path") or ""), "line": c.get("line") or c.get("original_line"),
                        "author": ((c.get("user") or {}).get("login") or ""), "ts": str(c.get("updated_at") or c.get("created_at") or ""),
                        "pr": str(c.get("pull_request_url") or "").rsplit("/", 1)[-1], "url": str(c.get("html_url") or "")})
        if len(rows) < 100:
            break
    return out


def ingest_reviews(cfg: Config, state: State, store: Observations) -> List[Dict]:
    """Review comments → candidate observations for the model ('Review comment on PR #n by X on path: …')."""
    if not gh_ready(cfg):
        return []
    rows = review_comments(cfg, state)
    have = {o.get("id") for o in store.iter_all()}
    cands: List[Dict] = []
    newest = state.data.get("reviews_since", "")
    for c in rows:
        newest = max(newest, c["ts"][:19] + "Z" if len(c["ts"]) >= 19 else newest)
        body = " ".join(c["body"].split())
        if len(body) < 25 or _BOT.search(c["author"]) or body.lower().startswith(("lgtm", "nit:", "nit ", "typo", "+1", "thanks", "done")):
            continue
        oid = "obs_" + hashlib.sha1(("review:" + c["id"]).encode()).hexdigest()[:10]
        if oid in have:
            continue
        loc = c["path"] + (f":{c['line']}" if c.get("line") else "")
        text, fired = redact(f"Review comment on PR #{c['pr']} by {c['author']} on {loc}: {body}"[:700])
        if fired:
            continue
        cands.append({"id": oid, "text": text, "category": "convention", "score": 0.7, "source": "review", "files": [c["path"]] if c["path"] else [],
                      "signals": ["review", f"pr-{c['pr']}"], "turn_uuid": "", "ts": c["ts"][:19] + "Z" if len(c["ts"]) >= 19 else now_iso(),
                      "author": c["author"], "agent": "github", "session": "", "commit": "", "event": "review", "kind": "candidate", "url": c["url"]})
    if newest:
        state.data["reviews_since"] = newest
    return cands
