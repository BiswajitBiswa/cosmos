# cosmos validation report

> **This run.** Judge reached through the independently operated gateway jev-ai.pro (TypeSafe's Jev behind it; not TypeSafe's own endpoint). Suite: `tool-claims` only, against the public cosmos source. Five requests in total: one single-claim probe; thirty claims packed ten per request with excerpts cut around matching lines; then the twelve unconfirmed claims re-judged in one request with whole functions extracted by the Python parser. The table shows the latest answer per claim. No company repository content was sent. Confidence is the judge's own figure; answers under 60% are listed but not counted.


Judge: **jev-ai.pro gateway → typesafe jev** (a decision model; it did not write any of cosmos). Repository: `cosmos` (aggregates only). Run: 2026-09-22 15:42 UTC. Cases: 30.

Agreement = the judge's answer matches what cosmos decided (or, for evidence and claims, the judge says the evidence supports it). Low-confidence answers (confidence < 0.6) are counted separately and never as agreement.

| suite | feature | new / existing | cases | agree | disagree | low confidence | agreement |
|---|---|---|---|---|---|---|---|
| tool-claims | atlas | existing | 1 | 1 | 0 | 0 | 100% |
| tool-claims | charter | existing | 2 | 2 | 0 | 0 | 100% |
| tool-claims | dream | existing | 2 | 1 | 0 | 1 | 100% |
| tool-claims | eval | new | 1 | 1 | 0 | 0 | 100% |
| tool-claims | flares | existing | 1 | 1 | 0 | 0 | 100% |
| tool-claims | freshness | new | 3 | 3 | 0 | 0 | 100% |
| tool-claims | gate | existing | 1 | 1 | 0 | 0 | 100% |
| tool-claims | handoff | new | 1 | 1 | 0 | 0 | 100% |
| tool-claims | hooks | existing | 1 | 1 | 0 | 0 | 100% |
| tool-claims | journal | new | 1 | 0 | 0 | 1 | — |
| tool-claims | lanes | existing | 1 | 1 | 0 | 0 | 100% |
| tool-claims | ledger | existing | 1 | 1 | 0 | 0 | 100% |
| tool-claims | mcp | existing | 2 | 2 | 0 | 0 | 100% |
| tool-claims | pretooluse-recall | new | 1 | 1 | 0 | 0 | 100% |
| tool-claims | privacy | existing | 1 | 1 | 0 | 0 | 100% |
| tool-claims | proportional-gate | new | 1 | 1 | 0 | 0 | 100% |
| tool-claims | reader | new | 2 | 1 | 0 | 1 | 100% |
| tool-claims | sources | new | 2 | 2 | 0 | 0 | 100% |
| tool-claims | sync | new | 2 | 2 | 0 | 0 | 100% |
| tool-claims | verdicts-aging | new | 1 | 0 | 0 | 1 | — |
| tool-claims | watch | new | 2 | 1 | 0 | 1 | 100% |

**Overall:** 25 agree · 0 disagree · 5 low confidence · agreement 100% on confident answers.

## Documented claims, as the judge saw them

| claim | feature | new / existing | answer | implemented | contradicted | cannot tell | confidence | latency |
|---|---|---|---|---|---|---|---|---|
| agent-fact-vs-human-rule | mcp | existing | **implemented** | 81% | 1% | 18% | 71% sure | 1.3 s |
| atlas-drift | atlas | existing | **implemented** | 81% | 1% | 18% | 71% sure | 2.3 s |
| auto-dream | dream | existing | **implemented** | 96% | 3% | 1% | 95% sure | 1.2 s |
| auto-memory-input | reader | new | **implemented** | 93% | 6% | 1% | 91% sure | 1.9 s |
| charter-first | charter | existing | **implemented** | 98% | 1% | 1% | 97% sure | 2.3 s |
| charter-grounded | charter | existing | **implemented** | 96% | 2% | 2% | 94% sure | 1.3 s |
| compact-recall | ledger | existing | **implemented** | 90% | 9% | 1% | 85% sure | 1.3 s |
| doubtful-never-injected | freshness | new | **implemented** | 96% | 3% | 1% | 95% sure | 1.9 s |
| dropped-never-resurface | dream | existing | **contradicted** | 34% | 64% | 2% | 46% sure | 2.3 s |
| evidence-across-worktrees | freshness | new | **implemented** | 99% | 1% | 0% | 99% sure | 1.9 s |
| flares-aging | verdicts-aging | new | **implemented** | 57% | 2% | 41% | 35% sure | 2.3 s |
| flares-close-from-commits | flares | existing | **implemented** | 95% | 3% | 2% | 93% sure | 1.2 s |
| gate-holds-once | gate | existing | **implemented** | 73% | 24% | 3% | 60% sure | 1.9 s |
| gate-proportional | proportional-gate | new | **implemented** | 79% | 20% | 1% | 69% sure | 1.9 s |
| git-history-source | sources | new | **implemented** | 97% | 3% | 0% | 95% sure | 1.2 s |
| handoff-auto-and-explicit | handoff | new | **implemented** | 98% | 1% | 1% | 97% sure | 1.2 s |
| hook-attaches-clone | sync | new | **implemented** | 77% | 22% | 1% | 65% sure | 2.3 s |
| hooks-never-break-a-session | hooks | existing | **implemented** | 95% | 5% | 0% | 91% sure | 2.3 s |
| identifier-check | freshness | new | **implemented** | 88% | 11% | 1% | 82% sure | 1.9 s |
| journal-per-turn | journal | new | **implemented** | 68% | 27% | 4% | 53% sure | 2.3 s |
| lanes-model-then-paths | lanes | existing | **implemented** | 82% | 18% | 0% | 72% sure | 1.3 s |
| ledger-branch | sync | new | **implemented** | 82% | 13% | 5% | 73% sure | 2.3 s |
| pr-reviews-source | sources | new | **implemented** | 96% | 3% | 1% | 94% sure | 1.2 s |
| pretooluse-recall | pretooluse-recall | new | **implemented** | 91% | 8% | 1% | 86% sure | 1.9 s |
| reader-reads-in-context | reader | new | **implemented** | 66% | 32% | 2% | 48% sure | 2.3 s |
| recall-eval | eval | new | **implemented** | 95% | 5% | 0% | 93% sure | 1.3 s |
| secrets-redacted | privacy | existing | **implemented** | 83% | 16% | 1% | 76% sure | 1.3 s |
| tools-precise-errors | mcp | existing | **implemented** | 86% | 13% | 1% | 79% sure | 2.3 s |
| watcher | watch | new | **implemented** | 70% | 23% | 7% | 54% sure | 2.3 s |
| worktree-paths | watch | new | **implemented** | 87% | 12% | 1% | 81% sure | 2.3 s |

Input tokens judged: 56,685 (≈ $0.002 at the published rate).

A high agreement rate is not proof cosmos is right: judge and tool can be wrong together. A low rate on a suite is a real signal. Calibration of the judge on this traffic is not measured here; see validation/README.md.
