# Post-Public Release Checklist

This checklist is the reusable post-public release control list for OpenSolver
Workbench after a public prerelease is visible on GitHub. It records the
`v0.1.3-rc1` flow as evidence and as a template for later release candidates.

OSW remains educational and research software. This checklist must not be used
to claim stable production readiness, industrial certification, bundled external
solvers, native commercial CAD direct import, MATLAB/ANSYS/Simulink parity, MSI
installer support, or code signing.

## Purpose

- Preserve the tag, branch, asset, and release-page evidence after publication.
- Keep public release wording accurate after draft, asset, publish, and
  maintenance follow-up gates.
- Make follow-up maintenance work repeatable without editing tags or release
  assets during audit-only gates.
- Give maintainers a command checklist that separates read-only verification,
  branch-only pushes, tag-only pushes, release draft work, asset upload, and
  issue closure.

## Release Identity

Fill this section for each public release.

| Field | v0.1.3-rc1 evidence | Reusable placeholder |
| --- | --- | --- |
| Package version | `0.1.3rc1` | `<release-version>` |
| Public tag | `v0.1.3-rc1` | `<tag-name>` |
| Tag target | `a6e8d3a8211e02359841d10e1947e16ab847b132` | `<tag-target>` |
| Remote tag object | `0502ae26b2013fcb8ce708d21a03d55f9dd7ed04` | `<remote-tag-object>` |
| Release branch | `develop` | `<branch>` |
| Current post-public develop | `c89ebe9f35e90fc05a00698641fad0635562bc4e` | `<branch-head>` |
| GitHub Release state | public prerelease, not draft | `<draft/prerelease/published>` |
| Assets | wheel, sdist, Windows portable ZIP, `SHA256SUMS.txt`, manifest | `<asset-list>` |

Important boundary: the public docs on `develop` may be newer than the tagged
source. Build release assets from the tag unless a later explicit release gate
creates a new tag.

## Pre-Release Gates

- Verify package metadata, `osw.__version__`, CLI `--version`, and release docs
  match the intended release version.
- Run no-tag validation before creating or pushing a tag.
- Verify the worktree has no tracked/staged changes except intentional release
  docs for that gate.
- Run focused tests, release gate checks, docs links, scope drift, architecture
  boundaries, solver artifact hygiene, JSON validation, and `git diff --check`.
- Confirm limitations are visible: prerelease status when applicable, optional
  dependencies, no bundled solvers, no industrial certification, and no stable
  production claim.

## Tag Gates

- Create only an annotated local release tag after metadata and QA pass.
- Verify the tag object type is `tag`.
- Verify the tag peels to the intended release commit.
- Push only the approved tag in the tag-only push gate.
- Never push all tags.
- Never retarget, delete, recreate, or force-update a published tag.
- Record the remote tag object and peeled target after push.

## GitHub Release Draft Gates

- Verify the remote tag exists before creating a GitHub Release draft.
- Verify GitHub CLI authentication and repository access.
- Check whether a release already exists for the tag.
- Create a draft prerelease only with the existing tag and `--verify-tag`.
- Keep notes honest about prerelease status, no assets yet when true, no MSI,
  no code signing, no bundled solvers, and no stable production claim.
- Do not publish in draft-only gates.

## Release Asset Build/Upload Gates

- Build package and binary assets from the release tag, not from a newer
  post-public `develop` commit.
- Build wheel and sdist, then smoke-install the wheel in a fresh environment.
- Build a Windows portable ZIP only when PyInstaller and required GUI
  dependencies are available and the executable `--help` smoke passes.
- Name the Windows bundle a portable ZIP, not an MSI or signed installer.
- Generate `SHA256SUMS.txt` and `release_asset_manifest.json`.
- Upload assets only to the intended GitHub Release and only when the release
  state allows the gate action.
- Do not overwrite release assets unless a later gate explicitly authorizes
  clobber and records the reason.

## Asset Verification Gates

- Verify release asset names, sizes, SHA256 hashes, and manifest entries.
- Verify wheel install and `python -m osw.cli --help`.
- Verify sdist install or metadata when source smoke is requested.
- Verify portable ZIP extraction is safe and does not include `.git`, virtual
  environments, build work directories, runtime artifacts, or secrets.
- Verify portable executable `--help` when the ZIP is built.
- Keep live GitHub release downloads manual or explicitly authorized; CI should
  use offline fixtures by default.

## Publish Gates

- Publish only after an explicit publish gate.
- Re-read release notes immediately before publish.
- Confirm attached assets, checksums, manifest, tag target, prerelease flag, and
  known limitations.
- Do not publish from an audit-only or docs-only gate.
- Do not upload assets while publishing unless the prompt explicitly authorizes
  both actions.

## Post-Public Audit Gates

- Verify GitHub Release is public and remains attached to the intended tag.
- Verify the release is prerelease or stable exactly as intended.
- Verify the release body does not contain stale draft, no-assets, or
  unpublished wording.
- Verify release assets are present and match expected names.
- Verify remote branch and tag state.
- Record warnings: unsigned portable ZIP, no MSI, no code signing, no bundled
  external solvers, optional dependencies are environment-specific.

## Release Notes Correction Gate

- Correct only stale or misleading public release text.
- Do not change the tag, assets, or branch history.
- Remove inaccurate draft/no-assets/no-publish wording after publication.
- Keep prerelease, unsigned portable ZIP, no MSI, no code signing, and no
  bundled solver warnings visible.

## Public Repo Docs Polish

- Update README, quickstart, examples, screenshots, release summaries, and
  limitation links after the source/tag release is public.
