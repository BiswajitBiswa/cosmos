"""Security checks for code written with AI agents, standard library only.

Three kinds of finding, each with its file and line:

- secret: a real credential in a file (high-precision patterns only: provider keys, tokens, private keys, credentials
  in a URL). The broad patterns cosmos uses to redact transcripts would flag ordinary code, so they are left out here.
- hidden: invisible or bidirectional Unicode (zero-width characters, bidi overrides, tag characters). In code it can
  make a line read differently than it runs; in an instruction file it can carry orders a person never sees.
- instruction: text in a file agents read as instructions (CLAUDE.md, AGENTS.md, rules, playbooks, commands, skills,
  the ledger) that tries to steer an agent: ignore previous instructions, a new system prompt, piping a download into a
  shell, keeping something from the user. cosmos puts these files in front of every agent, so a poisoned one reaches
  every session.

The Gate runs them on the files a turn edited; `cosmos scan` runs them on the repository, and with --tools also the
scanners that are installed (bandit, pip-audit, npm audit, semgrep, gitleaks). Ledger notes that read like
instructions are withheld from what agents are shown until a person looks at them.
"""
from __future__ import annotations

import fnmatch
import re
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from .privacy import SECRET_PATTERNS

HIGH_PRECISION = {"pem_block", "aws_access_key", "anthropic_key", "openai_key", "pypi_token", "npm_token", "github_token",
                  "slack_token", "google_api_key", "jwt", "url_credentials"}
# bidi overrides and isolates (Trojan Source), tag characters (hidden prompt text), zero-width space / non-joiner and
# word joiners. Not the zero-width joiner of emoji sequences, the marks of RTL text, or a byte-order mark.
HIDDEN = re.compile("[\u200b\u200c\u202a-\u202e\u2060-\u2064\u2066-\u2069\U000e0000-\U000e007f]", re.S)
INSTRUCTION = re.compile(
    r"(?i)\b(ignore|disregard|forget)\s+(all\s+|any\s+|the\s+|your\s+)*(previous|prior|above|earlier|other)\s+(instructions|rules|prompts?|guidelines)"
    r"|\byou are now\b(?!\s+(in|on|at)\b)"
    r"|\b(new|hidden|real|override)\s+system\s+prompt\b"
    r"|\bdo\s+not\s+(tell|inform|show|mention\s+(this\s+)?to)\s+the\s+user\b"
    r"|\b(curl|wget)\s+[^|\n]{1,200}\|\s*(sudo\s+)?(ba|z)?sh\b")
INSTRUCTION_FILES = ["CLAUDE.md", "AGENTS.md", "GEMINI.md", ".cursorrules", ".windsurfrules", ".clinerules", ".idx/airules.md",
                     ".github/copilot-instructions.md", ".cursor/rules/*", ".claude/commands/*", ".claude/skills/*", ".agents/skills/*",
                     ".gemini/commands/*", ".cursor/commands/*", ".github/prompts/*", ".windsurf/workflows/*", ".cosmos/*",
                     "plugin/commands/*", "plugin/skills/*"]
MANIFESTS = {
    "python": (["requirements*.txt", "pyproject.toml", "Pipfile", "Pipfile.lock", "poetry.lock", "uv.lock", "setup.py", "setup.cfg"],
               ["pip-audit", "pip_audit", "safety"], "python3 -m pip_audit (install once: python3 -m pip install pip-audit)"),
    "javascript": (["package.json", "package-lock.json", "pnpm-lock.yaml", "yarn.lock", "bun.lockb"],
                   ["npm audit", "pnpm audit", "yarn audit", "yarn npm audit", "bun audit"], "npm audit --omit=dev (in the folder with that package.json)"),
    "go": (["go.mod", "go.sum"], ["govulncheck"], "govulncheck ./... (install once: go install golang.org/x/vuln/cmd/govulncheck@latest)"),
    "rust": (["Cargo.toml", "Cargo.lock"], ["cargo audit"], "cargo audit (install once: cargo install cargo-audit)"),
    "ruby": (["Gemfile", "Gemfile.lock"], ["bundle audit", "bundler-audit"], "bundle audit check --update"),
}
MAX_BYTES = 1_000_000


def _match(rel: str, globs: Iterable[str]) -> bool:
    name = rel.rsplit("/", 1)[-1]
    return any(fnmatch.fnmatch(rel, g) or fnmatch.fnmatch(name, g) or (g.endswith("/*") and rel.startswith(g[:-1])) for g in globs)


def is_instruction_file(rel: str) -> bool:
    if rel.startswith(".cosmos/vendor/"):
        return False                                   # cosmos's own source, which describes these patterns
    return _match(rel, INSTRUCTION_FILES) or "/skills/" in rel and rel.endswith("SKILL.md") or rel.startswith(".cosmos/playbooks/")


