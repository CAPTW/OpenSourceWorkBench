# Decision Log

This log records architecture and process decisions that shape OSW v0.1.
Decisions are append-only unless a later ADR explicitly supersedes one.

## ADR-0001: Local-First Git Safety

- Status: Accepted
- Date: 2026-05-12
- Context: OSW work is performed by Codex in local repositories and worktrees.
  Review, amend, and recovery prompts must not risk remote state or user work.
- Decision: Codex workflows must not push, force-push, add or modify remotes,
  delete branches, delete worktrees, run `git reset --hard`, or run `git clean`
  unless a user explicitly requests the exact operation.
- Consequences: More local reports and checkpoint commits are required, but
  recovery is easier and remote repository state remains user-controlled.

## ADR-0002: Use `src/osw` Package Layout

- Status: Accepted
- Date: 2026-05-12
- Context: OSW needs a standard Python layout that keeps package imports
  explicit and separates product code from tests, docs, tools, and examples.
- Decision: The Python package lives under `src/osw`. Tests import the package
  through normal packaging or the configured local test environment.
- Consequences: Packaging metadata must include the `src` layout, and examples
  should not depend on implicit current-directory imports.

## ADR-0003: Heavy Dependencies Are Optional Extras

- Status: Accepted
- Date: 2026-05-12
- Context: v0.1 targets PySide6, meshio, Gmsh, PyVista, Matplotlib, CalculiX,
  OpenFOAM templates, Cantera, CoolProp, and MATLAB/Octave workflows, but not
  every developer or CI job should install heavy stacks.
- Decision: Heavy GUI, mesh, solver, CFD, chemistry, thermophysical, and
  visualization dependencies remain optional extras. The base install supports
  import, CLI smoke checks, and lightweight tests.
- Consequences: Feature code must guard optional imports and report missing
  extras clearly. Unit tests cannot assume heavy extras are installed.

## ADR-0004: No GUI Direct Solver Subprocess Execution in v0.1

- Status: Accepted
- Date: 2026-05-12
- Context: GUI-triggered external solver execution increases safety,
  reproducibility, cancellation, and environment complexity.
- Decision: v0.1 GUI workflows may prepare, preview, validate, and inspect
  solver cases, but must not directly launch external solver subprocesses.
- Consequences: Solver demos should use prepared templates, dry-run case
  generation, imported results, and clear command-line handoff documentation.

## ADR-0005: Worktree, Checkpoint, and Amend Loop

- Status: Accepted
- Date: 2026-05-12
- Context: Review and amend work can damage a useful implementation if done
  directly on the only working copy.
- Decision: Phase-step work uses `feature/osw-*` worktrees from `develop`.
  Review starts from a checkpoint commit. Risky review fixes use
  `amend/osw-*` branches or worktrees from the checkpoint.
- Consequences: Branch history may contain local checkpoint commits, but merge
  to `develop` remains clean through squash commits after gate approval.

## ADR-0006: Review-Gated Squash Merge and Release Evidence

- Status: Accepted
- Date: 2026-05-12
- Context: OSW needs traceable quality gates without depending on remote CI or
  industrial certification claims.
- Decision: Merge to `develop` requires review score thresholds, clean source
  and target worktrees, QA evidence, artifact checks, and a squash commit. A
  release candidate requires a separate release gate with validation, docs,
  packaging, and claim checks.
- Consequences: Some changes wait for documentation and QA evidence before
  merge, but `develop` remains understandable and release claims stay bounded.

## ADR-0007: Local Harness Scripts Are Advisory Until Wired

- Status: Accepted
- Date: 2026-05-12
- Context: OSW needs local QA commands before remote CI or connector automation
  exists.
- Decision: Harness scripts under `tools/qa/` and hook entrypoints under
  `tools/hooks/` are tracked, local-first, and safe to run without network
  access. They report missing optional tools explicitly.
- Consequences: The harness can gate local work immediately while remaining
  lightweight. Future CI may call the same scripts.

## ADR-0008: License And Tag Gates Require Maintainer Approval

- Status: Accepted for release process; final license remains pending
- Date: 2026-05-14
- Context: OSW v0.1 reached release-readiness review with a placeholder
  `LICENSE`, provisional package license metadata, no local `v0.1*` tag, and
  optional solver/runtime integrations that may carry separate license and
  redistribution obligations.
