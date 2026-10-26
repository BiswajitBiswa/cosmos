"""Plain notes: how a fact reads to a person, worked out from what agents wrote, with no model.

Agents tend to pack everything into one sentence: "Connections (step 2a, 2026-10-07): a Connection is …",
"OWNER RULE 2026-09-29 (top priority): …", "Lifecycle · Discover · done · …". Shown as is, the label, the date and the
step become the headline. view() splits a note into a short title, one plain sentence and small chips (date, step,
label, author, phase, status), so the console, Horizon and anything else reading the ledger show the fact first.
The stored text never changes, so ids, links and evidence stay as they are.

lint() is the same knowledge pointed the other way: when a note is written it says, briefly, what would read plainer
next time (a date in the sentence, capitals for emphasis, a sentence that carries three facts).
"""
from __future__ import annotations

import re
from typing import Dict, List, Optional

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
DATE = re.compile(r"\b(20\d\d)-(\d\d)-(\d\d)\b")
# labels that say what kind of note it is or who stated it, not what it is about: they become a chip, never the title
KIND_LABELS = re.compile(r"(?i)^(owner(?:'s)?(?: rules?| decisions?| corrections?| requests?| feedback| asked)?|feature|strict owner rule|owner rules?|"
                         r"team rule|rule|decision|constraint|finding|note|lesson|open risk|risk|correction|fact|update|status|"
                         r"commit note(?: by [^:]{1,40})?|shipped(?: in)?(?: #\d+)?|fixed(?: in)?(?: #\d+)?|safety|important|"
                         r"warning|todo|open question|question|feedback|heads-up)$")
LIFECYCLE = re.compile(r"^\s*Lifecycle\s*·\s*(?P<phase>[^·]{2,30}?)\s*·\s*(?P<status>[^·]{2,20}?)\s*·\s*(?P<rest>.+)$", re.S)
CAPS_LABEL = re.compile(r"^\s*(?P<label>[A-Z][A-Z0-9 &/'-]{2,40}?)(?P<date>\s+20\d\d-\d\d-\d\d)?\s*(?:\((?P<paren>[^)]{1,60})\))?\s*:\s+(?=\S)")
TOPIC_LABEL = re.compile(r"^\s*(?P<label>[A-Za-z][^():\n]{1,60}?)\s*\((?P<paren>[^)]{1,80})\)\s*:\s+(?=\S)")
PLAIN_LABEL = re.compile(r"^\s*(?P<label>[A-Za-z][\w '#&/.-]{1,40}?)(?P<date>\s+20\d\d-\d\d-\d\d)?\s*:\s+(?=\S)")
CAPS_TAG = re.compile(r"^\s*(?P<tag>[A-Z]{3,})\s+(?=[A-Z][a-z])")
ENUM = re.compile(r"^\s*\(?\d{1,2}[).]\s+")
QUOTED = re.compile(r"'[^'\n]{1,80}'|\"[^\"\n]{1,80}\"|`[^`\n]{1,80}`")
ANY_PAREN = re.compile(r"\s*\([^()]*\)")
LEAD_DATE = re.compile(r"^\s*(?:\(?\s*)(20\d\d-\d\d-\d\d)\s*\)?\s*(?:\((?P<paren>[^)]{1,60})\))?\s*[:,·-]\s*")
STEP = re.compile(r"(?i)\bstep\s+([0-9]+[a-z]?)\b")
PR = re.compile(r"#(\d{1,6})\b")
LONG_PAREN = re.compile(r"\s*\([^()]{40,}\)")
CLAUSE = re.compile(r"\s+—\s+|;\s+|:\s+|,\s+(?=(?:so|because|but|which|while|and then|unless|since)\b)|\.\s+(?=[A-Z(`\"'])")
SENTENCE_END = re.compile(r"(?<![A-Z][a-z])(?<!\be\.g)(?<!\bi\.e)(?<!\betc)\.\s+(?=[A-Z(`\"'])")
AI_WORDS = re.compile(r"(?i)\b(leverag\w*|robust|seamless(?:ly)?|utili[sz]\w*|delve|holistic|streamlin\w*|empower\w*|"
                      r"cutting-edge|game-changer|synerg\w*|paradigm|unlock(?:s|ing)? the|in order to|it is important to note)\b")
TITLE_WORDS = 12
LOWER_NAMES = {"cosmos", "npm", "pnpm", "git", "pip", "ios", "macos", "iphone", "ipad", "e.g.", "i.e."}


