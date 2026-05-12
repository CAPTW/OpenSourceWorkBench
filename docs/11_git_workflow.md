# OSW Local Git Workflow

This repository uses local Git safety rails for OpenSolver Workbench
development. The workflow is designed for Codex-assisted work where review,
amend, and recovery must be possible without pushing or damaging user state.

## Non-Negotiable Safety Rules

- Do not run `git push` or any force-push variant.
- Do not add, remove, or rewrite remotes.
- Do not delete branches or worktrees.
- Do not run `git reset --hard` or `git clean`.
- Do not overwrite an existing worktree path.
- Do not commit generated solver runtime junk, secrets, credentials, or tokens.
- Do not guess missing `user.name` or `user.email`; report the blocker instead.

## Branch Strategy

- `main` is the stable local trunk name.
- `develop` is the default integration branch for v0.1 work.
- Feature branches use `feature/osw-<phase-step-or-topic>`.
- Amend branches use `amend/osw-<phase-step>-review-<n>`.
- Release preparation branches, when needed, use `release/osw-v<version>`.

For a brand-new repository with no commits, Git can point `HEAD` at `main`, but
additional branches such as `develop` cannot be materialized until the first
commit exists. After the initial safe checkpoint commit, create `develop` from
`main`.

PowerShell:

```powershell
git switch main
git switch -c develop
```

Unix shell:

```sh
git switch main
git switch -c develop
```

## Worktree Strategy

Use sibling worktrees under `../_worktrees/` for isolated feature and amend
work. The base repository should stay clean and available for branch
inspection, merge gates, and recovery.

Feature worktree example:

```powershell
python tools/git/create_worktree.py "project schema" --dry-run
python tools/git/create_worktree.py "project schema"
```

```sh
python3 tools/git/create_worktree.py "project schema" --dry-run
python3 tools/git/create_worktree.py "project schema"
```

Manual equivalent when the helper is unavailable:

```powershell
git worktree add -b feature/osw-p1-1-project-schema ..\_worktrees\osw-p1-1-project-schema develop
```

```sh
git worktree add -b feature/osw-p1-1-project-schema ../_worktrees/osw-p1-1-project-schema develop
```

If the branch already exists but has no worktree, add the worktree from the
branch:

```powershell
git worktree add ..\_worktrees\osw-p1-1-project-schema feature/osw-p1-1-project-schema
```

```sh
git worktree add ../_worktrees/osw-p1-1-project-schema feature/osw-p1-1-project-schema
```

Never create a worktree from a dirty base worktree, and never reuse a path that
already exists.

## Checkpoint Commit Policy

Checkpoint commits are local recovery points before review, amend, merge, or
other risky work. A checkpoint should capture one coherent state and should not
include runtime artifacts or unrelated user changes.

PowerShell:

```powershell
git status --short --branch
python tools/git/preflight_commit.py
git add <allowed-files>
git commit -m "checkpoint(p1.1): project schema before review"
```

Unix shell:

```sh
git status --short --branch
python3 tools/git/preflight_commit.py
git add <allowed-files>
git commit -m "checkpoint(p1.1): project schema before review"
```

Checkpoint commits on feature or amend branches are local safety commits. When
the work passes review, `develop` receives a single squash commit rather than
the checkpoint sequence.

## Amend Safety Policy

Review fixes that might disturb a working checkpoint should be performed on an
amend branch or amend worktree created from the review checkpoint.

PowerShell:

```powershell
git worktree add -b amend/osw-p1-1-project-schema-review-01 ..\_worktrees\osw-amend-p1-1-project-schema-review-01 <review-commit>
```

Unix shell:

```sh
git worktree add -b amend/osw-p1-1-project-schema-review-01 ../_worktrees/osw-amend-p1-1-project-schema-review-01 <review-commit>
```

An amend commit must state which review findings it addresses and must record
rerun command evidence in `.codex/reports/amend/` when that report path is
available. Never amend while unrelated user changes are mixed into the index.

## Merge Gate Policy

The default merge into `develop` is a squash merge after review approval. The
merge gate must verify:

- Source branch exists and is clean.
- Target branch exists and is clean.
- Review decision and score meet `docs/06_review_protocol.md` thresholds.
- Required fixes are complete.
- Pre-merge QA passes or has valid local skip reasons.
- Scope drift and architecture checks pass when available.
- Diff scope matches the Task Card.
- No secrets, generated runtime artifacts, or forbidden claims are in the diff.

Manual gate:

```powershell
python tools/git/check_merge_gate.py
git switch develop
git merge --squash <source-branch>
git status --short
git commit -m "<squash commit message>"
```

```sh
python3 tools/git/check_merge_gate.py
git switch develop
git merge --squash <source-branch>
git status --short
git commit -m "<squash commit message>"
```

If conflicts occur, stop and report the blocker. Do not perform a large
automatic conflict resolution inside the merge prompt.

## Rollback and Recovery Policy

Rollback means returning to a known safe local state while preserving evidence.
Prefer non-destructive recovery:

- Switch back to a clean branch or worktree.
- Use checkpoint commits as restore references.
- Save rescue patches before changing dirty files.
- Use `git revert` for already-committed changes when a normal inverse commit
  is appropriate.
- Park out-of-scope work in a new Task Card, risk entry, or decision-log entry.

Do not use `git reset --hard`, `git clean`, branch deletion, or worktree
removal as a Codex recovery shortcut.

## Dirty Recovery Policy

Use the rescue helper before manual recovery. It writes patch files and an
untracked-file manifest under `.git/osw-rescue/<timestamp>` only when `--write`
is passed.

PowerShell:

```powershell
python tools/git/rescue_dirty_worktree.py
python tools/git/rescue_dirty_worktree.py --write
```

Unix shell:

```sh
python3 tools/git/rescue_dirty_worktree.py
python3 tools/git/rescue_dirty_worktree.py --write
```

Review saved patches before applying or discarding anything.

## Prohibited Git Commands

Do not use these commands in OSW bootstrap, review, amend, merge, or recovery
workflows unless a human explicitly requests the exact operation:

- `git push`
- `git push --force`
- `git push --force-with-lease`
- `git remote add`
- `git remote remove`
- `git remote set-url`
- `git branch -D`
- `git branch -d`
- `git worktree remove`
- `git reset --hard`
- `git clean -fd`
- `git checkout -- <path>` for user-owned changes

## Local Configuration

Bootstrap configures only local repository settings:

```powershell
git config --local core.hooksPath .githooks
git config --local commit.template .gitmessage
```

```sh
git config --local core.hooksPath .githooks
git config --local commit.template .gitmessage
```

If `user.name` or `user.email` is missing, report it and let the developer set
the appropriate identity. Do not guess or write global Git identity settings.

## Reports

Codex reports should be written under `.codex/reports/` when the relevant
directory is available:

- `.codex/reports/worktrees/` for worktree start reports.
- `.codex/reports/review/` for pre-review checkpoint and review evidence.
- `.codex/reports/amend/` for amend start and post-amend comparisons.
- `.codex/reports/merge/` for merge or blocked-merge reports.
- `.codex/reports/release/` for release gate evidence.
