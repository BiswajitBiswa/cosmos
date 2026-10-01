---
type: Handoff
kind: handoff
branch: "main"
by: "Biswajit Tripathy"
at: "2026-10-01T12:39:39Z"
how: auto
---

You're right. That was cosmos leaking across projects, and it's now fixed: a session in another project can't read or write retent's memory any more. **What happened:** your Claude Desktop config has a server named `cosmos` hard-wired to retent, and Desktop offers it to every session. The Odin session's project has no `.cosmos`, so no cosmos briefing ran there to warn it. The tool's reply also didn't say which repo it wrote to, so the agent believed it had recorded the bug "in cosmos". **The fix (`cosmos/mcp.py:156`, `foreign_session`):** - **The server asks which project the session is in.** Claude Code reports a session's project folder when the server asks (MCP "roots"). I confirmed that  …
