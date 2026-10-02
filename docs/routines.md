# Routines: cosmos's work, run by Claude Routines

Everything cosmos does by itself (dreams, the watcher, the daily pulse) runs on someone's machine. Claude Routines run
Claude Code in the cloud on a schedule or a GitHub trigger, on a checkout of the repository, whether or not any laptop
is open. cosmos ships seven routines for them.

## Set one up

In Claude: **Routines → New routine**. Pick the repository, the schedule or trigger from the table, and paste one line
as the instruction:

```
Run `python3 .cosmos/cosmosw routine <name>` and follow what it prints.
```

`cosmos routines` lists them with their schedules. The steps are not in the routine: `cosmos routine <name>` prints
them from the repository's own cosmos, so a better routine arrives with the next release and the auto-upgrade, and
nobody edits a routine or a repository to get it.

| routine | when | what it does |
|---|---|---|
| `pr-review` | pull request opened or updated | reviews the diff against the Charter, the team's rules and the open flares on the files it touches; names which callers the change can break; runs `cosmos scan`; posts one review comment and files flares for real bugs |
| `pulse` | daily | `cosmos pulse --bench --save`; investigates every red health check; opens a pull request with the day's metrics |
| `dream` | nightly | the dream, then a reconcile of stale and contradicting facts against today's code, and the Atlas when it drifted; a pull request with the `.cosmos/` changes |
| `scan` | weekly | `cosmos scan --tools` over the whole repository; a flare for each real finding, false positives named |
| `merge-memory` | pull request closed (merged) | decisions and constraints from the PR's description and review become facts; flares it fixed are closed; a release-notes line |
| `flare-triage` | weekly | flares open 14+ days are checked against the code: gone, fixed or still real; duplicates merged |
| `digest` | weekday mornings | what the team's memory gained since yesterday, in under 15 lines, posted where the routine posts |

## What every run does the same way

It works on a branch named `cosmos/<routine>-<date>` and ends with a pull request (or a comment, for `pr-review`);
it never commits to the default branch and never prints a secret. It reads `.cosmos/charter.md` first and records
through the command line (`cosmos remember`, `cosmos flares add`), so what it learns goes through review like code.
