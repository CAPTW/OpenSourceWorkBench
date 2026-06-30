---
name: dirty-worktree-recovery
description: Preserve and classify dirty local changes before recovery or task handoff.
---

# Dirty Worktree Recovery

Use when a task starts dirty or unexpected changes appear. Save a rescue patch,
record `git status --short`, create a local rescue branch when appropriate, and
work only with clearly related changes. Do not run `git reset --hard` or
`git clean`.
