---
description: Build or refresh the Atlas — inventory, dependency index and architecture diagrams — into .cosmos/ledger/atlas
---
You are building the **Atlas** for this repository: a living architecture record that cosmos keeps in sync with the code. `cosmos atlas` has already produced a deterministic inventory (`.cosmos/ledger/atlas/inventory.md`, `containers.md`, `deployment.md`, `api.md`) — read those first, then deepen them in three passes and WRITE files; do not just answer in chat.

## Pass 1 — Inventory (no diagrams yet)
Read, in this order, whatever exists: repository root listing · monorepo workspaces · `package.json` / `pom.xml` / `build.gradle*` / `pyproject.toml` / `requirements*.txt` / `go.mod` · `docker-compose*.yml` · `k8s/**`, `helm/**` · `terraform/**` · `README*` · `.env.example` · OpenAPI / Swagger specs · CI workflows.
Update `inventory.md`: services and apps (name, language, entry point, port), data stores, queues/topics, external APIs, environments, and every config key from `.env.example` with which service reads it. Cite the file for each row. Never read `.env`, secrets or credentials.

## Pass 2 — Dependency index
Write `.cosmos/ledger/atlas/dependencies.md`: service → service calls, service → store, service → queue, and the public API surface (method, path, handler file, auth). Prefer facts found in code and specs over README claims; where they disagree record both and mark `DRIFT`.

## Pass 3 — Diagrams (Mermaid, one per file, each ending with a `## Sources` list and the HEAD commit)
1. `system-context.md` — actors, apps, external systems
2. `containers.md` — refine the generated one: protocols on edges, missing services
3. `data-flow.md` — the 2–3 flows that matter most to this product, end to end
4. `deployment.md` — from compose / k8s / Terraform: what runs where
5. `lanes.md` — group modules into feature lanes; propose a `lanes` mapping (lane → path globs) for `.cosmos/config.json`

Rules: every node must exist in the inventory; every edge must have a source file; use the team's own names; keep each diagram under 40 nodes (split if bigger). Finish with `cosmos atlas --check` and print a 5-line summary of what changed since the previous Atlas.
