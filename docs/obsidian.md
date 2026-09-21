# Obsidian

The ledger *is* a vault: markdown notes, YAML frontmatter, `[[wikilinks]]`, `#tags`. `cosmos init` adds `.obsidian/app.json` and a `graph.json` with colour groups per category, so the graph view shows architecture/decision/convention/… in distinct colours and superseded facts faded.

- `cosmos obsidian --open` — opens `.cosmos/ledger` in Obsidian (via `obsidian://` URI).
- `cosmos obsidian --vault ~/Obsidian/Team` — symlinks the ledger into an existing vault as `cosmos/<repo>/`, so several repos' ledgers sit side by side in one vault.
- `_index.md` is the map of content; every note links its evidence, related facts, contradictions and supersession chain.
- Edits you make in Obsidian are real: change the title line to reword a fact, or the `status` field to retire it, then `cosmos render`.

`workspace*.json` is gitignored; `app.json` and `graph.json` are committed so the team shares the same view.
