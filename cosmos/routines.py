"""Routines: cosmos's work run by Claude Routines (scheduled or triggered Claude Code runs in the cloud).

Everything cosmos does by itself today runs on someone's machine: dreams, the watcher, the daily pulse. A routine runs
on the repository whether or not any laptop is open. Each one is set up once in Claude's Routines screen with a single
instruction:

    Run `python3 .cosmos/cosmosw routine <name>` and follow what it prints.

The steps themselves live here, in cosmos, so a better routine arrives with a release and the auto-upgrade, never by
editing the routine or the repository. A routine works through a branch and a pull request, never on the default
branch, and never prints a secret.
"""
from __future__ import annotations

from typing import Dict, List

CLI = "python3 .cosmos/cosmosw"

COMMON = f"""Ground rules for this run:
- You are running unattended in the cloud on a checkout of this repository. Work on a new branch named `cosmos/<routine>-<date>` and finish with a pull request; never commit to the default branch, never force-push.
- Read `.cosmos/charter.md` first; it outranks your own habits.
- Record through the command line: `{CLI} remember "…"` for a decision or constraint, `{CLI} flares add "<severity>: <title> @ <path:line>" --what … --fix …` for a bug. Never choose a flare prefix.
- Never print, copy or commit a secret value; naming a variable is fine.
- If a step fails, say which and why in the pull request (or the run's summary) instead of guessing.
"""

ROUTINES: List[Dict[str, str]] = [
    {"name": "pr-review", "title": "Charter review of a pull request", "when": "Trigger: pull request opened or updated",
     "steps": f"""Review the pull request that triggered this run against what this team agreed and already knows.
1. Read the diff (`git diff origin/<base>...HEAD`). For every file it touches run `{CLI} search --file <path>` and read the facts, rules and open flares it returns.
2. Check the change against `.cosmos/charter.md` and the rules: tests for changed behaviour, the file's existing style, errors handled where they can be acted on, docs the charter requires.
3. Reach: for each changed module, find who imports it (`git grep -l` on its import name) and say which of those callers the change could break.
4. Security: `{CLI} scan` reports credentials, hidden Unicode and agent-steering text; if a dependency manifest changed, run its audit.
5. Post ONE review comment: what is right, what breaks a rule (with `path:line` and the rule's id), the reach, open flares on these files that the PR fixes or ignores. No style nitpicks the charter does not ask for.
6. File a flare for a real bug you found that the PR does not fix. Do not push commits to the PR branch."""},
    {"name": "pulse", "title": "Daily health and metrics", "when": "Schedule: daily",
     "steps": f"""Measure cosmos in this repository and act on anything red.
1. Run `{CLI} pulse --bench --save`. It writes `.cosmos/ledger/metrics/<date>.json`.
2. For every health check marked ✗: find why (logs in `.cosmos/state/`, the check's detail), and file a flare with the evidence, or fix it when the fix is in this repository and small.
3. Open a pull request with the metrics file and any fix. Its description lists each health check and the headline numbers (turns, facts, flares, recall@5, before-edit hit, tokens per prompt, hook time)."""},
    {"name": "dream", "title": "Nightly dream: curate, reconcile, refresh the Atlas", "when": "Schedule: nightly",
     "steps": f"""Do the memory work that otherwise needs someone's laptop.
1. `{CLI} dream` (it curates what sessions left, merges duplicates, finds contradictions and stale facts).
2. Reconcile: for each fact `{CLI} pulse` or the dream flags as stale or contradicting, check today's code and either verify it (`{CLI} verify <id>`), correct it (`{CLI} remember` with the corrected sentence) or retire it (`{CLI} forget <id>`), naming the file you checked.
3. `{CLI} atlas` when the briefing says the Atlas drifted.
4. Open a pull request with the `.cosmos/` changes; its description says how many facts were added, merged, corrected and retired, and why for each retirement."""},
    {"name": "scan", "title": "Weekly security scan", "when": "Schedule: weekly",
     "steps": f"""Scan the whole repository, not just the last turn's files.
1. `{CLI} scan --tools` (credentials, hidden Unicode, agent-steering text in instruction files, and bandit, pip-audit, npm audit, semgrep, gitleaks where they can be installed: install the ones the repository's languages need first).
2. For each finding: confirm it is real by reading the code. File a flare for each real one (severity by what an attacker gets), and name each false positive with why.
3. Open a pull request only for safe, small fixes (a dependency bump with its changelog checked, a removed hidden character); everything else stays a flare."""},
    {"name": "merge-memory", "title": "What a merged pull request taught the team", "when": "Trigger: pull request closed (merged)",
     "steps": f"""Turn the merged pull request into team memory and release notes.
1. Read the pull request's description, its review comments and its commits (`gh pr view <n> --comments`).
2. Each decision with its reason, each constraint a reviewer stated, each correction: `{CLI} remember "…"` (one full sentence naming the file it applies to). Skip task progress.
3. Flares this pull request fixed: `{CLI} flares fix <id> "PR #<n>"`.
4. Append a user-facing line to the release notes draft (`CHANGELOG.md` under Unreleased, or the file the repository uses), then open a pull request with it and the `.cosmos/` changes."""},
    {"name": "flare-triage", "title": "Weekly flare triage", "when": "Schedule: weekly",
     "steps": f"""Keep open flares honest.
1. `{CLI} flares list --status open` and `{CLI} pulse` (flares naming files this repository lacks).
2. For each flare open 14+ days: check the code at its `path:line`. Gone → `{CLI} flares withdraw <id> "<why>"`; already fixed → `{CLI} flares fix <id> "<commit>"`; still real → leave it and say so.
3. Merge duplicates (same file and same problem): keep the older, withdraw the newer naming it.
4. Open a pull request with the `.cosmos/` changes and a table of what moved and why."""},
    {"name": "digest", "title": "Team digest", "when": "Schedule: weekdays, morning",
     "steps": f"""Tell the team what changed in its memory since yesterday, in under 15 lines.
1. Read yesterday's journal (`.cosmos/ledger/journal/<date>.md`), the facts and rules created or changed since yesterday (`{CLI} search` and the ledger's `updated:` dates), and flares opened, fixed or regressed.
2. Write: decisions and rules first (who, what, why), then flares (opened · fixed · regressed), then the busiest lanes. Name files as `path`.
3. Post it where the routine is configured to post (a Slack channel, or a GitHub discussion); change no files."""},
]


def find(name: str) -> Dict[str, str]:
    for r in ROUTINES:
        if r["name"] == name:
            return r
    raise KeyError(name)


def instructions(name: str) -> str:
    r = find(name)
    return f"# cosmos routine · {r['name']} — {r['title']}\n\n{COMMON.replace('<routine>', r['name'])}\n{r['steps']}\n"


def setup_line(name: str) -> str:
    return f"Run `{CLI} routine {name}` and follow what it prints."
