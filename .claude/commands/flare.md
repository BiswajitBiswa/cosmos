---
description: "File a bug or risk as a flare with a lifecycle"
argument-hint: "<what is wrong>"
---
<!-- written by cosmos (`cosmos connect` rewrites it; delete this line to keep your own version) -->
File a flare for: $ARGUMENTS
Find the code it is about first and cite it as `path:line`. Then call `cosmos_flare` with `title` (one line, what is wrong), `severity` (critical|high|medium|low), `locations` (`path:line · path:line`), `what`, `impact` and `fix`.
Without the tools: write the finding as a one-item JSON list (id, severity, title, area, locations, sections [[label, text]]) to a temporary file and run `python3 .cosmos/cosmosw flares import <file>`.
Do not choose a prefix: cosmos names the flare after the project's lifecycle stage (`python3 .cosmos/cosmosw flares stage` shows it). Reply with the flare id.
