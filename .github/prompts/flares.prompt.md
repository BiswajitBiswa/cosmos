---
description: "Open flares: list, show one, move it through its lifecycle"
---
<!-- written by cosmos (`cosmos connect` rewrites it; delete this line to keep your own version) -->
Work with this repository's flares. Request: (the text the person typed after the command)
- No request: `python3 .cosmos/cosmosw flares list --status open`, grouped by severity, with what each one blocks.
- An id: `python3 .cosmos/cosmosw flares show <id>`.
- A status change: `python3 .cosmos/cosmosw flares <claim|pr-open|fix|needs-human|withdraw|wontfix|reopen> <id> "<note>"`. When the work lives in another worktree or branch, add `--commit <sha> --branch <name>`.
- A correction to what was filed: `python3 .cosmos/cosmosw flares edit <id> --title … --severity … --locations …`.
Never change a flare's status without saying why in the note.
