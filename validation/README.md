# Validation: an independent check on cosmos

cosmos is built with Claude and, left alone, would be graded by Claude. That is not a check. This folder asks a
different kind of model, TypeSafe's **Jev**, a decision-only model that returns typed answers with calibrated
probabilities and never writes prose, a fixed set of closed questions about what cosmos actually produced in a
repository, and compares the answers with what cosmos decided.

It is not an integration. cosmos does not call Jev. This is a test you run against a repository where cosmos has
been working, and it writes one report.

## What is checked

| suite | question to the judge | compared with |
|---|---|---|
| facts-vs-evidence | does the evidence (the cited files, today) support the fact? how durable is it as team knowledge? | the fact is active in the ledger |
| curation | should this observation have been kept? | what the dream kept or dropped |
| freshness | given today's evidence, is the fact still true, outdated or unclear? | cosmos's verdict: active, retired, or waiting for a human |
| recall-precision | is this retrieved fact relevant to the task? | the fact was in the top 5 |
| handoff | could a colleague continue the branch from this handoff alone? | the handoff cosmos kept |
| journal | is the journal line an accurate record of the turn? | the line cosmos wrote |
| tool-claims | does the source code implement this documented claim? | 30 claims from the README and site, paired with the code that should implement them |

Every case is tagged **new** or **existing**, so the features added in the last round are reported separately from
the older ones. Answers below a confidence threshold (default 0.6) are counted as low confidence, never as agreement.

## Run it

```bash
# build the cases and estimate the cost, calling nothing
python3 validation/validate.py --repo /path/to/your/repo --dry-run

# with a TypeSafe key (waitlist at typesafe.ai)
TYPESAFE_API_KEY=… python3 validation/validate.py --repo /path/to/your/repo

# or through Cloudflare Workers AI
CLOUDFLARE_ACCOUNT_ID=… CLOUDFLARE_API_TOKEN=… python3 validation/validate.py --judge cloudflare --repo /path/to/your/repo

# or hand the same cases to a person
python3 validation/validate.py --repo /path/to/your/repo --export cases.jsonl
```

The report lands in `validation/REPORT.md` and holds aggregates and references only. Fact texts and code excerpts
are sent to the judge and kept in `validation/results.jsonl` on your machine; neither is committed.

## How to read it

- A **high agreement** rate is not proof cosmos is right. Judge and tool can be wrong together.
- A **low agreement** rate on a suite is a real signal, and the disagreements are listed by reference so you can
  open each fact with `cosmos why <id>`.
- The **durability** distribution says what kind of thing cosmos keeps. A ledger full of level 1 and 2 is a ledger
  full of narration.
- Calibration of the judge on your traffic is not measured here. TypeSafe publishes its own; independent checks
  exist. If you want it measured, label a sample of `results.jsonl` by hand and compare.

## Why Jev and not another LLM

Another LLM would write a paragraph, and the paragraph would have to be trusted. Jev can only pick from the options
given, with a probability attached, in a few hundred milliseconds, for a fraction of a cent per case. It also
cannot flatter. Its documented weak spots, literal reading, counting, dates, multi-hop reasoning, are the reason
the questions here are short and the evidence is placed directly in front of it.
