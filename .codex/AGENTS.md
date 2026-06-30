# Codex Harness Agent Rules

This directory owns prompt templates, local reports, MCP notes, and Codex
harness metadata.

- Keep prompt and report files free of secrets, tokens, credentials, private
  keys, and large generated runtime artifacts.
- Reports should record commands run, pass/fail status, skipped checks, changed
  files, blockers, and residual risks.
- Prompt templates must include allowed files, forbidden files, safety rules,
  acceptance criteria, QA commands, and a post-anchor stopping rule.
- Do not create skills or hooks unless the active prompt explicitly allows
  those files.
- Local repository files are authoritative when prompt metadata conflicts with
  docs or code.
