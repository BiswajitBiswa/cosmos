"""Deterministic observation extraction. No LLM required.

An observation is a sentence-level candidate memory scored on importance,
specificity and durability. Only high-signal, concrete, durable statements survive.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from .transcript import Turn

CATEGORIES = ["architecture", "decision", "convention", "constraint", "bug", "dependency", "workflow", "domain", "rejected", "finding"]

# (regex, weight, category hint)
SIGNALS: List[Tuple[re.Pattern, float, Optional[str]]] = [
    (re.compile(r"\b(must|never|always|should not|shouldn't|do not|don't|forbidden|required to)\b", re.I), 0.55, "constraint"),
    (re.compile(r"\b(convention|naming|style|pattern is|we prefix|we suffix|all .{1,40} (return|throw|use))\b", re.I), 0.5, "convention"),
    (re.compile(r"\b(decided|we chose|chose .{1,30} (over|instead of|rather than)|instead of|rather than|(is|are) used (for|as|to)|we use .{1,40} for|went with)\b", re.I), 0.55, "decision"),
    (re.compile(r"\b(owns|is responsible for|talks to|calls into|entry ?point|lives in|boundary|layer|service .{1,30} (reads|writes))\b", re.I), 0.5, "architecture"),
    (re.compile(r"\b(root cause|caused by|race condition|regression|breaks when|fails when|bug is|the fix is|workaround)\b", re.I), 0.55, "bug"),
    (re.compile(r"\b(version \d|v\d+(\.\d+)+|pinned|incompatible|requires .{1,30}(>=|<=|==|\d)|upgrade|downgrade|breaks .{1,20} build)\b", re.I), 0.55, "dependency"),
    (re.compile(r"\b(run .{1,60} (before|first|after)|requires? .{1,40} (running|to be running)|docker compose|make [a-z\-]+|npm run|pytest|gradle|from the .{1,20} directory|working directory)\b", re.I), 0.5, "workflow"),
    (re.compile(r"\b(is considered|counts as|means that|is defined as|business rule|a .{1,25} is active|billing|tenant|customer)\b", re.I), 0.45, "domain"),
    (re.compile(r"\b(rejected|don't use|do not use|avoid .{1,30} because|was rejected because|not viable)\b", re.I), 0.5, "rejected"),
    (re.compile(r"\b(because|since|the reason|so that|otherwise)\b", re.I), 0.2, None),
]

NOISE = [
    re.compile(r"^(let me|i'll|i will|i'm going to|now i|now let|next,? i|first,? i|looking at|i see|i can see|i found|i notice|opening|reading|running|checking|let's|okay|ok,|sure|great|done|here('s| is)|the (file|output) shows)", re.I),
    re.compile(r"\?\s*$"),
    re.compile(r"[:;,\-—]\s*$"),                                   # lead-in to a list
    re.compile(r"\|.*\|"),                                          # markdown table row
    re.compile(r"^(yes|no|correct|right|exactly|note|alternatively|but|then|so|also|and|or|that should|verified|covers|part \d|the finding|if you|two|three|four|five|six|several|a few|one more|another)\b", re.I),
    re.compile(r"\b(this turn|this session|for now|temporarily|as a test|try(ing)? this|let's see|mid-check|worth (a look|your attention)|as requested|per your)\b", re.I),
    re.compile(r"\b(diagram|canvas|screenshot|render(s|ed|ing)?|colou?r coding|slide|pdf|confluence page|zoom(ed)?)\b", re.I),   # artefacts of the conversation
]
SECOND_PERSON = re.compile(r"\b(you|your|you're|yours|you'll|you've)\b", re.I)
SESSION_PAST = re.compile(r"\b(was|were|got|has been|have been|is now|are now|already) (rejected|deleted|merged|pushed|touched|changed|added|removed|fixed|verified|committed|in|done)\b", re.I)

# something concrete to anchor the fact
SPECIFIC = re.compile(r"(`[^`]+`|[\w\-/]+\.(py|ts|tsx|js|kt|java|go|rs|rb|md|json|ya?ml|toml|sql|sh)\b|\b[A-Z][a-z]+[A-Z]\w+\b|\b\w+_\w+\b|\b(Redis|Postgres|PostgreSQL|Kafka|Snowflake|ClickHouse|Mongo\w*|Docker|Kubernetes|Stripe|Authentik|GraphQL|gRPC|REST|S3|SQS|Lambda)\b|/[\w\-]+/[\w\-]+)")

EXPLICIT_RULE = re.compile(r"^\s*(remember|cosmos|rule|convention|note to memory|finding|flare)\s*:\s*(.+)$", re.I | re.S)
IMPERATIVE_RULE = re.compile(r"^\s*(always|never|do not|don't|from now on|going forward)\b", re.I)

MAX_LEN = 320
MIN_LEN = 35


@dataclass
class Observation:
    text: str
    category: str
    score: float
    source: str                 # observed | explicit
    files: List[str] = field(default_factory=list)
    signals: List[str] = field(default_factory=list)
    turn_uuid: str = ""

    def to_dict(self) -> Dict:
        return {"text": self.text, "category": self.category, "score": round(self.score, 3), "source": self.source,
                "files": self.files, "signals": self.signals, "turn_uuid": self.turn_uuid}


_CODE_BLOCK = re.compile(r"```.*?```", re.S)
_INLINE_LINK = re.compile(r"\[([^\]]+)\]\([^)]+\)")
_MD_NOISE = re.compile(r"^\s{0,3}(#{1,6}\s+|[-*+]\s+|\d+\.\s+|>\s*)", re.M)


def clean_markdown(text: str) -> str:
    text = _CODE_BLOCK.sub(" ", text)
    text = _INLINE_LINK.sub(r"\1", text)
    text = _MD_NOISE.sub("", text)
    text = text.replace("**", "").replace("__", "")
    return text


def split_sentences(text: str) -> List[str]:
    out: List[str] = []
    for para in re.split(r"\n\s*\n|\n(?=[A-Z0-9])", text):
        para = " ".join(para.split())
        if not para:
            continue
        # split on sentence end not inside backticks (approximation: backtick count even so far)
        parts = re.split(r"(?<=[.!?])\s+(?=[A-Z`\"'(])", para)
        out.extend(p.strip() for p in parts if p.strip())
    return out


def classify(sentence: str) -> Tuple[float, Optional[str], List[str]]:
    score = 0.0
    cat: Optional[str] = None
    best = 0.0
    names: List[str] = []
    for pat, w, hint in SIGNALS:
        if pat.search(sentence):
            score += w
            names.append(pat.pattern[:24])
            if hint and w > best:
                best, cat = w, hint
    return min(score, 1.0), cat, names


def extract_from_turn(turn: Turn, prev_files: Optional[List[str]] = None, min_score: float = 0.5) -> List[Observation]:
    obs: List[Observation] = []
    files = list(dict.fromkeys((turn.files or []) + (prev_files or [])))[:6]

    if turn.role == "user":
        files = list(turn.files or [])
        raw = turn.text.strip()
        m = EXPLICIT_RULE.match(raw)
        if m:
            body = " ".join(m.group(2).split())[:MAX_LEN]
            if len(body) >= 8:
                _, cat, sig = classify(body)
                if m.group(1).lower() in ("finding", "flare"):
                    cat = "finding"
                obs.append(Observation(body, cat or "convention", 0.95, "explicit", files, sig, turn.uuid))
            return obs
        if len(raw) > 1200 or "<" in raw and ">" in raw:
            return obs    # a pasted document / injected tool text, not a developer stating a rule
        for s in split_sentences(clean_markdown(raw)):
            if IMPERATIVE_RULE.match(s) and MIN_LEN <= len(s) <= MAX_LEN:
                _, cat, sig = classify(s)
                obs.append(Observation(s, cat or "convention", 0.85, "explicit", files, sig, turn.uuid))
        return obs

    for s in split_sentences(clean_markdown(turn.text)):
        if not (MIN_LEN <= len(s) <= MAX_LEN):
            continue
        if any(n.search(s) for n in NOISE):
            continue
        base, cat, sig = classify(s)
        if base <= 0 or cat is None:
            continue
        specific = 1.0 if (SPECIFIC.search(s) or turn.files) else 0.4
        # narration about the conversation or the session is low durability
        durability = 1.0
        if re.search(r"\b(I|I've|I'm|my)\b", s):
            durability *= 0.6
        if SECOND_PERSON.search(s):
            durability *= 0.6
        if SESSION_PAST.search(s):
            durability *= 0.7
        score = base * specific * durability
        if score >= min_score:
            obs.append(Observation(s, cat, score, "observed", files, sig, turn.uuid))
    return obs


def extract(turns: List[Turn], min_score: float = 0.5, max_per_batch: int = 40) -> List[Observation]:
    out: List[Observation] = []
    prev_files: List[str] = []
    for t in turns:
        out.extend(extract_from_turn(t, prev_files, min_score))
        if t.files:
            prev_files = t.files
    explicit = [o for o in out if o.source == "explicit"]
    observed = sorted((o for o in out if o.source != "explicit"), key=lambda o: -o.score)[:max_per_batch]
    keep = {id(o) for o in explicit + observed}
    return [o for o in out if id(o) in keep]
