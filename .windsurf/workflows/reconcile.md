---
description: "Bring the ledger back in line with the code: stale, moved and contradicting facts"
---
<!-- written by cosmos (`cosmos connect` rewrites it; delete this line to keep your own version) -->
Reconcile the team memory with the code. (the text the person typed after the command)
1. `python3 .cosmos/cosmosw review` lists contradictions and stale facts.
2. For each stale fact: if its evidence file moved, find the new path (`git log --follow --name-status -- <old path>`) and confirm the fact still holds there; if it holds, `python3 .cosmos/cosmosw verify <id>`; if it no longer holds, `python3 .cosmos/cosmosw forget <id>`.
3. For each contradiction: read both facts and the code; keep the true one with `python3 .cosmos/cosmosw verify <id> --resolve`.
4. Run `python3 .cosmos/cosmosw dream` to consolidate, then `python3 .cosmos/cosmosw health`.
Report counts: verified, forgotten, resolved, left for a human (and why).