def human_date(iso: str) -> str:
    m = DATE.search(iso or "")
    return f"{int(m.group(3))} {MONTHS[int(m.group(2)) - 1]} {m.group(1)}" if m else ""


def _cap(s: str) -> str:
    s = s.strip()
    first = s.split(" ", 1)[0] if s else ""
    if first.lower().strip(",.:;") in LOWER_NAMES:
        return s
    if not s or s[:1].isupper() or s.startswith(("`", "/", ".", "(")) or re.search(r"[/_.(=]|[a-z][A-Z]", first):
        return s
    return s[:1].upper() + s[1:]


def _paren_chips(paren: str) -> List[str]:
    """'(step 2a, 2026-10-07)' or '(owner, 2026-10-01)' → chips; a date is dropped here, it has its own chip."""
    out = []
    for part in re.split(r"[,;]\s*", paren or ""):
        part = DATE.sub("", part).strip(" ·-")
        if part and len(part) <= 30:
            out.append(part.lower() if not re.search(r"[A-Z]{2}|#|\d", part) else part)
    return out


def _peel_label(text: str, chips: List[str], found: Dict[str, str]) -> tuple:
    """Strip one leading label ('SAFETY:', 'Owner rule (2026-10-06):', 'Connections (step 2a, …):', 'Shipped #89:').
    Returns (topic or '', rest)."""
    tag = CAPS_TAG.match(text)
    if tag and not CAPS_LABEL.match(text):
        chips.append(tag.group("tag").lower())
        text = text[tag.end():]
    for pat in (CAPS_LABEL, TOPIC_LABEL, PLAIN_LABEL):
        m = pat.match(text)
        if not m:
            continue
        label = m.group("label").strip()
        paren = m.groupdict().get("paren") or ""
        if pat is PLAIN_LABEL and not KIND_LABELS.match(label) and len(label.split()) > 4:
            continue                                   # "Every query is scoped: …" is a sentence, not a label
        if pat is CAPS_LABEL and label.lower() == label:
            continue
        if pat is TOPIC_LABEL and not (DATE.search(paren) or STEP.search(paren) or KIND_LABELS.match(paren.split(",")[0].strip())):
            continue                                   # "(the owner's call)" inside a sentence, not a label
        for d in DATE.findall((m.groupdict().get("date") or "") + " " + paren):
            found.setdefault("date", "-".join(d))
        st = STEP.search(paren)
        if st:
            found.setdefault("step", st.group(1))
        chips += [c for c in _paren_chips(paren) if not STEP.fullmatch(c) and not c.lower().startswith("step")]
        by = re.match(r"(?i)commit note by (.+)$", label)
        if by:
            found.setdefault("author", by.group(1).strip())
            chips.append("commit")
            return "", text[m.end():]
        if KIND_LABELS.match(label) or label.isupper():
            chips.append(label.lower() if label.isupper() else label[:1].lower() + label[1:])
            return "", text[m.end():]
        return label, text[m.end():]
    return "", text


def _mask(text: str) -> tuple:
    """Quoted text ('Think. Build.') held aside so its full stops and colons never split a sentence or a title."""
    held: List[str] = []
    masked = QUOTED.sub(lambda m: held.append(m.group(0)) or f"\x00{len(held) - 1}\x00", text)
    return masked, lambda s: re.sub(r"\x00(\d+)\x00", lambda m: held[int(m.group(1))], s)


def _sentences(text: str) -> List[str]:
    masked, back = _mask(text)
    return [re.sub(r"^[-•*]\s+", "", back(s).strip()) for s in SENTENCE_END.split(masked) if s.strip()]


def _title_from(sentence: str) -> tuple:
    """A headline from the first clause of a sentence: (title, what is left of the sentence)."""
    s, back = _mask(ANY_PAREN.sub("", sentence).strip())
    cut = None
    for m in CLAUSE.finditer(s):
        if len(s[:m.start()].split()) >= 3:
            cut = m
            break
    head, tail = (s[:cut.start()], s[cut.end():]) if cut else (s, "")
    words = head.split()
    if len(words) > TITLE_WORDS:
        head, tail = " ".join(words[:TITLE_WORDS]) + "…", LONG_PAREN.sub("", sentence).strip()
    return _cap(back(head).rstrip(" .,:;—-")), _cap(back(tail).strip())


