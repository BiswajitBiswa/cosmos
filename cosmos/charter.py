"""Charter: the one coding style and working agreement, written once, injected into every AI session on every machine.

`.cosmos/charter.md` is hand-written prose (committed, reviewed in PRs) plus a small `gate:` block that configures the Gate.
Explicit rules typed as `remember:` land in the ledger and are shown next to the charter.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List

from .config import Config
from .store import Memory

TEMPLATE = """---
gate: {"enabled": true, "require_tests": true, "require_refs": true, "test_patterns": ["pytest", "npm test", "npm run test", "pnpm test", "yarn test", "go test", "gradle test", "gradlew test", "mvn test", "cargo test", "jest", "vitest", "make test", "./manage.py test"], "code_globs": ["**/*.py", "**/*.ts", "**/*.tsx", "**/*.js", "**/*.kt", "**/*.java", "**/*.go", "**/*.rs", "**/*.rb"], "skip_globs": ["**/*.md", "**/*.json", "**/*.yml", "**/*.yaml", "docs/**", ".cosmos/**"]}
---

# Charter

The working agreement for this repository. Every AI session on every machine reads this first.
Edit it in a pull request; do not tell your own AI a different style.

## How we write code
- Follow the existing style of the file you are in before any personal preference.
- Small, named functions; no clever one-liners that need a comment to decode.
- Errors are handled where they can be acted on; never swallowed silently.

## How we test
- A change to behaviour comes with a test in the same change.
- Run the tests that cover the files you touched before you stop.

## How we point at things
- Refer to code as `path/to/file.py:123`, never "the function above".
- Every claim about the codebase names the file it was verified in.

## How we review our own work
- Before finishing: re-read the diff, check it against this charter, and state what was NOT tested.
- Open findings on the files you touched are addressed or explicitly deferred with a reason.

## Architecture rules
- Add rules here as decisions are made (or type `remember: …` in a session; explicit rules outrank inferred ones).
"""


def path(cfg: Config) -> Path:
    return cfg.paths.cosmos / "charter.md"


def ensure(cfg: Config) -> Path:
    p = path(cfg)
    if not p.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(TEMPLATE)
    return p


def read(cfg: Config) -> str:
    p = path(cfg)
    return p.read_text() if p.exists() else ""


def body(cfg: Config) -> str:
    """Charter prose without the frontmatter."""
    txt = read(cfg)
    m = re.match(r"^---\n.*?\n---\n(.*)$", txt, re.S)
    return (m.group(1) if m else txt).strip()


def gate_config(cfg: Config) -> Dict[str, Any]:
    default = json.loads(re.search(r"gate: (\{.*\})", TEMPLATE).group(1))
    txt = read(cfg)
    m = re.search(r"^gate:\s*(\{.*\})\s*$", txt, re.M)
    if m:
        try:
            default.update(json.loads(m.group(1)))
        except Exception:
            pass
    default.update(cfg.get("gate", {}) or {})
    return default


def rules(mems: Dict[str, Memory]) -> List[Memory]:
    """Explicit developer rules (remember: …) that belong beside the charter."""
    out = [m for m in mems.values() if m.source == "explicit" and m.status == "active" and m.category in ("convention", "constraint", "architecture", "workflow")]
    out.sort(key=lambda m: (m.category, m.created))
    return out


def summary(cfg: Config, mems: Dict[str, Memory], max_lines: int = 28) -> str:
    """Compact charter for injection: headings + bullets, then explicit rules."""
    lines = []
    for ln in body(cfg).splitlines():
        if ln.startswith("#") or ln.startswith("- "):
            lines.append(ln.strip())
    lines = lines[:max_lines]
    rs = rules(mems)
    if rs:
        lines.append("## Explicit team rules")
        lines += [f"- [{m.category}] {m.text}" for m in rs[:12]]
    return "\n".join(lines)


def add_section_rule(cfg: Config, text: str, section: str = "Architecture rules") -> Path:
    p = ensure(cfg)
    txt = p.read_text()
    marker = f"## {section}"
    if marker not in txt:
        txt = txt.rstrip("\n") + f"\n\n{marker}\n"
    head, _, tail = txt.partition(marker)
    tail_lines = tail.split("\n")
    # append after the last bullet of this section (before the next heading)
    idx = len(tail_lines)
    for i, ln in enumerate(tail_lines[1:], 1):
        if ln.startswith("## "):
            idx = i
            break
    tail_lines.insert(idx, f"- {text}")
    p.write_text(head + marker + "\n".join(tail_lines))
    return p