- Decision: License selection is a maintainer decision and must be completed
  before any public v0.1 tag or announcement. Release planning may document a
  recommended GPL-compatible path, package version scheme, tag naming scheme,
  rollback plan, and artifact policy, but planning prompts must not create tags,
  push tags, finalize public announcements, or bundle external solver binaries.
- Consequences: Public release remains blocked until maintainers finalize the
  license, align `LICENSE`, package metadata, README, release notes, and
  third-party notices, then run a dedicated release/tag prompt. The current
  release plan can clear the version/tag planning blocker without clearing the
  final license blocker.

## ADR-0009: GPL-3.0-or-later Source License For v0.1

- Status: Accepted
- Date: 2026-05-14
- Context: The maintainer supplied an explicit v0.1 license decision:
  repository source license is `GPL-3.0-or-later`, the `LICENSE` file should
  contain the canonical GNU GPL version 3 text, optional external solver
  binaries are not bundled by default, and third-party redistribution
  obligations remain documented through notice review. This is a maintainer
  project decision, not legal advice.
- Decision: OSW v0.1 repository source is licensed as `GPL-3.0-or-later`.
  The repository stores the canonical GNU GPL version 3 text in `LICENSE` and
  records the "or later" grant through package metadata, README wording,
  `docs/13_license_and_version_plan.md`, this decision log, and release
  checklist wording.
- Consequences: Public release metadata can align around `GPL-3.0-or-later`.
  External solver binaries remain optional local tools unless a future packaging
  and redistribution review explicitly approves bundling them.

## ADR-0010: v0.1 Release Candidate Version And Tag Naming

- Status: Accepted
- Date: 2026-05-14
- Context: OSW needs PEP 440 package versions and human-readable Git tag names
  without creating a release tag during metadata finalization.
- Decision: Use PEP 440 release-candidate versions such as `0.1.0rc1`,
  `0.1.0rc2`, and `0.1.0rc3` before final `0.1.0`. Use Git tag names such as
  `v0.1.0-rc1`, `v0.1.0-rc2`, `v0.1.0-rc3`, and `v0.1.0` in dedicated
  release/tag prompts. No tag is created by metadata or release notes prompts.
- Consequences: CLI/package metadata and release notes can describe the release
  candidate consistently while public tag creation remains controlled by a
  separate gate.

## ADR-0011: Local RC Tag Gate Is Separate From Push And Final Release

- Status: Accepted
- Date: 2026-05-14
- Context: OSW v0.1 release-candidate metadata is aligned for package version
  `0.1.0rc1` and local tag name `v0.1.0-rc1`. Creating a local release-candidate
  tag is useful for final inspection, but it must not be confused with pushing a
  public tag, publishing release artifacts, creating the final `v0.1.0` tag, or
  announcing a public release.
- Decision: OSW-AUTO-043 may create a local annotated `v0.1.0-rc1` tag only
  after feature-branch QA, review, squash merge to `develop`, post-merge
  pre-tag QA, clean worktree verification, and tag-object verification pass.
  The final `v0.1.0` tag, any tag push, release artifacts, and public
  announcement require separate maintainer-controlled gates.
- Consequences: A local RC tag is release evidence, not a public release.
  Maintainers can inspect it locally and decide separately whether to push,
  retag for a later RC, or run the final release gate.

## ADR-0012: Release Metadata Checks Have Pre-Tag And RC-Aware Modes

- Status: Accepted
- Date: 2026-05-14
- Context: OSW-AUTO-043 created a valid local annotated `v0.1.0-rc1` tag as
  release evidence. OSW-AUTO-044 then showed that the release metadata checker
  still assumed all metadata checks happen before any local `v0.1*` tag exists.
- Decision: `tools/qa/check_release_metadata.py` supports strict pre-tag mode
  with `--forbid-release-tags` and RC-aware mode with an expected RC tag,
  expected peeled target commit, and annotated-tag requirement. Default checks
  may accept the expected local annotated rc1 tag, but still reject the final
  `v0.1.0` tag and unexpected `v0.1*` tags.
