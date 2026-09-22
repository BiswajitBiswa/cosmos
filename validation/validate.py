#!/usr/bin/env python3
"""Independent validation of cosmos with a decision model that does not write prose.

Why this exists: the model that builds the ledger (Claude) is also the model that, left to itself, would grade it.
This harness asks a *different* kind of model - TypeSafe's Jev, a System One model that only returns typed answers
with calibrated probabilities - a fixed set of questions about what cosmos actually produced in a repository, and
compares the answers with what cosmos decided. Nothing here is generated; every question has a closed answer set.

    python3 validation/validate.py --repo /path/to/repo --dry-run          # build the cases, count them, estimate cost
    TYPESAFE_API_KEY=… python3 validation/validate.py --repo /path/to/repo   # run, write validation/REPORT.md
    CLOUDFLARE_ACCOUNT_ID=… CLOUDFLARE_API_TOKEN=… python3 validation/validate.py --judge cloudflare --repo …
    python3 validation/validate.py --repo … --export cases.jsonl             # hand the same cases to a human

The report holds aggregates only. Evidence excerpts and fact texts stay on the machine that ran it.
Standard library only, like cosmos itself.
"""
from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
import time
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from cosmos.config import load_config                      # noqa: E402
from cosmos.store import Ledger, Observations, State, make_id  # noqa: E402
from cosmos.retrieve import retrieve, tokens                # noqa: E402
from cosmos.dream import _evidence_excerpt, jaccard         # noqa: E402

NEW_FEATURES = {"handoff", "sources", "reader", "journal", "watch", "sync", "eval", "verdicts-aging", "proportional-gate", "pretooluse-recall", "freshness"}

# ---------------------------------------------------------------- questions (closed answer sets, no prose)
Q_SUPPORT = {"type": "choice", "instructions": "Does the EVIDENCE (excerpts of the files the fact cites, as they are today) support the FACT?",
             "criteria": {"supports": "the evidence shows the fact is true as written, or true with a trivial difference",
                          "contradicts": "the evidence shows the fact is not true as written",
                          "says_nothing": "the evidence does not bear on the fact either way"}}
Q_DURABLE = {"type": "score", "instructions": "How durable is this statement as knowledge for a software team?",
             "criteria": ["narration of one session, progress or status, or something about the AI tool itself",
                          "a one-off detail unlikely to matter next month",
                          "useful for a while, but likely to change soon",
                          "a durable fact about the codebase, a decision with its reason, a constraint or a convention",
                          "a hard rule or constraint a new developer must know on day one"]}
Q_KEEP = {"type": "noul", "instructions": "Should this observation be kept as team knowledge?",
          "criteria": {"true": "it states something durable and specific about the codebase, a decision, a constraint or a convention",
                       "false": "it is narration, task status, a question, speculation, generic advice, or about the AI tool"}}
Q_STALE = {"type": "choice", "instructions": "Given the EVIDENCE as it is today, is the FACT still true?",
           "criteria": {"still_true": "the evidence supports the fact", "outdated": "the evidence shows the fact no longer holds",
                        "unclear": "the evidence cannot decide, for example the file is missing"}}
Q_RELEVANT = {"type": "noul", "instructions": "Would this fact be relevant to a developer doing the TASK?",
              "criteria": {"true": "the fact bears on the file or question in the task", "false": "the fact is about something else"}}
Q_HANDOFF = {"type": "score", "instructions": "Could another developer continue the work on this branch from this handoff alone?",
             "criteria": ["no: it is noise or says nothing about the work", "barely: it names the area but not the state",
                          "partly: what was done is clear, what is open is not", "mostly: done, open and next are clear enough to start",
                          "fully: a colleague could pick it up without asking anything"]}
Q_CLAIM = {"type": "choice", "instructions": "Does the SOURCE CODE implement the CLAIM made in the documentation?",
           "criteria": {"implemented": "the code does what the claim says", "contradicted": "the code does something different from the claim",
                        "cannot_tell": "the excerpt is not enough to decide"}}
Q_JOURNAL = {"type": "noul", "instructions": "Is the JOURNAL LINE an accurate one-line record of the TURN (what was asked, files edited, commits)?",
             "criteria": {"true": "it matches the turn", "false": "it misstates or invents something"}}


