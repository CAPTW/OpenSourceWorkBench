---
name: git-worktree
description: Create or validate local feature and amend worktrees without pushing or deleting branches.
---

# Git Worktree

Use before feature or amend work. Confirm base branch exists and is clean.
Never overwrite an existing path. Use `git worktree add -b <branch> <path>
develop` for new feature branches. Do not push, delete branches, delete
worktrees, or edit remotes.