- Consequences: Existing local `v0.1.0-rc1` remains valid OSW-AUTO-043
  evidence. Because OSW-AUTO-044A creates a later commit, rc1 must remain
  local-only and must not be pushed as the current `develop` release candidate;
  the next public/pushable current RC should be produced by an RC2 tag gate.

## ADR-0013: RC2 Supersedes Local RC1 As Current Candidate

- Status: Accepted
- Date: 2026-05-14
- Context: OSW-AUTO-044A advanced `develop` after the local annotated
  `v0.1.0-rc1` tag was created. The rc1 tag still points to the
  OSW-AUTO-043 commit and remains useful local release evidence, but it no
  longer represents current `develop`.
- Decision: OSW-AUTO-045 updates package metadata to `0.1.0rc2` and controls
  creation of a new local annotated `v0.1.0-rc2` tag after merge and
  post-merge pre-tag QA. The existing `v0.1.0-rc1` tag must not be deleted,
  moved, retargeted, recreated, overwritten, or pushed as the current RC.
- Consequences: rc2 becomes the current local release candidate if the gate
  passes. Any public tag push, final `v0.1.0` tag, release artifact, or public
  announcement remains a separate maintainer-controlled gate.

## ADR-0014: Default Pytest Collection Uses Unique Test Basenames

- Status: Accepted
- Date: 2026-05-14
- Context: OSW-AUTO-046 verified local rc2, but default `pytest -q` still failed
  before running tests because the GUI and unit plugin manager dialog tests
  shared the same basename. Importlib mode passed, but the release hardening
  goal is to make the default command work without relying on a global pytest
  import-mode workaround.
- Decision: Test files under `tests/` should have unique basenames. OSW-AUTO-047
  renames the colliding plugin manager dialog tests and adds a local QA helper
  that reports duplicate test basenames without importing test modules.
- Consequences: Default `pytest -q` becomes a normal release-hardening check.
  Since this fix advances `develop` after local rc2, `v0.1.0-rc2` remains
  local historical feedback evidence; any new current RC should use a dedicated
  RC3 tag gate.

## ADR-0015: Documentation Links Are Checked Locally

- Status: Accepted
- Date: 2026-05-14
- Context: The release checklist kept docs link checking as the last known P2
  QA placeholder after default pytest collection was fixed. OSW needs a reusable
  local command that checks repository documentation without making network
  access part of release QA.
- Decision: Add `tools/qa/check_docs_links.py` to validate local Markdown file
  links and anchors in README, CHANGELOG, docs, and examples. External links are
  classified as skipped by default, generated `.codex/reports/` evidence is not
  scanned by default, and fast/pre-merge QA run the checker.
- Consequences: Broken local docs links block QA. External URL freshness remains
  outside this local checker. Since this hardening commit advances `develop`
  after local rc2, `v0.1.0-rc2` stays historical local evidence; a current
  pushable RC requires the RC3 tag gate.

## ADR-0016: RC3 Supersedes Local RC2 As Current Candidate

- Status: Accepted
- Date: 2026-05-19
- Context: OSW-AUTO-047 fixed default `pytest -q` collection and
  OSW-AUTO-048 added the local-only docs link checker after the local annotated
  `v0.1.0-rc2` tag was created. The rc1 and rc2 tags still provide useful
  local release evidence, but neither represents current `develop` after those
  hardening commits.
- Decision: OSW-AUTO-049 updates package metadata to `0.1.0rc3`, preserves
  `v0.1.0-rc1` and `v0.1.0-rc2` unchanged as historical local-only evidence,
  and controls local annotated `v0.1.0-rc3` creation only after merge,
  post-merge pre-tag QA, prior-RC verification, docs-link QA, duplicate
  basename QA, and default pytest pass.
- Consequences: rc3 becomes the current local release candidate if the gate
  passes. Any tag push, final `v0.1.0` tag, release artifact, remote push gate,
  or public announcement remains a separate maintainer-controlled gate.

## ADR-0017: Final v0.1 Metadata Prep Follows RC3 Local UAT

- Status: Accepted
- Date: 2026-05-19
- Context: OSW-AUTO-052 local RC3 UAT passed with no P0 or P1 blockers. The
  local environment lacked PySide6 and optional external solver stacks, so live
  GUI interaction and live solver runs were not claimed; those remain
  environment-specific follow-ups. Automated QA, docs link checking, duplicate
  basename prevention, scope/architecture checks, solver artifact scans, and
  default `pytest -q` passed.
