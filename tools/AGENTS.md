# Tools Agent Rules

This directory owns repository helper scripts.

- Tools must be local-first, deterministic, and safe to run from PowerShell and
  Unix shells when practical.
- Do not push, force-push, edit remotes, delete branches, delete worktrees, run
  `git reset --hard`, or run `git clean`.
- Do not write global Git config or infer missing Git identity.
- Prefer clear nonzero exit codes for hard failures and concise diagnostics for
  skipped optional checks.
- Secret scans, runtime artifact scans, scope checks, and architecture checks
  must avoid network access by default.
- Tool tests should not mutate real user state outside the test workspace.