def view(text: str, meta: Optional[Dict[str, str]] = None, category: str = "") -> Dict:
    """{title, sentence, chips, date, step, author, phase, status} for one note. Pure: same text, same view."""
    meta = meta or {}
    t = " ".join((text or "").split())
    chips: List[str] = []
    found: Dict[str, str] = {}
    out: Dict = {"title": "", "sentence": "", "chips": chips}

    lc = LIFECYCLE.match(t)
    if lc:
        found["phase"], found["status"] = lc.group("phase").strip(), lc.group("status").strip().lower()
        t = lc.group("rest").strip()
    if meta.get("phase"):
        found["phase"], found["status"] = meta["phase"], meta.get("phase_status", found.get("status", ""))

    m = LEAD_DATE.match(t)
    if m:
        found["date"] = m.group(1)
        chips += _paren_chips(m.group("paren") or "")
        t = t[m.end():]
    topic, rest = _peel_label(t, chips, found)
    if found.get("author") and " — " in rest:
        subject, body = rest.split(" — ", 1)
        title, _ = _title_from(subject)
        body_s = _sentences(body)
        found_view = {"title": meta.get("title") or title, "sentence": _clip(body_s[0] if body_s else ""), "chips": chips}
        return _finish(found_view, found, chips)
    if not topic and rest is not t:
        topic, rest = _peel_label(rest, chips, found)
    m = LEAD_DATE.match(rest)
    if m:
        found.setdefault("date", m.group(1))
        rest = rest[m.end():]
    if not found.get("step"):
        st = STEP.search(topic)
        if st:
            found["step"] = st.group(1)
    rest = ENUM.sub("", rest)
    sentences = _sentences(rest)
    first = sentences[0] if sentences else rest
    if meta.get("title"):
        title, remainder = meta["title"].strip(), ""
    elif topic and not lc:
        title, remainder = _cap(topic), ""
    else:
        title, remainder = _title_from(first)
    if remainder and len(remainder.split()) >= 2:
        sentence = remainder
    elif meta.get("title") or (topic and not lc):
        sentence = _cap(LONG_PAREN.sub("", first))
    else:
        sentence = sentences[1] if len(sentences) > 1 else ""
    sentence = _clip(sentence)
    if sentence and sentence.rstrip("…. ").lower() == title.rstrip("…. ").lower():
        sentence = ""
    out["title"] = title or _cap(" ".join(t.split()[:TITLE_WORDS]))
    out["sentence"] = sentence
    return _finish(out, found, chips)


def _clip(sentence: str, n: int = 220) -> str:
    sentence = _cap(sentence or "")
    return sentence[:n].rsplit(" ", 1)[0].rstrip(",;:") + "…" if len(sentence) > n else sentence


def _finish(out: Dict, found: Dict[str, str], chips: List[str]) -> Dict:
    out.update({k: v for k, v in found.items() if v})
    if found.get("date"):
        out["when"] = human_date(found["date"])
    pr = PR.search(" ".join(chips))
    if pr:
        out["pr"] = pr.group(1)
    # one chip per idea: drop chips that only repeat the step, the date or the author
    seen = set()
    out["chips"] = [c for c in chips if c and c.lower() not in seen and not seen.add(c.lower())][:4]
    return out


def lint(text: str) -> List[str]:
    """What would read plainer next time. Short, at most three, never blocks a write."""
    t = " ".join((text or "").split())
    out = []
    head = t[:90]
    if DATE.search(head) or STEP.search(head[:40]):
        out.append("put dates and step numbers in fields (they show as chips), not at the start of the sentence")
    if CAPS_LABEL.match(t) or re.search(r"\b[A-Z]{3,}(?:\s+[A-Z]{3,})+\b", t):
        out.append("no capitals for emphasis; say why it matters in plain words")
    first = _sentences(t)[0] if _sentences(t) else t
    if len(first.split()) > 30:
        out.append(f"the first sentence has {len(first.split())} words: lead with the fact in under 25, details after")
    if t.count(";") >= 2 or len(re.findall(r"\(", t)) >= 3:
        out.append("one fact per note: too many clauses and brackets")
    ai = AI_WORDS.search(t)
    if ai:
        out.append(f"plain words: drop '{ai.group(0)}'")
    return out[:3]


STYLE = ("Write each fact so a person scanning a list gets it at once: a title of at most 8 words in plain language, then one "
         "sentence of under 25 words with the fact and where it lives, then why. No dates, step numbers, IDs or labels like "
         "'Owner rule' or 'SAFETY' in the sentence (they are stored as fields), no capitals for emphasis, no stacked brackets "
         "or semicolons, no words like leverage, robust or seamless.")