- Decision: OSW-AUTO-053 prepares final package metadata as `0.1.0`, updates
  final release notes and release checklist evidence, and preserves local
  `v0.1.0-rc1`, `v0.1.0-rc2`, and `v0.1.0-rc3` unchanged as historical
  evidence. The final `v0.1.0` tag is deferred to OSW-AUTO-054.
- Consequences: After final metadata prep advances `develop`, rc3 is no longer
  current `develop` HEAD. Final tag creation, tag pushes, release artifacts, and
  public announcements remain separate maintainer-controlled gates.

## ADR-0018: Patch Release Recovery After Source-Install UAT Fix

- Status: Accepted
- Date: 2026-05-19
- Context: OSW-AUTO-054 created a local annotated `v0.1.0` tag at commit
  `da8728adf679314442755ed781c1dd57d1c6ed27` before source-install UAT found
  isolated-venv blockers. OSW-AUTO-056 showed that editable install succeeded,
  but newer tooling exposed `ruff 0.15.13` UP042 failures and five default
  pytest/importlib pytest failures. OSW-AUTO-057 fixed those source-run blockers
  on `develop` at `50e606b869e7a9a9c2e0275c32470c4d011a94a1` without moving,
  deleting, retargeting, or pushing any tag. OSW-AUTO-058 then performed a fresh
  source-install retest: ruff, default pytest, importlib pytest,
  fast/pre-merge QA, docs link checking, duplicate basename checking, and GUI
  offscreen launch all passed with no P0/P1 blockers.
- Decision: Preserve local `v0.1.0` as historical local-only evidence and do
  not publish it as the current release because `develop` is now ahead of that
  tag. The selected recovery path is a patch release sequence:
  `0.1.1rc1` / `v0.1.1-rc1` followed by `0.1.1` / `v0.1.1`, controlled by later
  dedicated version/tag gates. OSW-AUTO-059 records the decision only; it does
  not bump package metadata, create tags, move tags, or push.
- Consequences: Existing `v0.1.0`, `v0.1.0-rc1`, `v0.1.0-rc2`, and
  `v0.1.0-rc3` remain immutable local historical evidence. Public publish of
  `v0.1.0` remains blocked. The next actionable release prompt is
  OSW-AUTO-060 to prepare `0.1.1rc1` metadata and the `v0.1.1-rc1` local tag
  gate path.

## ADR-0019: Patch v0.1.1 RC1 Candidate After Source-Install Recovery

- Status: Accepted
- Date: 2026-05-19
- Context: OSW-AUTO-059 selected the safe patch-release path after OSW-AUTO-058
  verified the OSW-AUTO-057 source-install fixes with no P0/P1 blockers. The
  local annotated `v0.1.0` tag remains historical evidence at
  `da8728adf679314442755ed781c1dd57d1c6ed27`; current `develop` must move
  forward through a new release-candidate version instead of moving or
  publishing that historical tag.
- Decision: Prepare patch release-candidate metadata as package version
  `0.1.1rc1` with local tag name `v0.1.1-rc1`. The RC tag may be created only
  after merge, post-merge QA, fresh source-install validation, historical tag
  preservation checks, and release metadata validation pass. Final `v0.1.1`
  remains deferred to a later final release gate.
- Consequences: `v0.1.0`, `v0.1.0-rc1`, `v0.1.0-rc2`, and `v0.1.0-rc3` remain
  immutable local historical evidence. Public push, final `v0.1.1` tag
  creation, release artifacts, and public announcement remain blocked until
  separate maintainer-controlled gates.

## ADR-0020: Patch RC1 Readiness Wording Cleanup

- Status: Accepted
- Date: 2026-05-19
- Context: OSW-AUTO-060 created local annotated `v0.1.1-rc1` at
  `da1a2c9e2d27674dc4bb85a2800138170c4c4dec` after release metadata checks,
  post-merge QA, and fresh source-install validation passed. OSW-AUTO-061
  verified the tag, package version `0.1.1rc1`, source license metadata,
  default/importlib pytest, ruff, fast QA, pre-merge QA, and source-install
  evidence, but found stale release checklist rows that still described the
  completed RC1 local tag gate as pending.
