# Team 17 — Elnora AI Agent Hackathon

Private workspace for **Team 17**. Push your work here — only your teammates
and the organizers can see this repo.

## What's already set up

This repo ships pre-wired with the hackathon agent toolkit (the same tools you
configured in the earlier sessions):

- **Agent config** — `CLAUDE.md` / `AGENTS.md`, and `.claude/settings.json`
  (enabled plugins, marketplaces, and the command allow/deny safety lists)
- **MCP servers** — `.mcp.json` (`context7`, `grep`, `chrome-devtools`, `estonian`)
- **Bundled plugins** — `plugins/` (Vercel + v0)
- **Examples** — `examples/` (Vertex image/video/voice + **Azure OpenAI** calls)
- **Tool catalog** — `TOOLS.md`

## Quick start

1. Clone this repo and open it in VS Code.
2. Start your coding agent: type `claude` (or `codex`).
3. Add your API key:
   ```bash
   cp .env.template .env
   # paste the Azure OpenAI key the organizers gave you into AZURE_OPENAI_API_KEY
   ```
4. Make your first AI call — see `examples/azure-openai/`.

## The hackathon AI models

Azure OpenAI models are pre-configured in `.env.template` (`gpt-5.5`,
`gpt-5.4-mini`, `text-embedding-3-large`). The endpoint is already filled in; the
**API key comes from the organizers**. Keep it in `.env` (gitignored) — never
commit it.

Build something great. 🚀
