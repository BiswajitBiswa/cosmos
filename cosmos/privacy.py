"""Secret redaction and path filtering. Runs before anything is persisted."""
from __future__ import annotations

import fnmatch
import re
from typing import Iterable, List, Tuple

# (name, pattern). Ordered: specific first.
SECRET_PATTERNS: List[Tuple[str, re.Pattern]] = [
    ("pem_block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----", re.S)),
    ("aws_access_key", re.compile(r"\b(AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("anthropic_key", re.compile(r"\bsk-ant-[A-Za-z0-9_\-]{20,}\b")),
    ("openai_key", re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_\-]{20,}\b")),
    ("github_token", re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr|github_pat)_[A-Za-z0-9_]{20,}\b")),
    ("slack_token", re.compile(r"\b(?:xox[abeoprs]-[A-Za-z0-9\-]{10,}|xapp-[A-Za-z0-9\-]{10,})\b")),
    ("google_api_key", re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b")),
    ("jwt", re.compile(r"\beyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\b")),
    ("bearer", re.compile(r"(?i)\b(bearer|token)\s+[A-Za-z0-9_\-\.=]{16,}")),
    ("url_credentials", re.compile(r"(?i)\b[a-z][a-z0-9+\-.]*://[^\s/:@]+:[^\s/@]+@")),
    ("kv_secret", re.compile(r"(?i)\b(password|passwd|pwd|secret|api[_\-]?key|access[_\-]?token|auth[_\-]?token|client[_\-]?secret|private[_\-]?key)\b\s*[:=]\s*[\"']?[^\s\"',;]{6,}")),
    ("long_base64", re.compile(r"\b[A-Za-z0-9+/]{48,}={0,2}\b")),
]


def redact(text: str) -> Tuple[str, List[str]]:
    """Return (redacted_text, [pattern names that fired])."""
    fired: List[str] = []
    for name, pat in SECRET_PATTERNS:
        def _sub(m: re.Match) -> str:
            if name == "kv_secret":
                # keep the key name, drop the value
                head = re.split(r"[:=]", m.group(0), maxsplit=1)[0]
                return f"{head}=[REDACTED:{name}]"
            if name == "bearer":
                return f"{m.group(1)} [REDACTED:{name}]"
            return f"[REDACTED:{name}]"
        text, n = pat.subn(_sub, text)
        if n:
            fired.append(name)
    return text, fired


def path_ignored(path: str, globs: Iterable[str]) -> bool:
    p = path.replace("\\", "/")
    for g in globs:
        if fnmatch.fnmatch(p, g) or fnmatch.fnmatch(p.split("/")[-1], g):
            return True
        # allow "dir/**" to match anything under dir
        if g.endswith("/**") and (p.startswith(g[:-3] + "/") or ("/" + g[:-3] + "/") in p):
            return True
    return False