- Decision: OSW-AUTO-061A corrects release readiness documentation only. It
  marks local `v0.1.1-rc1` creation and verification as PASS, keeps final
  `v0.1.1`, public push, and public announcement blocked, and does not change
  package version, source code, tests, or any tag.
- Consequences: This docs-only merge can advance `develop` beyond the
  `v0.1.1-rc1` tag. Final prep may proceed from docs-clean `develop` only if the
  maintainer accepts this post-RC documentation delta; if exact final-from-current
  RC identity is required, a later dedicated `v0.1.1-rc2` gate should create the
  next current release-candidate tag.

## ADR-0021: Patch v0.1.1 Final Prep From Docs-Clean Develop

- Status: Accepted
- Date: 2026-05-19
- Context: OSW-AUTO-060 created local annotated `v0.1.1-rc1` at
  `da1a2c9e2d27674dc4bb85a2800138170c4c4dec` after source-install validation
  and local QA passed. OSW-AUTO-061A then advanced `develop` only with
  docs/readiness cleanup at `eeac576cc830cf75038127b1fb5d1c178b8b0d6e`. No
  code, version, or tag changed in that cleanup.
- Decision: The maintainer accepts the docs-only post-RC delta for final prep.
  OSW-AUTO-062 prepares final package metadata as `0.1.1`, final release notes,
  final-prep release metadata checks, and final tag gate routing. It preserves
  `v0.1.0`, `v0.1.0-rc1`, `v0.1.0-rc2`, `v0.1.0-rc3`, and `v0.1.1-rc1`
  unchanged and does not create final `v0.1.1`.
- Consequences: Final local `v0.1.1` tag creation remains deferred to
  OSW-AUTO-063. Public push, release artifacts, external solver binary bundles,
  and public announcements remain blocked until separate maintainer-controlled
  gates.

## ADR-0022: GUI Workflow Glue After Parked Local v0.1.1

- Status: Accepted
- Date: 2026-05-21
- Context: OSW-AUTO-063 created local annotated `v0.1.1` at
  `7b232f5003fcc8eb207846570499ffb3442d3197`, and OSW-AUTO-064 parked that
  local final release with no remote publication. OSW-AUTO-065 and OSW-AUTO-066
  then validated that the GUI shell, menus, docks, plugin manager, preview
  states, and report export were credible, but the fully GUI-native
  Import -> Configure/Inspect -> Run/Generate -> Result/Table -> Report flow was
  still limited by API/CLI fallbacks.
- Decision: OSW-AUTO-067 may improve GUI workflow glue on `develop` without
  changing package version, source license, release tags, or remote state. The
  GUI may import/preview supported files into visible project state, select and
  inspect item metadata, call a workflow service for prepare-only workflows and
  optional dependency diagnostics, update table/result/report state, and keep
  `.m` import preview-first. It must not directly execute external solver
  subprocesses or claim live solver runs that were not performed.
- Consequences: After OSW-AUTO-067 merges, `develop` is intentionally ahead of
  the parked local `v0.1.1` tag. That tag remains immutable local release
  evidence and must not be pushed as the current state after post-tag product
  changes. Public publish remains blocked pending a new version/release decision
  such as a later candidate or final gate.

## ADR-0023: Patch v0.1.2 Recovery Path After GUI Workflow Retest

- Status: Accepted
- Date: 2026-05-21
- Context: OSW-AUTO-063 created local annotated `v0.1.1` at
  `7b232f5003fcc8eb207846570499ffb3442d3197` before the GUI workflow glue fix.
  OSW-AUTO-064 parked that local final release with no remote publication.
  OSW-AUTO-067 then improved GUI-native import, project tree, properties,
  run/generate, table/result, and report glue on `develop` at
  `a12812dab77e1d968223a30859a8fa91e2ef0e1d` without moving tags. OSW-AUTO-068
  retested current `develop` and returned `PASS_WITH_LIMITATIONS` with no P0/P1
  blockers: STL, VTU, `.m`, and `.mat` imports created visible project items;
  selection updated type/status/path/diagnostics; Run/Generate produced
  CalculiX, OpenFOAM, Gmsh, CHM, and M-script prepare or diagnostic items; and
  report export included imported files, diagnostics, limitations, CalculiX, and
  OpenFOAM state. The original development goal alignment is now much stronger
  than OSW-AUTO-066, but `develop` is ahead of the local `v0.1.1` tag.
