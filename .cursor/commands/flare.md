<!-- written by cosmos (`cosmos connect` rewrites it; delete this line to keep your own version) -->
# /flare: File a bug or risk as a flare with a lifecycle

File a flare for: (the text the person typed after the command)
Find the code it is about first and cite it as `path:line`. Then call `cosmos_flare` with `title` (one line, what is wrong), `severity` (critical|high|medium|low), `locations` (`path:line · path:line`), `what`, `impact` and `fix`.
Without the tools: `python3 .cosmos/cosmosw flares add "<severity>: <title> @ <path:line>" --what "…" --impact "…" --fix "…"`.
Several bugs at once (a list a person pasted, one per line, or a .csv / .xlsx / .txt path): one `cosmos_flare` per bug, or `python3 .cosmos/cosmosw flares add --from <file>` (`-` reads stdin).
Do not choose a prefix: cosmos names the flare after the project's lifecycle stage (`python3 .cosmos/cosmosw flares stage` shows it). Reply with the flare id.
