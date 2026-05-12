# OSW Local Git Workflow

This repository uses local Git safety rails for OpenSolver Workbench development.
Do not push from bootstrap or review prompts.

## Branch Strategy

- `main` is the stable local trunk name.
- `develop` is the default integration branch for v0.1 work.
- Feature branches use `feature/osw-<short-topic>`.
- Keep product feature work out of bootstrap commits.

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

Use sibling worktrees under `../_worktrees/` for isolated feature work.

PowerShell:

```powershell
python tools/git/create_worktree.py "linear static demo" --dry-run
python tools/git/create_worktree.py "linear static demo"
```

Unix shell:

```sh
python3 tools/git/create_worktree.py "linear static demo" --dry-run
python3 tools/git/create_worktree.py "linear static demo"
```

The helper creates a local branch such as `feature/osw-linear-static-demo` from
local `develop`. It does not add remotes, push, force-push, delete branches, or
delete worktrees.

## Checkpoint Commit Policy

Use small local checkpoint commits before risky review, amend, or merge work.
A checkpoint should capture one coherent state and include validation notes in
the commit body.

PowerShell:

```powershell
git status --short --branch
python tools/git/preflight_commit.py
git add .gitignore .gitattributes .gitmessage .githooks tools/git docs/11_git_workflow.md
git commit
```

Unix shell:

```sh
git status --short --branch
python3 tools/git/preflight_commit.py
git add .gitignore .gitattributes .gitmessage .githooks tools/git docs/11_git_workflow.md
git commit
```

## Amend Safety Policy

Before `git commit --amend`, run the status report and save a rescue patch if
there is any uncertainty.

PowerShell:

```powershell
python tools/git/git_status_report.py
python tools/git/rescue_dirty_worktree.py --write
git commit --amend
```

Unix shell:

```sh
python3 tools/git/git_status_report.py
python3 tools/git/rescue_dirty_worktree.py --write
git commit --amend
```

Never amend while unrelated user changes are mixed into the index.

## Merge Gate Policy

The tracked `pre-merge-commit` hook runs `tools/git/check_merge_gate.py`.
It checks staged conflict markers, `git diff --cached --check`, the preflight
artifact scan, optional scope drift checker, optional architecture checker, and
secret-like staged content.

Manual gate:

```powershell
python tools/git/check_merge_gate.py
```

```sh
python3 tools/git/check_merge_gate.py
```

## Dirty Recovery Policy

Use the rescue helper before any manual recovery. It writes patch files and an
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

Review the saved patches before applying or discarding anything.

## Prohibited Git Commands

Do not use these commands in OSW bootstrap, review, or amend workflows unless a
human explicitly requests the exact operation:

- `git push`
- `git push --force`
- `git push --force-with-lease`
- `git remote add`
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