- Decision: Preserve `v0.1.1` as historical local-only final evidence. Do not
  move, retarget, recreate, overwrite, delete, push, or publish `v0.1.1` as the
  current release after the post-tag GUI workflow fix. The selected safe
  recovery path is a new patch sequence: package version `0.1.2rc1` with local
  RC tag `v0.1.2-rc1`, followed later by package version `0.1.2` and final tag
  `v0.1.2`. OSW-AUTO-069 records only this decision; it does not bump version,
  create tags, build artifacts, or push.
- Consequences: Current package metadata remains `0.1.1` until OSW-AUTO-070
  prepares `0.1.2rc1`. Public publish of the existing `v0.1.1` tag remains
  blocked. Existing `v0.1.0`, `v0.1.0-rc1`, `v0.1.0-rc2`, `v0.1.0-rc3`,
  `v0.1.1-rc1`, and `v0.1.1` remain immutable local historical evidence.

## ADR-0024: Patch v0.1.2 RC1 Candidate After GUI Workflow Recovery

- Status: Accepted
- Date: 2026-05-21
- Context: OSW-AUTO-069 selected the safe patch-release recovery path after
  OSW-AUTO-067 advanced `develop` beyond the local `v0.1.1` tag with GUI
  workflow glue and OSW-AUTO-068 retested the result as `PASS_WITH_LIMITATIONS`
  with no P0/P1 blockers. The local `v0.1.1` final tag remains annotated at
  `7b232f5003fcc8eb207846570499ffb3442d3197`; `v0.1.1-rc1` remains at
  `da1a2c9e2d27674dc4bb85a2800138170c4c4dec`; historical `v0.1.0` remains at
  `da8728adf679314442755ed781c1dd57d1c6ed27`.
- Decision: OSW-AUTO-070 prepares package metadata as `0.1.2rc1`, release notes,
  release metadata checker coverage, source-install evidence, and compact GUI
  workflow smoke evidence for the next local RC tag `v0.1.2-rc1`. Historical
  `v0.1.0`, `v0.1.0-rc1`, `v0.1.0-rc2`, `v0.1.0-rc3`, `v0.1.1-rc1`, and
  `v0.1.1` must not be moved, recreated, retargeted, overwritten, deleted, or
  pushed.
- Consequences: The current local patch candidate is `0.1.2rc1` /
  `v0.1.2-rc1`. Final `0.1.2` / `v0.1.2`, public push, release artifacts,
  external solver binary bundles, and public announcements remain blocked until
  later dedicated maintainer gates.

## ADR-0025: Patch v0.1.2 Final Metadata Prep After RC1 Triage

- Status: Accepted
- Date: 2026-05-21
- Context: OSW-AUTO-070 prepared package metadata as `0.1.2rc1`, ran main
  checkout QA, fresh source-install validation, compact GUI workflow validation,
  and created local annotated `v0.1.2-rc1` at
  `28b30c1f79d4c62d160629e96fc1fcefa2382ebe` with no push. OSW-AUTO-071
  triaged RC1 as `NO_FEEDBACK_REPORTED` with no P0/P1 blockers. Remaining
  risks are P2/P3: optional external solver live runs, manual desktop CUA
  depth, Cantera 3.2 deprecation warning, packaging smoke, and external URL
  freshness.
- Decision: OSW-AUTO-072 prepares final package metadata as `0.1.2`, final
  release notes, release metadata checker coverage, fresh source-install
  evidence, and compact GUI workflow evidence. It must preserve historical
  `v0.1.0`, `v0.1.1`, and current `v0.1.2-rc1` local evidence unchanged. It
  must not create the final `v0.1.2` tag, create a new RC tag, push, build
  release artifacts, or create a public announcement.
- Consequences: Final local `v0.1.2` tag creation remains deferred to
  OSW-AUTO-073. Public push, release artifacts, external solver binary bundles,
  and public announcements remain blocked until later dedicated maintainer
  gates.