- Keep public docs aligned with educational/research scope.
- State what works now without implying production certification or commercial
  solver parity.
- Document source install, GUI launch, CLI smoke, plugin health, examples,
  optional dependencies, and limitations.
- Push only `develop` after checks pass and only when explicitly authorized.

## Branch Reconciliation / Docs Push Gates

- Treat branch pushes separately from tag pushes.
- Fetch and verify `origin/develop` is an ancestor before branch-only push.
- If local and remote `develop` diverge, reconcile in a separate branch
  divergence gate.
- Push exactly `develop` when authorized; do not push tags, all branches, or
  force updates.
- Verify remote `develop` and the release tag after push.

## Maintenance Follow-Up Gates

- Open the next development cycle only after the public release boundary is
  recorded.
- Keep maintenance/revalidation work separate from feature expansion.
- Track duplicate hygiene, live optional dependency evidence, release asset
  smoke automation, portable ZIP UX, public release wording, and issue closure
  as maintenance work.
- Do not create a new release tag unless a later release candidate gate
  explicitly authorizes it.

## CI/Manual Smoke Gates

- Keep default CI network-free and independent of optional solver executables.
- Run offline fixture smoke on pull requests and `develop` pushes.
- Use manual `workflow_dispatch` for live GitHub release downloads.
- Record workflow run IDs, conclusion, event type, branch, and head SHA.
- Treat live solver/science backend validation as environment-specific evidence,
  not a base release blocker.

## Issue/Milestone Triage

- Create or update GitHub issues only for scoped post-public work.
- Keep labels and milestones aligned with maintenance, validation, docs,
  packaging, or later feature planning.
- Do not close issues until evidence exists in the repository or GitHub run
  history.

## Issue Closure Triage

- Close only issues named by the active prompt.
- Verify local docs, reports, tests, workflow runs, and issue comments before
  closure.
- Use `--reason completed` for completed issues.
- Comment with concise evidence.
- Leave ineligible issues open and explain the missing evidence when comments
  are authorized.
- Do not close unrelated issues.

## Required Safety Checks

Run the subset required by the active gate:

```powershell
.venv\Scripts\python.exe -m osw.cli --version
.venv\Scripts\python.exe -m pytest tests/unit -q
.venv\Scripts\python.exe -m pytest tests/gui -q
.venv\Scripts\python.exe -m ruff check src tests tools
.venv\Scripts\python.exe tools/qa/check_release_gate.py
.venv\Scripts\python.exe tools/qa/check_scope_drift.py
.venv\Scripts\python.exe tools/qa/check_architecture_boundaries.py
.venv\Scripts\python.exe tools/qa/check_docs_links.py
.venv\Scripts\python.exe tools/qa/check_no_solver_artifacts_committed.py
.venv\Scripts\python.exe tools/qa/check_public_docs.py
.venv\Scripts\python.exe -m json.tool .codex/func_queue_state.json
git diff --check
git status --short
```

Use Windows OpenSSH override for Git remote verification in this checkout:

```powershell
$env:GIT_SSH = "C:\Windows\System32\OpenSSH\ssh.exe"
git ls-remote --heads origin "refs/heads/develop"
git ls-remote --tags origin "refs/tags/<tag-name>"
git ls-remote --tags origin "refs/tags/<tag-name>^{}"
```

## Never Do List

- Never force push.
- Never retarget a published tag.
- Never delete, recreate, or move release tags without a separate explicit gate.
- Never run `git push --tags` for these scoped gates.
- Never overwrite release assets without explicit clobber authorization.
- Never edit the release during audit-only gates.
- Never claim stable production readiness for a prerelease.
- Never claim MSI installer support unless an MSI was actually built and
  tested.
- Never claim code signing unless code signing was actually performed and
  verified.
- Never claim bundled external solvers.
- Never claim native commercial CAD direct import or MATLAB/ANSYS/Simulink
  cloning.
- Never stage `.codex/reports/*`, `.codex/rescue/*`, or runtime `artifacts/*`.

## Known Limitations

- `v0.1.3-rc1` is a prerelease.
- The Windows portable ZIP is unsigned.
- No MSI installer is provided.
- No code signing is provided.
- External solvers are not bundled.
- Optional dependencies may be missing on a given machine and should produce
  explicit diagnostics.
- Public docs on `develop` may be newer than the tagged source.
- Users must validate engineering results independently.

## Reusable Command Checklist Placeholders

Replace placeholders before running commands.

```powershell
# Identity
$tag = "<tag-name>"
$repo = "<owner/repo>"
$branch = "develop"
$expectedTagTarget = "<tag-target>"

# Local state
git rev-parse --show-toplevel
git status --short
git branch --show-current
git rev-parse HEAD
git rev-list -n 1 $tag
git cat-file -t $tag

# Remote state
$env:GIT_SSH = "C:\Windows\System32\OpenSSH\ssh.exe"
git ls-remote --heads origin "refs/heads/$branch"
git ls-remote --tags origin "refs/tags/$tag"
git ls-remote --tags origin "refs/tags/$tag^{}"

# GitHub release state
gh release view $tag --repo $repo --json tagName,name,isDraft,isPrerelease,url,publishedAt,assets

# Docs and QA
.venv\Scripts\python.exe tools/qa/check_docs_links.py
.venv\Scripts\python.exe tools/qa/check_public_docs.py
.venv\Scripts\python.exe tools/qa/check_scope_drift.py
git diff --check
git status --short
```

For any gate that mutates GitHub issues, releases, tags, assets, or branches,
the active prompt must explicitly authorize the exact mutation.
