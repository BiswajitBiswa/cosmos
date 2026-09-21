"""Publish findings to Slack as Block Kit cards - one top-level post per finding, idempotent via a state file.

Ported from the QA-audit poster: same layout (icon + stable id + severity, locations, labelled sections,
ack legend with 👀 / ✅ / 🚫 pre-seeded reactions), same delta semantics (already-posted ids are skipped),
stdlib only. The token is read from SLACK_BOT_TOKEN, never stored, never printed.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import ssl
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional

from .audit import SEV_ICON
from .config import Config, git_head
from .store import Memory

ACK = ":eyes: taking it   ·   :white_check_mark: fixed   ·   :no_entry_sign: not a bug"
REACTIONS = ("eyes", "white_check_mark", "no_entry_sign")
SECTION_MAX, HEADER_MAX, FIELD_MAX = 2900, 150, 1900   # Slack: section 3000, header 150, fields 10×2000, 50 blocks
SEV_LABEL = {"critical": "CRITICAL", "high": "HIGH", "medium": "MEDIUM", "low": "LOW", "note": "NOTE", "info": "INFO"}


def clip(s: str, n: int = SECTION_MAX) -> str:
    s = s or ""
    return s if len(s) <= n else s[: n - 3] + "..."


def strip_mrkdwn(s: str) -> str:
    """Plain-text version for header/fallback: header blocks reject mrkdwn.
    Underscores are only stripped where they act as italic markers, so snake_case identifiers survive."""
    for ch in ("*", "`", "~"):
        s = s.replace(ch, "")
    return re.sub(r"(?<!\w)_|_(?!\w)", "", s)


def build_card(m: Memory) -> List[Dict]:
    """One finding → Block Kit blocks (lifted from the QA poster, layout v2).

    Slack groups consecutive messages from the same app, so each card carries its own title bar
    (header WITH the title) and a trailing divider - without it one card bleeds into the next.
    """
    sev = m.meta.get("severity", "medium")
    icon, label = SEV_ICON.get(sev, "🔬"), SEV_LABEL.get(sev, sev.upper())
    aid = m.meta.get("audit_id", m.id)
    blocks: List[Dict] = [{"type": "header", "text": {"type": "plain_text", "text": clip(strip_mrkdwn(f"{icon} {label} · {aid} — {m.text}"), HEADER_MAX), "emoji": True}}]
    fields = [{"type": "mrkdwn", "text": f"*Severity*\n{icon} {label.title()}"}, {"type": "mrkdwn", "text": f"*Ref*\n`{aid}`"}]
    if m.meta.get("area"):
        fields.append({"type": "mrkdwn", "text": f"*Area*\n{m.meta['area']}"})
    status = m.meta.get("finding_status", "open")
    fields.append({"type": "mrkdwn", "text": f"*Status*\n{status}" + (" ⚠️" if status == "regressed" else "")})
    if m.meta.get("locations"):
        fields.append({"type": "mrkdwn", "text": f"*Location*\n{clip(m.meta['locations'], FIELD_MAX)}"})
    blocks.append({"type": "section", "fields": fields[:10]})
    blocks.append({"type": "divider"})
    if status == "regressed" and m.reason:
        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": clip(f"*Regression*\n{m.reason}")}})
    for lbl, txt in m.details:
        if not txt and not lbl:
            continue
        body = f"*{lbl}*\n{txt}" if lbl else txt
        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": clip(body)}})
    blocks.append({"type": "context", "elements": [{"type": "mrkdwn", "text": ACK}]})
    blocks.append({"type": "divider"})   # closes the card
    return blocks[:50]


def card_fallback_text(m: Memory) -> str:
    sev = m.meta.get("severity", "medium")
    return clip(strip_mrkdwn(f"{SEV_ICON.get(sev, '🔬')} {SEV_LABEL.get(sev, sev.upper())} {m.meta.get('audit_id', m.id)}: {m.text}"), 300)


def build_index(cfg: Config, fs: List[Memory]) -> str:
    from collections import Counter
    from .audit import OPEN_LIKE, NOTE
    open_ = [m for m in fs if m.meta.get("finding_status", "open") in OPEN_LIKE]
    notes = sum(1 for m in fs if m.meta.get("finding_status") == NOTE)
    c = Counter(m.meta.get("severity", "medium") for m in open_)
    top = sorted(open_, key=lambda m: -m.importance)[:2]
    return (f"🐛 *{cfg.paths.root.name} — QA / Security Audit* · `{git_head(cfg.paths.root)}`\n\n"
            f"*{len(open_)} open findings* — " + " · ".join(f"{SEV_ICON[s]} {c[s]} {s}" for s in ("critical", "high", "medium", "low", "info") if c[s])
            + (f" · 🔬 {notes} verification notes" if notes else "") + "\n\n"
            "*Each finding is posted separately below* so it can be owned and acked on its own:\n"
            "• :eyes: — you are picking it up\n• :white_check_mark: — fixed / PR merged\n• :no_entry_sign: — not a bug, or won't fix (say why in thread)\n\n"
            "Every post carries a stable id for cross-referencing in PRs and tickets.\n"
            + ("\n*Ship these first* — " + " · ".join(f"{SEV_ICON[m.meta.get('severity','medium')]} `{m.meta.get('audit_id')}`" for m in top) if top else ""))


def _ssl_ctx():
    """python.org macOS builds ship without a CA bundle; use certifi when present."""
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return None


class SlackClient:
    """Slack Web API over form-encoded POST (lists/dicts JSON-encoded), curl fallback when urllib has no usable CA bundle."""

    def __init__(self, token: Optional[str]):
        self.token = token

    def call(self, method: str, params: Dict, auth: bool = True) -> Dict:
        if auth and not self.token:
            raise SystemExit("SLACK_BOT_TOKEN is not set (scopes: chat:write, reactions:write; channels:history for --convert without --ts).")
        flat = {k: (json.dumps(v) if isinstance(v, (list, dict)) else v) for k, v in params.items()}
        data = urllib.parse.urlencode(flat).encode()
        req = urllib.request.Request(f"https://slack.com/api/{method}", data=data)
        req.add_header("Content-Type", "application/x-www-form-urlencoded; charset=utf-8")
        if auth:
            req.add_header("Authorization", f"Bearer {self.token}")
        try:
            with urllib.request.urlopen(req, timeout=30, context=_ssl_ctx()) as r:
                return json.loads(r.read().decode())
        except Exception:
            if not shutil.which("curl"):
                raise
            cmd = ["curl", "-sS", "-m", "30", "-X", "POST", f"https://slack.com/api/{method}"]
            if auth:
                cmd += ["-H", f"Authorization: Bearer {self.token}"]
            for k, v in flat.items():
                cmd += ["--data-urlencode", f"{k}={v}"]
            pr = subprocess.run(cmd, capture_output=True, text=True)
            if pr.returncode != 0:
                return {"ok": False, "error": f"transport_failed: {pr.stderr.strip()[:200]}"}
            try:
                return json.loads(pr.stdout)
            except Exception:
                return {"ok": False, "error": f"bad_response: {pr.stdout[:200]}"}


def parse_ts(v: str) -> str:
    """Accept a raw ts (1756211400.123456) or a Slack permalink (.../p1756211400123456)."""
    v = (v or "").strip()
    m = re.search(r"/p(\d{10})(\d{6})", v)
    return f"{m.group(1)}.{m.group(2)}" if m else v


def re_marker(marker: str, text: str) -> bool:
    """Exact marker match: QA-1 must not match QA-19 or QA-12."""
    return re.search(rf"{re.escape(marker)}(?![0-9-])", text) is not None


def convert(cfg: Config, fs: List[Memory], channel: str, dry: bool, only: Optional[str], ts_arg: Optional[str], state: "PostState", out=print) -> int:
    """Rewrite ALREADY-POSTED messages in place as cards via chat.update (reactions/threads preserved).

    Messages are located by their audit-id marker; --ts skips conversations.history so a single
    message can be converted with chat:write alone.
    """
    client = SlackClient(os.environ.get("SLACK_BOT_TOKEN"))
    if only:
        fs = [m for m in fs if m.meta.get("audit_id") == only or m.meta.get("audit_id", "").endswith("-" + only)]
        if not fs:
            raise SystemExit(f"no finding {only!r}")
    by_id: Dict[str, str] = {}
    if ts_arg:
        if len(fs) != 1:
            raise SystemExit("--ts requires exactly one finding; add --only <id>")
        by_id[fs[0].meta["audit_id"]] = parse_ts(ts_arg)
    else:
        # known ts from our own state first, then scan history for the rest
        for m in fs:
            rec = state.data["posted"].get(m.meta.get("audit_id", ""), {})
            if rec.get("ts"):
                by_id[m.meta["audit_id"]] = rec["ts"]
        missing = [m for m in fs if m.meta["audit_id"] not in by_id]
        cursor, pages = None, 0
        while missing and pages < 10:
            params = {"channel": channel, "limit": 200}
            if cursor:
                params["cursor"] = cursor
            r = client.call("conversations.history", params)
            if not r.get("ok"):
                _explain(r.get("error", "unknown"), channel)
            for msg in r.get("messages", []):
                txt = msg.get("text") or ""
                for m in missing:
                    if m.meta["audit_id"] not in by_id and re_marker(m.meta["audit_id"], txt):
                        by_id[m.meta["audit_id"]] = msg["ts"]
            cursor = (r.get("response_metadata") or {}).get("next_cursor")
            pages += 1
            if not cursor:
                break
    found = [m for m in fs if m.meta["audit_id"] in by_id]
    not_found = [m.meta["audit_id"] for m in fs if m.meta["audit_id"] not in by_id]
    out(f"matched {len(found)}/{len(fs)} posted messages" + (f"; not found: {', '.join(not_found)}" if not_found else ""))
    if dry:
        for m in found:
            out(f"  would convert {m.meta['audit_id']:<14} ts={by_id[m.meta['audit_id']]} -> {len(build_card(m))} blocks")
        out("dry run — nothing changed. drop --dry to apply.")
        return 0
    n = 0
    for m in found:
        r = client.call("chat.update", {"channel": channel, "ts": by_id[m.meta["audit_id"]], "text": card_fallback_text(m), "blocks": build_card(m)})
        if r.get("ok"):
            state.mark(m.meta["audit_id"], by_id[m.meta["audit_id"]], channel)
            state.save()
            n += 1
            out(f"  ✅ converted {m.meta['audit_id']}")
        else:
            out(f"  ❌ {m.meta['audit_id']}: {r.get('error')}")
        time.sleep(0.35)
    out(f"converted {n} message(s). Reactions and threads preserved.")
    return 0


class PostState:
    """Which audit ids have already been posted (per repo, gitignored)."""

    def __init__(self, path: Path):
        self.path = path
        self.data: Dict = {"note": "audit ids already posted to Slack; delete one to allow reposting", "posted": {}}
        if path.exists():
            try:
                self.data = json.loads(path.read_text())
                if isinstance(self.data.get("posted"), list):          # legacy list format
                    self.data["posted"] = {i: {} for i in self.data["posted"]}
            except Exception:
                pass

    def seed_from(self, legacy: Path, prefix: str) -> int:
        """Import the QA poster's docs/.slack-posted.json (raw ids) so a migration never double-posts."""
        d = json.loads(legacy.read_text())
        n = 0
        for raw in d.get("posted", []):
            aid = raw if str(raw).startswith(prefix) else f"{prefix}-{raw}"
            if aid not in self.data["posted"]:
                self.data["posted"][aid] = {"seeded_from": str(legacy)}
                n += 1
        return n

    def posted(self, aid: str) -> bool:
        return aid in self.data["posted"]

    def mark(self, aid: str, ts: str, channel: str) -> None:
        self.data["posted"][aid] = {"ts": ts, "channel": channel}

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.data, indent=1))


