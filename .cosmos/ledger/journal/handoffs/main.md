---
type: Handoff
kind: handoff
branch: "main"
by: "Biswajit Tripathy"
at: "2026-10-02T14:42:52Z"
how: auto
---

**Auto-upgrade commands.** The auto-upgrade is in 0.1.6, which is still unreleased, so every machine needs one manual step after release; after that it's automatic. In order: 1. **Me:** push to both repos and build the files, once you say go. 2. **You, once:** upload to PyPI. ```bash python3 -m twine upload dist-0.1.6/* ``` 3. **Each machine with a pip install, once** (or let the repo copy carry it, below): ```bash python3 -m pip install -U cosmos-dev ``` 4. **From then on, nothing to run.** Every session start checks PyPI at most once a day and pulls in newer releases. To force or inspect it in a repo: ```bash python3 .cosmos/cosmosw upgrade ``` ```bash python3 .cosmos/cosmosw upgrade --che …
