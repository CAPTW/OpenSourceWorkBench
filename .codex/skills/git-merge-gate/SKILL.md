---
name: git-merge-gate
description: Gate squash merges into develop using review score, QA evidence, clean worktrees, and diff scope.
---

# Git Merge Gate

Use before merging to `develop`. Require review approval, passing or validly
skipped QA, clean source and target worktrees, no runtime artifacts, no secrets,
and diff scope matching the Task Card. Default to squash merge. Do not push.