def validate_cards(client: SlackClient, fs: List[Memory]) -> List[str]:
    """blocks.validate for every card. Returns a list of 'AUDIT-ID: error' strings (empty = all valid)."""
    errors = []
    for m in fs:
        resp = client.call("blocks.validate", {"blocks": build_card(m)}, auth=False)
        if not resp.get("ok"):
            errors.append(f"{m.meta.get('audit_id')}: {resp.get('error', 'unknown')} {resp.get('errors', '')}")
    return errors


def publish(cfg: Config, fs: List[Memory], channel: str, send: bool, all_: bool, state: PostState, out=print) -> Dict[str, int]:
    client = SlackClient(os.environ.get("SLACK_BOT_TOKEN"))
    posted = skipped = 0
    reactions_ok = True
    if not state.data["posted"] or all_:
        idx = build_index(cfg, fs)
        if send:
            r = client.call("chat.postMessage", {"channel": channel, "text": idx, "unfurl_links": False, "unfurl_media": False})
            if not r.get("ok"):
                _explain(r.get("error", "unknown"), channel)
        else:
            out("──── index (preview) ────\n" + idx)
    for m in fs:
        aid = m.meta.get("audit_id", m.id)
        if state.posted(aid) and not all_:
            skipped += 1
            continue
        blocks = build_card(m)
        if not send:
            out(f"──── {aid} (preview) ────\n" + "\n".join(b.get("text", {}).get("text", "") if b["type"] in ("section", "header") else "" for b in blocks).strip())
            continue
        r = client.call("chat.postMessage", {"channel": channel, "text": card_fallback_text(m), "blocks": blocks, "unfurl_links": False, "unfurl_media": False})
        if not r.get("ok"):
            _explain(r.get("error", "unknown"), channel)
        ts = r["ts"]
        if reactions_ok:
            for name in REACTIONS:
                rr = client.call("reactions.add", {"channel": channel, "timestamp": ts, "name": name})
                if not rr.get("ok") and rr.get("error") in ("missing_scope", "not_allowed_token_type"):
                    out("note: token lacks reactions:write — posting without pre-seeded acks.")
                    reactions_ok = False
                    break
        state.mark(aid, ts, channel)
        state.save()
        posted += 1
        out(f"posted {aid}")
    return {"posted": posted, "skipped": skipped}


def _explain(err: str, channel: str) -> None:
    hints = {"not_in_channel": f"in Slack run  /invite @YourApp  in {channel}", "missing_scope": "add the missing scope (chat:write / reactions:write / channels:history) and reinstall the app",
             "channel_not_found": f"check --channel {channel}", "invalid_auth": "token is invalid or revoked"}
    raise SystemExit(f"slack error: {err}" + (f"\n  fix: {hints[err]}" if err in hints else ""))
