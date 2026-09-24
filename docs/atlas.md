# Atlas — architecture that stays in sync

`cosmos atlas` reads what the repository already declares and writes `.cosmos/ledger/atlas/`:

| source | what is read |
|---|---|
| `package.json`, `pyproject.toml`, `requirements*.txt`, `pom.xml`, `build.gradle*`, `go.mod`, `Cargo.toml`, `Gemfile` | apps and packages: name, language, dependency count, scripts |
| `docker-compose*.yml` | services (build/image, ports, `depends_on`) and infrastructure containers classified as database / cache / queue / search / identity / gateway |
| `k8s/`, `kubernetes/`, `deploy/`, `helm/`, `charts/`, `manifests/` | Kubernetes objects by kind and name |
| `**/*.tf` | Terraform resource types and counts |
| OpenAPI / Swagger (json or yaml) | every method + path |
| `.env.example` | configuration keys (never `.env`) |
| `README*` | the title |

Outputs: `inventory.md` (tables), `containers.md` and `deployment.md` (Mermaid), `api.md`, and `atlas.json` with a hash of every source file. Each file lists its sources and the commit it was generated at.

**Drift**: `cosmos atlas --check` (also run by every dream and shown at SessionStart and in the UI) compares the recorded hashes with the working tree. When compose, manifests or specs change and the Atlas has not been regenerated, everyone is told — the diagram can no longer silently lie.

**Deep pass**: the model follows the same prompt as `/atlas` (`.claude/commands/atlas.md`) on top of the inventory and writes `system-context.md`, `containers.md`, `data-flow.md`, `deployment.md`, `dependencies.md` and `lanes.md`. Dreams start it in the background when one of those files is missing, when a file the Atlas read has changed, or after `atlas.deep_days` (7) with new commits. It runs `claude -p` with your Claude Code login, read-only tools everywhere and write access only to `.cosmos/ledger/atlas/`; cosmos's own hooks are off for that run. The generator never overwrites a diagram the model wrote (`generated_by: atlas-deep`). `cosmos atlas --deep` runs it now; `/atlas` in Claude Code runs it interactively. Every node must exist in the inventory and every edge must cite a source file. The inventory reads only files git tracks or would track, so ignored folders never shape the map.

The Atlas page in `cosmos ui` renders the Mermaid diagrams and the inventory, with a rebuild button and the drift status.