def _cut(s: str, n: int) -> str:
    s = " ".join(str(s).split())
    return s if len(s) <= n else s[:n] + " …"


# ---------------------------------------------------------------- cases
def build_cases(root: Path, sample: int, seed: int) -> List[Dict[str, Any]]:
    random.seed(seed)
    cfg = load_config(root)
    mems = Ledger(cfg.paths).load()
    state = State(cfg.paths)
    obs = list(Observations(cfg.paths).iter_all())
    cases: List[Dict[str, Any]] = []
    active = [m for m in mems.values() if m.status == "active" and m.category != "finding"]

    # 1. facts vs their evidence (existing: ledger)
    with_files = [m for m in active if m.files and any((root / f).is_file() for f in m.files)]
    for m in random.sample(with_files, min(sample, len(with_files))):
        cases.append({"suite": "facts-vs-evidence", "feature": "ledger", "new": m.meta.get("verified", "").startswith("llm") or "model" in " ".join(m.tags),
                      "ref": m.id, "cosmos_says": "active",
                      "state": {"FACT": m.text, "EVIDENCE": _evidence_excerpt(root, m, 2200)},
                      "questions": {"support": Q_SUPPORT, "durable": Q_DURABLE}})

    # 2. curation agreement: observations cosmos kept vs dropped (new: model curation / reader)
    dreamed = [o for o in obs if o.get("kind") not in ("journal",) and o.get("id") and state.is_dreamed(o["id"]) and len(o.get("text", "")) > 20]
    index = [(tokens(m.text), m) for m in mems.values()]
    def kept(o):
        t = " ".join(o["text"].split()); tk = tokens(t)
        return any(jaccard(tk, mt) >= 0.6 or m.text == t for mt, m in index)
    for o in random.sample(dreamed, min(sample, len(dreamed))):
        cases.append({"suite": "curation", "feature": "reader" if o.get("event") == "read" else "dream", "new": o.get("event") in ("read", "git", "review", "auto-memory"),
                      "ref": o["id"], "cosmos_says": "kept" if kept(o) else "dropped",
                      "state": {"OBSERVATION": o["text"], "SOURCE": o.get("source", ""), "FILES": (o.get("files") or [])[:4]},
                      "questions": {"keep": Q_KEEP, "durable": Q_DURABLE}})

    # 3. staleness verdicts (new: freshness)
    judged = [m for m in mems.values() if m.category != "finding" and (m.status == "stale-candidate" or m.meta.get("verified", "").startswith("llm")
              or (m.status == "forgotten" and "outdated" in (m.reason or "")) or (m.reason or "").startswith("Evidence verified again"))]
    judged = [m for m in judged if m.files]
    for m in random.sample(judged, min(sample, len(judged))):
        says = "outdated" if m.status == "forgotten" else ("unclear" if m.status == "stale-candidate" else "still_true")
        cases.append({"suite": "freshness", "feature": "freshness", "new": True, "ref": m.id, "cosmos_says": says,
                      "state": {"FACT": m.text, "COSMOS_DOUBT": _cut(m.reason or "", 200), "EVIDENCE": _evidence_excerpt(root, m, 2200)},
                      "questions": {"stale": Q_STALE}})

    # 4. recall precision (existing retrieval + new eval questions)
    cands = []
    for m in active:
        if m.files:
            cands.append((m, m.files[0].rsplit("/", 1)[-1], [m.files[0]], "file"))
        if m.meta.get("eval_q"):
            cands.append((m, m.meta["eval_q"], [], "question"))
    for m, q, paths, kind in random.sample(cands, min(sample, len(cands))):
        got = retrieve(mems, q, paths=paths or None, k=5)
        for r in got[:3]:
            cases.append({"suite": "recall-precision", "feature": "eval" if kind == "question" else "ledger", "new": kind == "question",
                          "ref": f"{m.id}<-{r.id}", "cosmos_says": "retrieved",
                          "state": {"TASK": (f"working on the file {paths[0]}" if paths else q), "FACT": r.text, "FACT_FILES": r.files[:3]},
                          "questions": {"relevant": Q_RELEVANT}})

    # 5. handoffs (new)
    hdir = cfg.paths.ledger / "journal" / "handoffs"
    if hdir.exists():
        for p in sorted(hdir.glob("*.md"))[:sample]:
            md = p.read_text(); body = md[md.find("\n---", 3) + 4:].strip()
            cases.append({"suite": "handoff", "feature": "handoff", "new": True, "ref": p.stem, "cosmos_says": "kept",
                          "state": {"BRANCH": p.stem, "HANDOFF": _cut(body, 1500)}, "questions": {"usable": Q_HANDOFF}})

    # 6. journal lines vs the turn they summarise (new) - only where the transcript is still on disk
    journal = [o for o in obs if o.get("kind") == "journal" and o.get("event") in ("Stop", "watch", "backfill") and o.get("turn_uuid")]
    try:
        from cosmos.adapters import find_claude_sessions, read_session
        by_sid = {sid: p for p, sid in find_claude_sessions(root)}
    except Exception:
        by_sid = {}
    picked = random.sample(journal, min(sample // 2, len(journal))) if journal else []
    for o in picked:
        sid = next((s for s in by_sid if o.get("session") and __import__("hashlib").sha1(s.encode()).hexdigest()[:8] == o["session"]), None)
        if not sid:
            continue
        turns, _ = read_session(by_sid[sid], "claude", 0)
        i = next((k for k, t in enumerate(turns) if t.uuid == o["turn_uuid"]), None)
        if i is None:
            continue
        window = turns[i:i + 6]
        turn_txt = "\n".join(f"{'USER' if t.role == 'user' else 'AGENT'}: {_cut(t.text, 500)}" + (f"\n  edited: {', '.join(t.files[:6])}" if t.files else "")
                             + (f"\n  ran: {' | '.join(c.splitlines()[0][:120] for c in t.commands[:4])}" if t.commands else "") for t in window)
        cases.append({"suite": "journal", "feature": "journal", "new": True, "ref": o["id"], "cosmos_says": "recorded",
                      "state": {"JOURNAL_LINE": o["text"], "TURN": _cut(turn_txt, 4000)}, "questions": {"accurate": Q_JOURNAL}})

    # 7. cosmos as a tool: documentation claims vs source code (existing and new)
    claims = json.loads((HERE / "claims.json").read_text())
    src_root = HERE.parent
    for c in claims:
        excerpt = []
        for f in c["files"]:
            p = src_root / f
            if not p.exists():
                continue
            text = p.read_text(errors="ignore")
            if c.get("grep"):
                lines = text.splitlines(); hits = [i for i, l in enumerate(lines) if any(g in l for g in c["grep"])]
                picked_lines = set()
                for i in hits[:8]:
                    picked_lines.update(range(max(0, i - 6), min(len(lines), i + 34)))   # whole function bodies, not fragments
                excerpt.append(f"[{f}]\n" + "\n".join(f"{j+1}: {lines[j]}" for j in sorted(picked_lines)))
            else:
                excerpt.append(f"[{f}]\n" + text[:3000])
        cases.append({"suite": "tool-claims", "feature": c["feature"], "new": c["feature"] in NEW_FEATURES, "ref": c["id"], "cosmos_says": "implemented",
                      "state": {"CLAIM": c["claim"], "SOURCE_CODE": _cut("\n\n".join(excerpt), 6500)}, "questions": {"claim": Q_CLAIM}})
    return cases


# ---------------------------------------------------------------- judges
class TypeSafeJudge:
    name = "typesafe-jev"

    def __init__(self, key: str, model: str = "jev-latest"):
        self.key, self.model = key, model

    def ask(self, state: Any, questions: Dict[str, Dict]) -> Dict[str, Any]:
        body = json.dumps({"state": state, "model": self.model, "questions": questions}).encode()
        req = urllib.request.Request("https://api.typesafe.ai/v1/systemone", data=body, method="POST",
                                     headers={"Authorization": f"Bearer {self.key}", "Content-Type": "application/json"})
        return _post(req)


class GatewayJudge(TypeSafeJudge):
    """jev-ai.pro: an independently operated gateway to TypeSafe's Jev (same request shape). Credits are scarce there:
    input tokens are billed first, then one credit per request, so cases are packed into few requests."""
    name = "jev-ai.pro gateway → typesafe jev"
    url = "https://jev-ai.pro/api/v1/systemone"

    def ask(self, state, questions):
        body = json.dumps({"state": state, "model": self.model, "questions": questions}).encode()
        req = urllib.request.Request(self.url, data=body, method="POST",
                                     headers={"Authorization": f"Bearer {self.key}", "Content-Type": "application/json"})
        return _post(req)


class CloudflareJudge:
    name = "cloudflare-workers-ai/typesafe-jev"

    def __init__(self, account: str, token: str):
        self.url = f"https://api.cloudflare.com/client/v4/accounts/{account}/ai/run/typesafe/jev"
        self.token = token

    def ask(self, state: Any, questions: Dict[str, Dict]) -> Dict[str, Any]:
        body = json.dumps({"state": state, "questions": questions}).encode()
        req = urllib.request.Request(self.url, data=body, method="POST", headers={"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"})
        out = _post(req)
        return out.get("result", out)


def _ssl_context():
    """Framework builds of Python on macOS ship without a CA bundle; use certifi's when present, else the default."""
    import ssl
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()


def _post(req: urllib.request.Request, tries: int = 4) -> Dict[str, Any]:
    ctx = _ssl_context()
    if not req.has_header("User-agent"):   # some gateways sit behind a CDN that rejects Python's default agent (Cloudflare 1010)
        req.add_header("User-Agent", "cosmos-validation/0.1")
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=60, context=ctx) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            if e.code in (429, 529, 500, 502, 503) and attempt < tries - 1:
                time.sleep(1.5 * (2 ** attempt)); continue
            raise SystemExit(f"judge returned HTTP {e.code}: {e.read().decode()[:300]}")
    raise SystemExit("judge unreachable")


def _answer(ans: Dict[str, Any]) -> Tuple[str, float]:
    t = ans.get("type")
    if t == "noul":
        p = float(ans.get("noul", 0.5)); return ("true" if p >= 0.5 else "false"), max(p, 1 - p)
    if t == "choice":
        return str(ans.get("choice")), float(ans.get("confidence", 0.0))
    if t == "score":
        return f"{float(ans.get('score', 0)):.2f}", float(ans.get("confidence", 0.0))
    return str(ans), 0.0


# ---------------------------------------------------------------- run + report
def _state_text(st: Dict[str, Any]) -> str:
    return "\n\n".join(f"{k}:\n{v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)}" for k, v in st.items())


def run(cases: List[Dict], judge, min_conf: float, batch: int = 1, max_requests: int = 0) -> List[Dict]:
    """One request per case, or `batch` cases per request: the states are concatenated under numbered headings and
    each question names its case. Every answer keeps the raw probabilities, confidence and the request latency."""
    out: List[Dict] = []
    requests_made = 0
    groups = [cases[i:i + batch] for i in range(0, len(cases), batch)] if batch > 1 else [[c] for c in cases]
    for gi, group in enumerate(groups, 1):
        if max_requests and requests_made >= max_requests:
            break
        if len(group) == 1:
            state, questions, keymap = _state_text(group[0]["state"]), group[0]["questions"], {q: (0, q) for q in group[0]["questions"]}
        else:
            parts, questions, keymap = [], {}, {}
            for n, c in enumerate(group, 1):
                parts.append(f"===== CASE {n} =====\n" + _state_text(c["state"]))
                for q, spec in c["questions"].items():
                    qid = f"case{n}_{q}"
                    questions[qid] = dict(spec, instructions=f"About CASE {n} only: " + spec["instructions"])
                    keymap[qid] = (n - 1, q)
            state = "\n\n".join(parts)
        t0 = time.time()
        res = judge.ask(state, questions)
        ms = int((time.time() - t0) * 1000)
        requests_made += 1
        raw = res.get("answers") or {}
        per_case: Dict[int, Dict[str, Any]] = defaultdict(dict)
        for qid, ans in raw.items():
            idx, q = keymap.get(qid, (0, qid))
            per_case[idx][q] = ans
        for idx, c in enumerate(group):
            answers = {q: _answer(a) for q, a in per_case.get(idx, {}).items()}
            out.append({**{k: v for k, v in c.items() if k != "state"}, "answers": answers, "raw": per_case.get(idx, {}),
                        "latency_ms": ms, "usage": res.get("usage", {}) if idx == 0 else {}, "request": gi})
        print(f"\r  request {gi}/{len(groups)} · {ms} ms · usage {res.get('usage')}", end="", flush=True)
    print()
    return out


def agreement(suite: str, c: Dict) -> Optional[bool]:
    a = c["answers"]
    if suite == "facts-vs-evidence":
        return a["support"][0] == "supports"
    if suite == "curation":
        return (a["keep"][0] == "true") == (c["cosmos_says"] == "kept")
    if suite == "freshness":
        return a["stale"][0] == c["cosmos_says"]
    if suite == "recall-precision":
        return a["relevant"][0] == "true"
    if suite == "handoff":
        return float(a["usable"][0]) >= 3.0
    if suite == "journal":
        return a["accurate"][0] == "true"
    if suite == "tool-claims":
        return a["claim"][0] == "implemented"
    return None


def report(results: List[Dict], judge_name: str, repo: str, min_conf: float) -> str:
    lines = [f"# cosmos validation report", "",
             f"Judge: **{judge_name}** (a decision model; it did not write any of cosmos). Repository: `{repo}` (aggregates only). "
             f"Run: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}. Cases: {len(results)}.", "",
             "Agreement = the judge's answer matches what cosmos decided (or, for evidence and claims, the judge says the evidence supports it). "
             f"Low-confidence answers (confidence < {min_conf}) are counted separately and never as agreement.", "",
             "| suite | feature | new / existing | cases | agree | disagree | low confidence | agreement |", "|---|---|---|---|---|---|---|---|"]
    groups: Dict[Tuple[str, str, str], List[Dict]] = defaultdict(list)
    for r in results:
        groups[(r["suite"], r["feature"], "new" if r["new"] else "existing")].append(r)
    totals = Counter()
    for (suite, feat, age), rs in sorted(groups.items()):
        ag = dis = low = 0
        for r in rs:
            conf = min((v[1] for v in r["answers"].values()), default=0.0)
            ok = agreement(suite, r)
            if conf < min_conf:
                low += 1
            elif ok:
                ag += 1
            else:
                dis += 1
        totals.update({"cases": len(rs), "agree": ag, "dis": dis, "low": low})
        rate = f"{ag / max(1, ag + dis):.0%}" if ag + dis else "—"
        lines.append(f"| {suite} | {feat} | {age} | {len(rs)} | {ag} | {dis} | {low} | {rate} |")
    lines += ["", f"**Overall:** {totals['agree']} agree · {totals['dis']} disagree · {totals['low']} low confidence · "
              f"agreement {totals['agree'] / max(1, totals['agree'] + totals['dis']):.0%} on confident answers.", ""]
    # durability distribution where asked
    dur = [float(r["answers"]["durable"][0]) for r in results if "durable" in r["answers"]]
    if dur:
        buckets = Counter(int(round(x)) for x in dur)
        lines += ["Durability of what cosmos keeps (1 = session narration … 5 = must-know rule): " + " · ".join(f"{k}: {buckets[k]}" for k in sorted(buckets)), ""]
    # disagreements, by reference only
    dis_refs = [f"{r['suite']}/{r['feature']}: {r['ref']} → judge {list(r['answers'].values())[0][0]} vs cosmos {r['cosmos_says']}"
                for r in results if agreement(r["suite"], r) is False and min((v[1] for v in r["answers"].values()), default=0) >= min_conf]
    if dis_refs:
        lines += ["## Disagreements (references only)", ""] + [f"- {x}" for x in dis_refs[:60]] + [""]
    claims = [r for r in results if r["suite"] == "tool-claims" and r.get("raw")]
    if claims:
        lines += ["## Documented claims, as the judge saw them", "",
                  "| claim | feature | new / existing | answer | implemented | contradicted | cannot tell | confidence | latency |", "|---|---|---|---|---|---|---|---|---|"]
        for r in sorted(claims, key=lambda r: r["ref"]):
            a = r["raw"].get("claim", {}); pr = a.get("probabilities") or {}
            pc = lambda k: f"{100 * float(pr.get(k, 0)):.0f}%"
            lines.append(f"| {r['ref']} | {r['feature']} | {'new' if r['new'] else 'existing'} | **{a.get('choice', '?')}** | {pc('implemented')} | {pc('contradicted')} | {pc('cannot_tell')} | {100 * float(a.get('confidence', 0)):.0f}% sure | {r.get('latency_ms', 0) / 1000:.1f} s |")
        lines.append("")
    usage = sum(int((r.get("usage") or {}).get("input_tokens", 0)) for r in results)
    lines += [f"Input tokens judged: {usage:,} (≈ ${usage / 1e6 * 0.042:.3f} at the published rate).", "",
              "A high agreement rate is not proof cosmos is right: judge and tool can be wrong together. A low rate on a suite is a real signal. "
              "Calibration of the judge on this traffic is not measured here; see validation/README.md."]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", default=".", help="a repository where cosmos has run")
    ap.add_argument("--judge", choices=["typesafe", "cloudflare", "gateway"], default="typesafe", help="gateway = jev-ai.pro (JEV_AI_PRO_KEY), an independently operated reseller")
    ap.add_argument("--suite", action="append", help="run only these suites (repeatable)")
    ap.add_argument("--batch", type=int, default=1, help="cases per request (saves credits on metered gateways; keep small)")
    ap.add_argument("--max-requests", type=int, default=0, help="stop after this many requests (0 = no limit)")
    ap.add_argument("--sample", type=int, default=40, help="cases per suite")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--min-conf", type=float, default=0.6)
    ap.add_argument("--dry-run", action="store_true", help="build the cases and estimate the cost; call no judge")
    ap.add_argument("--export", help="write the cases as JSONL for a human judge")
    ap.add_argument("--out", default=str(HERE / "REPORT.md"))
    a = ap.parse_args()
    root = Path(a.repo).resolve()
    cases = build_cases(root, a.sample, a.seed)
    if a.suite:
        cases = [c for c in cases if c["suite"] in set(a.suite)]
    est_tokens = sum(len(json.dumps(c["state"], ensure_ascii=False)) // 4 + 120 for c in cases)
    by = Counter((c["suite"], "new" if c["new"] else "existing") for c in cases)
    print(f"{len(cases)} cases from {root.name}:")
    for (s, age), n in sorted(by.items()):
        print(f"  {s:18} {age:9} {n}")
    print(f"≈ {est_tokens:,} input tokens → ≈ ${est_tokens / 1e6 * 0.042:.3f} at $0.042/M")
    if a.export:
        Path(a.export).write_text("\n".join(json.dumps(c, ensure_ascii=False) for c in cases) + "\n"); print(f"wrote {a.export}")
    if a.dry_run or a.export:
        return 0
    if a.judge == "gateway":
        key = os.environ.get("JEV_AI_PRO_KEY")
        if not key:
            print("JEV_AI_PRO_KEY is not set."); return 2
        judge = GatewayJudge(key)
    elif a.judge == "typesafe":
        key = os.environ.get("TYPESAFE_API_KEY")
        if not key:
            print("TYPESAFE_API_KEY is not set. Get a key at typesafe.ai (waitlist) or use --judge cloudflare with a Workers AI token."); return 2
        judge = TypeSafeJudge(key)
    else:
        acct, tok = os.environ.get("CLOUDFLARE_ACCOUNT_ID"), os.environ.get("CLOUDFLARE_API_TOKEN")
        if not (acct and tok):
            print("CLOUDFLARE_ACCOUNT_ID and CLOUDFLARE_API_TOKEN are not set."); return 2
        judge = CloudflareJudge(acct, tok)
    results = run(cases, judge, a.min_conf, batch=a.batch, max_requests=a.max_requests)
    (HERE / "results.jsonl").write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in results) + "\n")
    text = report(results, judge.name, root.name, a.min_conf)
    Path(a.out).write_text(text + "\n")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