def _line(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


PLACEHOLDER = re.compile(r"(?i)example|placeholder|dummy|fake|sample|x{4,}|\*{3,}|<[^>]+>|://[^:/\s]+:(pass|password|secret|changeme|\*+)@")
LOCAL_URL = re.compile(r"(?i)@(localhost|127\.0\.0\.1|0\.0\.0\.0|\[::1\]|host\.docker\.internal|[a-z][a-z0-9_-]*)(:\d+)?(/|$|\s|\?)")   # local, or a docker-compose service: not a credential anyone can use
ALLOW = "cosmos: allow-secret"                         # on the line: a documented fixture, not a credential


def secrets(text: str) -> List[Dict]:
    out, spans = [], []
    lines = text.split("\n")
    for name, pat in SECRET_PATTERNS:
        if name not in HIGH_PRECISION:
            continue
        for m in pat.finditer(text):
            n = _line(text, m.start())
            if PLACEHOLDER.search(m.group(0)) or ALLOW in lines[n - 1]:
                continue
            if name == "url_credentials" and LOCAL_URL.match(text, m.end() - 1):
                continue
            if any(a < m.end() and m.start() < b for a, b in spans):
                continue                               # the same value under a broader pattern (an Anthropic key is also sk-…)
            spans.append((m.start(), m.end()))
            out.append({"kind": "secret", "what": name, "line": n})
    return out


def hidden(text: str) -> List[Dict]:
    return [{"kind": "hidden", "what": f"U+{ord(m.group(0)):04X}", "line": _line(text, m.start())} for m in HIDDEN.finditer(text)][:5]


def instruction_like(text: str) -> List[Dict]:
    return [{"kind": "instruction", "what": " ".join(m.group(0).split())[:60], "line": _line(text, m.start())} for m in INSTRUCTION.finditer(text)][:5]


def scan_text(rel: str, text: str) -> List[Dict]:
    found = secrets(text) + hidden(text)
    if is_instruction_file(rel):
        found += instruction_like(text)
    return [dict(f, file=rel) for f in found]


def scan_file(root: Path, rel: str) -> List[Dict]:
    p = root / rel
    try:
        if not p.is_file() or p.stat().st_size > MAX_BYTES:
            return []
        data = p.read_bytes()
    except OSError:
        return []
    if b"\x00" in data[:4096]:
        return []                                      # binary
    return scan_text(rel, data.decode("utf-8", errors="ignore"))


def describe(f: Dict) -> str:
    why = {"secret": "a credential in the file: remove it, rotate it, read it from the environment",
           "hidden": "invisible or bidirectional Unicode: delete it unless it is meant to be there",
           "instruction": "text that steers an agent, in a file agents read as instructions: remove it or say why it belongs"}[f["kind"]]
    return f"`{f['file']}:{f['line']}` {f['what']} ({why})"


def audits_needed(edited: Iterable[str], commands: List[str]) -> List[str]:
    """A dependency manifest changed this turn and no audit ran: the audit to run, once per ecosystem."""
    out = []
    for eco, (globs, patterns, command) in MANIFESTS.items():
        if any(_match(f, globs) for f in edited) and not any(p in c for c in commands for p in patterns):
            out.append(f"{eco}: `{command}`")
    return out


# ---------------------------------------------------------------- the repository
def tracked(root: Path) -> List[str]:
    try:
        out = subprocess.run(["git", "ls-files", "-z"], cwd=root, capture_output=True, timeout=30)
        return [f for f in out.stdout.decode(errors="ignore").split("\0") if f]
    except (OSError, subprocess.SubprocessError):
        return []


TOOLS = [("bandit", ["bandit", "-q", "-ll", "-r", ".", "-x", "./.venv,./venv,./node_modules,./.cosmos"], "python3 -m pip install bandit"),
         ("pip-audit", ["pip-audit"], "python3 -m pip install pip-audit"),
         ("npm audit", ["npm", "audit", "--omit=dev"], "comes with npm"),
         ("semgrep", ["semgrep", "scan", "--config", "p/default", "--error", "--quiet"], "python3 -m pip install semgrep"),
         ("gitleaks", ["gitleaks", "detect", "--no-banner", "--redact"], "brew install gitleaks")]


def run_tools(root: Path) -> List[Dict[str, str]]:
    out = []
    for name, cmd, how in TOOLS:
        if name == "npm audit" and not (root / "package.json").exists():
            continue
        if name == "pip-audit" and not any((root / f).exists() for f in ("requirements.txt", "pyproject.toml")):
            continue
        if not shutil.which(cmd[0]):
            out.append({"tool": name, "result": f"not installed ({how})"})
            continue
        try:
            r = subprocess.run(cmd, cwd=root, capture_output=True, text=True, timeout=600)
            tail = (r.stdout or r.stderr).strip().splitlines()[-1:] or ["no output"]
            out.append({"tool": name, "result": ("clean" if r.returncode == 0 else "findings") + f" · {tail[0][:160]}"})
        except (OSError, subprocess.SubprocessError) as e:
            out.append({"tool": name, "result": f"did not finish: {e}"})
    return out


def scan_repository(root: Path, with_tools: bool = False) -> Dict:
    findings: List[Dict] = []
    files = tracked(root)
    for rel in files:
        findings += scan_file(root, rel)
    rep = {"files": len(files), "findings": findings}
    if with_tools:
        rep["tools"] = run_tools(root)
    return rep


def withheld(text: str, meta: Optional[Dict] = None) -> Optional[str]:
    """A ledger note that reads like orders to an agent, or hides characters: why it is withheld, or None. A person
    allows one on purpose (a quoted prompt-injection test case) with `cosmos scan --allow <id>`."""
    if meta and meta.get("security_allowed"):
        return None
    if HIDDEN.search(text):
        return "hidden characters"
    if INSTRUCTION.search(text):
        return "reads like instructions to an agent"
    return None
