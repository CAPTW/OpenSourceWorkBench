# Git Worktree Start Template

Confirm base branch exists and is clean. If the feature branch does not exist,
run `git worktree add -b FEATURE_BRANCH WORKTREE_PATH BASE_BRANCH`. If it
exists, validate branch and path before reuse. Do not overwrite paths.
