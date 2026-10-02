---
type: Handoff
kind: handoff
branch: "main"
by: "Biswajit Tripathy"
at: "2026-10-07T16:52:13Z"
how: auto
---

The restart didn't fix the Desktop side. Claude Desktop keeps its config file in memory and wrote it back when it restarted, so my rename of the `cosmos` entry was lost. Desktop sessions, HORIZON included, still send their cosmos notes to retent. It only sticks if the file is changed while Desktop is fully closed, so this one needs you: 1. Quit Claude Desktop completely with **⌘Q**. Closing the window isn't enough. 2. In the macOS Terminal app, run: ```bash python3 -c "import json,shutil,os;p=os.path.expanduser('~/Library/Application Support/Claude/claude_desktop_config.json');shutil.copy(p,p+'.bak-before-rename');d=json.load(open(p));s=d.get('mcpServers',{});s.update({'cosmos-retent':s.pop( …
