# MCP Resource Plan

MCP resources may help Codex find OSW prompts, reports, schemas, and role
guidance, but local repository files remain authoritative.

## Resource Categories

- Prompt templates under `.codex/prompts/`.
- Agent role descriptions under `.codex/agents/`.
- Review, amend, merge, release, and smoke reports under `.codex/reports/`.
- Future schema references for ProjectSchema, UnitSystem, MaterialDB,
  ResultDataset, and FigureDataset.
- Optional connector summaries that exclude secrets, tokens, and credentials.

## Rules

- Do not store API keys, credentials, private documents, or solver runtime junk
  in MCP resources.
- Prefer stable local Markdown resources over hidden external state.
- If MCP content conflicts with tracked docs or `AGENTS.md`, follow the tracked
  repository file.
- MCP examples must be local-only and safe to share.
