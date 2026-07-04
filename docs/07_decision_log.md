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
  maintainer accepts this post-RC documentation delta; if exact final-from-RC
  identity is required, a later dedicated `v0.1.1-rc2` gate should create the
  next release-candidate tag for that historical line.

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

## ADR-0026: Patch v0.1.2 GitHub Source Publish

- Status: Accepted
- Date: 2026-05-26
- Context: OSW-AUTO-073 created local annotated `v0.1.2` at
  `c39f21372ef837f096aa0d430cced82adc6f3485`. OSW-AUTO-075 source smoke passed
  with limitations and no P0/P1 blockers. OSW-AUTO-076E verified a clean publish
  clone and found the GitHub remote ready for first-time publication.
- Decision: OSW-AUTO-077 published only
  `refs/heads/develop:refs/heads/develop` and
  `refs/tags/v0.1.2:refs/tags/v0.1.2` from the clean publish clone. It did not
  push historical `v0.1.0`, `v0.1.1`, or `v0.1.2-rc1` tags, did not run
  `git push --tags`, and did not create release artifacts or announcement text.
- Consequences: The GitHub source release is now published at `develop` and
  `v0.1.2`, both resolving to `c39f21372ef837f096aa0d430cced82adc6f3485`.
  Release artifacts, GitHub Release notes, binary installers, optional solver
  live-run evidence, and public announcement text remain separate
  maintainer-controlled gates.

## ADR-0027: Patch v0.1.3rc1 Metadata And Tag-Only Publish

- Status: Accepted
- Date: 2026-06-02
- Context: The final `v0.1.2` source release was already published at
  `c39f21372ef837f096aa0d430cced82adc6f3485`, then freeze, handoff, and
  release-line reconciliation work advanced local `develop`. OSW-RELEASE-002
  repaired the local editable import path and recommended a new patch candidate
  line instead of moving historical tags.
- Decision: OSW-RELEASE-003 prepares package metadata as `0.1.3rc1` and uses
  Git tag name `v0.1.3-rc1`. OSW-RELEASE-005 creates the annotated local tag,
  OSW-RELEASE-008 pushes only that tag to `origin`, and OSW-RELEASE-009 verifies
  that the remote tag peels to
  `a6e8d3a8211e02359841d10e1947e16ab847b132`. Historical `v0.1.0`, `v0.1.1`,
  `v0.1.2`, and their RC tags remain immutable release evidence.
- Consequences: Branch push, release artifacts, external solver binary bundles,
  GitHub Release creation, and public announcements remain blocked until
  dedicated maintainer gates. `v0.1.3-rc1` must not be moved, deleted,
  retargeted, recreated, force-updated, or pushed again without an explicit
  maintainer gate.

## ADR-0028: VFEA Is Experimental Planning Before Implementation

- Status: Accepted for planning
- Date: 2026-06-06
- Context: After v0.1.4 workflow/product polish closed issues `#15` and `#14`,
  issue `#17` remained as the strategic planning item. Vision-to-FEA can be
  useful for educational model setup, but image and VLM interpretation can
  hallucinate geometry, units, loads, materials, and boundary conditions.
- Decision: Treat VFEA as an experimental plugin planning line, not a core OSW
  solver rewrite. The planning architecture uses drawing/image input, optional
  problem text, a provider layer, `FEASpecCandidate`, `FEASpecValidator`, human
  review, approved FEASpec, ProjectSchema bridge, CalculiX-first export path,
  and ResultDataset/report integration. The forbidden path is automatic
  unreviewed solver execution from image or VLM output. Abaqus export is
  optional/non-default planning only. Topology optimization remains a separate
  future plugin topic.
- Consequences: The next VFEA work should be scope/spec documentation such as
  `OSW-EXP-002_FEASPEC_IR_DESIGN`, not implementation. No provider API keys,
  VLM integration, Abaqus dependency, solver execution, release assets, tags, or
  version metadata changes are part of this decision.

## ADR-0029: v0.1.4 Planned Scope Completion

- Status: Accepted for planning
- Date: 2026-06-06
- Context: Issues `#12`, `#15`, `#14`, and `#17` are closed after v0.1.4
  planning, Plugin Manager UX/install receipts, ResultViewer / FieldViewer
  workflow, and VFEA experimental scope definition landed with evidence. Issues
  `#6` through `#11` remain open in the live optional validation milestone and
  require external solvers or optional Python packages.
- Decision: Treat the planned v0.1.4 workflow/product-polish and VFEA
  scope-definition line as complete. Keep live optional validation separate and
  environment-dependent. This decision does not release `v0.1.4`, bump version
  metadata, create tags, edit the GitHub Release, upload assets, or implement
  VFEA.
- Consequences: The next work should be selected explicitly: FEASpec IR design
  as a new experimental design gate, live optional validation on a suitable
  environment, or release metadata/revalidation planning for the next prerelease
  boundary. No live validation issue is closed by the completion review.

## ADR-0030: Prefer v0.1.4-rc1 For The Next Prerelease Boundary

- Status: Accepted for planning
- Date: 2026-06-06
- Context: The public baseline is `v0.1.3-rc1`, while `develop` now includes
  post-public maintenance, release trust work, onboarding docs, Plugin Manager
  UX/install receipts, ResultViewer / FieldViewer workflow, VFEA experimental
  scope definition, and v0.1.4 completion review. Active metadata still reports
  `0.1.3rc2.dev0`.
- Decision: If maintainers choose release preparation now, prefer
  `v0.1.4-rc1` over `0.1.3rc2` as the next prerelease boundary. The user-facing
  Plugin Manager and ResultViewer / FieldViewer work plus VFEA scope closure
  were planned and closed under the v0.1.4 line.
- Consequences: A later metadata-alignment gate must deliberately update
  package metadata, CLI version, docs, and release notes before any tag or
  release asset work. This decision does not bump version metadata, create tags,
  edit the GitHub Release, upload assets, run live validation, or close issues.

## ADR-0031: Align Metadata To v0.1.4rc1 Before Tagging

- Status: Accepted for release preparation
- Date: 2026-06-06
- Context: ADR-0030 selected `v0.1.4-rc1` as the cleaner next prerelease
  boundary after v0.1.4 planned scope completion. The repository still reported
  package and CLI version `0.1.3rc2.dev0`, while the then-current public release
  remained `v0.1.3-rc1`.
- Decision: Align package metadata, `osw.__version__`, CLI version, release
  metadata QA, changelog, and release docs to candidate version `0.1.4rc1`.
  Treat `v0.1.4-rc1` as the intended future candidate tag, not as an existing
  tag.
- Consequences: Final revalidation, local tag creation, asset build/smoke, and
  GitHub Release publication remain separate gates. This decision does not
  create or push tags, build or upload release assets, edit the GitHub Release,
  run live validation, or close issues.

## ADR-0032: FEASpec IR Is Design-Only Before Implementation

- Status: Accepted for experimental design
- Date: 2026-06-06
- Context: The public `v0.1.4-rc1` prerelease is published and VFEA scope issue
  `#17` is closed. The next experimental line needs a precise FEASpec
  intermediate representation before any Python models, validators, provider
  integrations, ProjectSchema bridge, or solver-adapter work is considered.
- Decision: Define FEASpec as a design-only IR contract with untrusted
  `FEASpecCandidate` data, explicit units, GeometryGraph entities,
  materials/sections, boundary conditions, loads, dimensions, assumptions,
  evidence/confidence, diagnostics, validation states, solver compatibility,
  and serialization examples. Only a human-approved FEASpec may proceed to a
  future ProjectSchema or SolverAdapter handoff. Planning remains
  CalculiX-first, while Abaqus is optional and non-default.
- Consequences: FEASpec and VFEA remain unimplemented. This decision does not
  add source code, VLM APIs, credentials, solver execution, topology
  optimization, release edits, asset uploads, tags, or issue mutation. Future
  implementation gates must preserve the candidate/approved boundary and add
  focused tests before any production behavior is merged.

## ADR-0033: FEASpec Examples And Benchmark Seeds Are Text Fixtures

- Status: Accepted for experimental fixtures
- Date: 2026-06-06
- Context: ADR-0032 defines the FEASpec IR contract, but future Python models
  and validators need deterministic examples and seed fixtures before source
  behavior is implemented. The examples must preserve the same human-review and
  no-execution boundaries as the design document.
- Decision: Add canonical JSON examples and synthetic benchmark seed folders as
  docs/test fixtures only. Examples cover candidate, approved, and invalid
  diagnostic cases. Benchmark seeds contain prompt text, placeholder source
  metadata, approved ground-truth FEASpec-style JSON, and expected metrics for
  future detection work. No images, VLM runs, solver outputs, CalculiX decks,
  or benchmark scores are generated in this gate.
- Consequences: Future implementation gates can use these fixtures for model
  parsing and validator tests. FEASpec and VFEA remain unimplemented, external
  solvers remain optional and unbundled, Abaqus remains optional/non-default,
  and the public release/tag/assets remain unchanged.

## ADR-0034: FEASpec Model Layer Is Experimental And Non-Executing

- Status: Accepted for experimental implementation
- Date: 2026-06-06
- Context: FEASpec examples and benchmark seeds need a Python model layer that
  can load, preserve, basic-check, and serialize the documented JSON without
  jumping ahead to VFEA implementation or solver handoff.
- Decision: Place the first FEASpec models under
  `src/osw/experimental/feaspec/` with standard-library dataclasses, JSON I/O,
  and structural basic checks only. The package may report required-field,
  explicit-unit, geometry-reference, target-reference, and approved-review
  diagnostics. It must not import GUI modules, solver adapters, ProjectSchema
  bridging, VLM provider/API clients, credential handling, or command-execution
  libraries.
- Consequences: Existing examples and benchmark seeds become executable
  compatibility fixtures for parsing and structural diagnostics. Full
  validation, full ProjectSchema persistence, ProjectSchema mutation,
  CalculiX case planning, Abaqus export planning, VLM integration, and any
  solver execution remain separate future gates.

## ADR-0035: FEASpec Validator Contract Precedes Runtime Validation

- Status: Accepted for experimental design
- Date: 2026-06-07
- Context: The FEASpec Python model layer can load, basic-check, and serialize
  examples and benchmark seeds, but it is intentionally structural only. A
  future semantic validator needs stable diagnostic categories, severity
  taxonomy, approval rules, solver handoff blockers, and benchmark readiness
  rules before any runtime validator, full ProjectSchema persistence, schema
  mutation, or solver exporter exists.
- Decision: Define the FEASpec validator as a design-only contract first. The
  contract reserves required diagnostic codes, requires human review before an
  approved FEASpec can proceed toward future solver handoff, keeps
  CalculiX-first compatibility planning, and treats Abaqus as optional and
  non-default only.
- Consequences: Runtime validator implementation, full ProjectSchema
  persistence, ProjectSchema mutation, CalculiX case planning, Abaqus export
  planning, VLM integration, and solver execution remain separate future gates.
  Candidates remain untrusted and must not be treated as solver-ready.

## ADR-0036: FEASpec Semantic Validator Is Field-Level And Non-Executing

- Status: Accepted for experimental implementation
- Date: 2026-06-11
- Context: ADR-0035 reserved the validator contract before runtime validation.
  The next implementation step needs structured diagnostics for existing
  FEASpec models, examples, and benchmark seed fixtures without crossing into
  ProjectSchema conversion, solver export, or execution.
- Decision: Implement an experimental semantic validator report layer under
  `src/osw/experimental/feaspec/` with stable severities, categories,
  diagnostic codes, phase results, approval blockers, solver handoff blockers,
  CalculiX-first field-level compatibility, Abaqus optional/non-default
  diagnostics, and benchmark readiness checks.
- Consequences: Candidates remain untrusted and not solver-ready. The validator
  does not perform full physics validation, numerical rigid-body mode solving,
  mesh generation, full ProjectSchema persistence, ProjectSchema mutation,
  CalculiX or Abaqus export, VLM provider/API integration, credential handling,
  or solver execution. Those remain separate future gates.

## ADR-0037: FEASpec To ProjectSchema Bridge Is Design-Only Before Conversion

- Status: Accepted for experimental design
- Date: 2026-06-11
- Context: The experimental FEASpec model layer and semantic validator report
  layer can represent and diagnose approved FEASpec data, but ProjectSchema
  conversion needs a separate boundary before any source bridge code or schema
  changes are considered.
- Decision: Define the FEASpec to ProjectSchema bridge as a design-only
  contract first. The future bridge must require an approved FEASpec, a
  validator report with no blockers, explicit units, source/provenance/evidence
  preservation, bridge diagnostics, unmapped-field reporting, and clear
  ProjectSchema extension needs. The bridge ends at a ProjectSchema draft and
  diagnostics boundary.
- Consequences: ProjectSchema mutation, full ProjectSchema persistence,
  SolverAdapter/export handoff, CalculiX or Abaqus case generation, VLM
  provider/API integration, credential handling, mesh generation, and solver
  execution remain separate future gates. Candidates remain untrusted, and
  unmapped FEASpec fields must stay visible rather than being silently dropped.

## ADR-0038: FEASpec Bridge Produces Draft Plans Without ProjectSchema Mutation

- Status: Accepted for experimental implementation
- Date: 2026-06-12
- Context: ADR-0037 defined the FEASpec to ProjectSchema bridge boundary. The
  next step needs executable compatibility evidence for approved FEASpec
  examples without changing core ProjectSchema, exporting solver cases, or
  executing external tools.
- Decision: Implement an experimental bridge plan layer under
  `src/osw/experimental/feaspec/`. The bridge accepts only approved FEASpec
  data, validates it with the existing validator report layer, blocks
  candidates and invalid fixtures, returns a draft plan with provenance,
  diagnostics, extension needs, unmapped fields, and a ProjectSchema-compatible
  dictionary, and records that no solver export or solver execution occurred.
- Consequences: Full ProjectSchema persistence, ProjectSchema schema mutation,
  SolverAdapter/exporter calls, CalculiX or Abaqus case generation, VLM
  provider/API integration, credential handling, GUI workflow, and solver
  execution remain separate future gates. The bridge plan is preview evidence,
  not authorization for unreviewed solver handoff.

## ADR-0039: FEASpec To CalculiX Planning Stays Design-Only Before Export

- Status: Accepted for experimental design
- Date: 2026-06-12
- Context: The FEASpec bridge plan layer can produce approved, previewable
  draft evidence, but CalculiX deck generation requires explicit mesh topology,
  element choices, material/section mappings, target sets, and output requests.
  Issue `#8` live `ccx` validation also remains a separate installed-only
  validation track.
- Decision: Define the FEASpec to CalculiX case-plan boundary as design-only.
  The future contract requires approved FEASpec data, validator reports with no
  blockers, bridge plans that are draft-ready or draft-ready-with-warnings,
  explicit units, reviewed material/section/BC/load targets, explicit mesh
  source, CalculiX-first target metadata, and `FC_*` planning diagnostics.
- Consequences: Case-plan model implementation, `.inp` writer design,
  CalculiX exporter implementation, SolverAdapter calls, runner calls, live
  `ccx` validation, dependency install, and solver execution remain separate
  future gates. The planning document is not proof of solver readiness or
  physical correctness.

## ADR-0040: FEASpec CalculiX Case-Plan Model Is Non-Executing

- Status: Accepted for experimental implementation
- Date: 2026-06-12
- Context: ADR-0039 defined the CalculiX-first case-plan boundary. The next
  implementation step needs a serializable planning object that preserves
  approved FEASpec bridge evidence and exposes writer-readiness diagnostics
  without creating solver files or crossing into live validation.
- Decision: Implement `FEASpecCalculiXCasePlan` and `FC_*` diagnostics under
  `src/osw/experimental/feaspec/`. The planner accepts approved FEASpec or
  draft-ready bridge plans, blocks candidates and bridge/validator blockers,
  preserves units, node-like geometry evidence, materials, sections, boundary
  conditions, loads, default static step metadata, output request metadata, and
  provenance comments, and reports `FC_MESH_REQUIRED` until explicit reviewed
  element topology exists.
- Consequences: `ready_for_solver_execution` is always false, examples without
  mesh topology are not writer-ready, and `.inp` writer design, CalculiX export,
  SolverAdapter handoff, runner handoff, live `ccx` validation, ProjectSchema
  mutation, VLM integration, dependency install, and solver execution remain
  separate future gates.

## ADR-0041: FEASpec CalculiX INP Writer Requires A No-Run Design Gate

- Status: Accepted for experimental design
- Date: 2026-06-12
- Context: The FEASpec CalculiX case-plan model can expose writer readiness
  only after approved FEASpec, validator, bridge, explicit node topology,
  explicit element topology, materials, sections, boundary conditions, loads,
  static step metadata, output request metadata, and provenance evidence are
  present. The repository also has existing CalculiX deck and runner layers,
  so the FEASpec writer boundary must be explicit before any renderer code is
  added.
- Decision: Define the FEASpec-to-CalculiX `.inp` writer as design-only before
  implementation. The future writer may render deterministic CalculiX text from
  a `FEASpecCalculiXCasePlan` only when `ready_for_inp_writer` is true, while
  `ready_for_solver_execution` remains false until a separate installed-only
  run gate. The design reserves `FW_*` diagnostics, deterministic section
  ordering, provenance comments, and golden fixture strategy.
- Consequences: No writer implementation, generated `.inp` files, SolverAdapter
  calls, runner calls, ProjectSchema mutation, live `ccx` validation, VLM API,
  dependency install, or solver execution is added by the design gate. Issue
  `#8` remains the separate live CalculiX validation track.

## ADR-0042: FEASpec CalculiX INP Renderer Is No-Run Text Generation

- Status: Accepted for experimental implementation
- Date: 2026-06-12
- Context: ADR-0041 defined the FEASpec CalculiX `.inp` writer contract before
  source behavior. The next implementation step needs deterministic text
  rendering for writer-ready `FEASpecCalculiXCasePlan` records without crossing
  into CalculiX export, SolverAdapter handoff, runner execution, or live issue
  `#8` validation.
- Decision: Implement an experimental no-run renderer under
  `src/osw/experimental/feaspec/`. The renderer accepts only case plans with
  `ready_for_inp_writer=true`, maps incomplete or unsupported records into
  `FW_*` diagnostics, renders deterministic sections in the documented order,
  preserves provenance and no-certification comments, and writes only to
  caller-provided paths with overwrite protection. Every result keeps
  `ready_for_solver_execution=false`.
- Consequences: Approved examples without explicit mesh topology remain
  blocked. No tracked generated `.inp` fixtures, SolverAdapter calls, runner
  calls, `ccx` invocation, subprocess use, ProjectSchema mutation, VLM API,
  dependency install, live validation, release edit, asset upload, tag mutation,
  or issue closure is added by this gate. Golden fixtures, exporter behavior,
  and installed-only runs remain separate future gates.

## ADR-0043: FEASpec CalculiX Golden Fixtures Are No-Run Text Evidence

- Status: Accepted for experimental test evidence
- Date: 2026-06-13
- Context: ADR-0042 added a no-run FEASpec CalculiX INP renderer. Renderer
  behavior needs deterministic regression fixtures, but those fixtures must not
  be confused with CalculiX execution, live issue `#8` validation, solver
  output, or proof of engineering correctness.
- Decision: Add controlled `.inp` golden text fixtures only under
  `tests/fixtures/feaspec/calculix_golden/`, with README and manifest metadata
  stating that the files are no-run renderer regression fixtures. Tests compare
  normalized renderer output against the static text and verify SHA-256
  manifest entries. QA guardrails reject arbitrary `.inp` or solver-output file
  drops outside curated fixture locations.
- Consequences: The fixtures improve renderer regression coverage without
  invoking `ccx`, calling SolverAdapter or runner code, using subprocess APIs,
  mutating ProjectSchema, adding VLM APIs, closing issue `#8`, editing the
  public release, uploading assets, or pushing tags. Exporter and installed-only
  run gates remain separate future work.

## ADR-0044: FEASpec CalculiX Exporter Is A No-Run Bundle Boundary

- Status: Accepted for experimental implementation
- Date: 2026-06-13
- Context: The FEASpec CalculiX renderer can produce deterministic no-run
  `.inp` text for writer-ready case plans, and golden fixtures lock that text.
  The next useful boundary is a safe local export bundle for reviewed files,
  but it must not become live `ccx` validation, SolverAdapter integration,
  runner execution, ProjectSchema mutation, or release asset generation.
- Decision: Implement an experimental no-run exporter under
  `src/osw/experimental/feaspec/`. The exporter wraps successful renderer
  output and writes only caller-directory `.inp`, manifest JSON, diagnostics
  JSON, and `README_RUN_FIRST.txt` files. It records checksums, OSW version,
  release tag context, source FEASpec ID, `solver_execution_performed=false`,
  `ready_for_solver_execution=false`, limitations, `FX_*` diagnostics, safe
  basename checks, missing-directory checks, nonempty-directory checks, and
  overwrite guards.
- Consequences: Issue `#8` remains the separate live CalculiX validation track.
  SolverAdapter calls, runner calls, external command invocation, ProjectSchema
  mutation, dependency install, VLM integration, release edits, asset uploads,
  tag mutation, and issue closure remain separate future gates.

## ADR-0045: FEASpec CalculiX Export Preview CLI Is Diagnostic-Only

- Status: Accepted for experimental CLI implementation
- Date: 2026-06-13
- Context: ADR-0044 added a write-capable no-run export bundle API for
  writer-ready case plans. Users also need a CLI way to inspect readiness,
  diagnostics, and planned bundle names before any write path is called.
- Decision: Add `feaspec-calculix-export-preview` as a diagnostic-only CLI
  command. It reads FEASpec JSON, runs validator, bridge, case-plan, and safe
  in-memory renderer preview layers, emits text or JSON, supports strict
  blocked-preview exit code `2`, and reports planned `.inp`, manifest,
  diagnostics, and README file names without creating them.
- Consequences: The command writes no files, creates no output directories,
  executes no solver, calls no SolverAdapter or runner code, invokes no
  external commands, mutates no ProjectSchema, validates no issue `#8`, and
  stages no runtime export bundles. A future write CLI and installed-only run
  gate remain separate.

## ADR-0046: FEASpec CalculiX Export Write CLI Is A No-Run Local Bundle Boundary

- Status: Accepted for experimental CLI implementation
- Date: 2026-06-13
- Context: ADR-0044 added the no-run exporter API and ADR-0045 added a
  diagnostic-only preview command. Users now need an explicit CLI write command
  that can create a reviewed local export bundle without crossing into
  CalculiX execution, live issue `#8` validation, release asset generation, or
  solver adapter/runner integration.
- Decision: Add `feaspec-calculix-export-write` as an experimental no-run CLI
  command. It accepts FEASpec JSON or an experimental writer-ready
  `FEASpecCalculiXCasePlan` JSON path, requires `--output-dir`, supports text
  and JSON output, blocks unsafe basenames and missing mesh/topology examples,
  honors explicit `--create-dir` and `--overwrite`, and calls only the no-run
  exporter boundary. Successful exports write only `.inp`, manifest JSON,
  diagnostics JSON, and `README_RUN_FIRST.txt` files, with
  `solver_execution_performed=false`.
- Consequences: The command does not run `ccx`, call SolverAdapter or runner
  code, invoke external commands, mutate ProjectSchema, validate issue `#8`,
  install dependencies, edit releases/assets, push tags, add VLM APIs, or stage
  runtime export bundles. Installed-only run validation and human-review UI
  work remain separate future gates.

## ADR-0047: FEASpec CalculiX Result Import And Run Gates Stay Separate

- Status: Accepted for experimental design
- Date: 2026-06-13
- Context: The FEASpec CalculiX no-run exporter and CLI write command can
  create a local reviewed export bundle, but the next post-export flow must not
  blur bundle writing, human review, installed-only solver runs, result import,
  ResultDataset/report summary, and live issue `#8` validation.
- Decision: Record a design-only result import / run gate sequence. FEASpec
  human review, no-run export preview, no-run export write, optional manual
  inspection, installed-only run, result import, and ResultDataset/report
  summary remain separate gates. The design defines run preconditions and
  outputs, explicit result import inputs and outputs, `FR_*` and `FI_*`
  diagnostics, ResultDataset mapping, path-safety rules, and issue `#8`
  separation.
- Consequences: This decision does not implement result import, run commands,
  SolverAdapter or runner integration, subprocess or external command
  invocation, ProjectSchema mutation, dependency install, live `ccx`
  validation, release mutation, asset upload, tag mutation, or issue closure.
  Result import and installed-only run behavior require separate future gates.

## ADR-0048: FEASpec Human Review Record Is A Data Boundary

- Status: Accepted for experimental implementation
- Date: 2026-06-18
- Context: The FEASpec CalculiX no-run exporter and result import / run gate
  design depend on auditable human-review evidence, but the repository still
  needs to keep GUI approval, CLI approval, installed-only run behavior, result
  import, SolverAdapter handoff, runner handoff, and live issue `#8`
  validation as separate gates.
- Decision: Add an experimental FEASpec human review record model under
  `src/osw/experimental/feaspec/`. The record captures reviewer state/action,
  source FEASpec id, validator summary/hash, accepted-warning reasons,
  diagnostic decisions, bridge/case/export summaries, acknowledgements, and
  solver-execution flags in JSON-serializable form. The model requires
  `solver_execution_performed=false` and treats installed-only run request
  approval as intent only, not execution.
- Consequences: Human review evidence can be summarized and persisted as JSON,
  but no GUI, CLI approval command, result importer, run gate, SolverAdapter or
  runner integration, subprocess or external command invocation, ProjectSchema
  mutation, VLM API, dependency install, live `ccx` validation, release
  mutation, asset upload, tag mutation, or issue closure is added by this gate.

## ADR-0049: FEASpec Human Review CLI Is Record-Only

- Status: Accepted for experimental CLI implementation
- Date: 2026-06-18
- Context: ADR-0048 added JSON-serializable human-review records, and the
  no-run FEASpec CalculiX export preview/write commands need a CLI way to
  capture reviewer decisions without crossing into GUI approval, result import,
  installed-only run behavior, SolverAdapter handoff, runner handoff, or live
  issue `#8` validation.
- Decision: Add `feaspec-human-review-create`,
  `feaspec-human-review-validate`, and `feaspec-human-review-summary` as
  experimental record-only CLI commands. The create command validates before
  writing one explicit review JSON file, refuses overwrite unless requested,
  supports text and JSON output, requires accepted-warning reasons, blocks
  approval when validator blockers/errors are present, and keeps
  `solver_execution_performed=false`.
- Consequences: The CLI workflow does not implement a GUI, result importer,
  run gate, SolverAdapter or runner integration, subprocess or external command
  invocation, ProjectSchema mutation, VLM API, dependency install, live `ccx`
  validation, release mutation, asset upload, tag mutation, issue mutation, or
  solver execution. No-run export and installed-only run gates remain separate.

## ADR-0050: FEASpec Human Review GUI Dialog Starts As Design-Only

- Status: Accepted for experimental design
- Date: 2026-06-18
- Context: ADR-0048 added the human-review record model and ADR-0049 added
  record-only CLI commands. A future GUI surface needs to present the same
  review states, diagnostics, warning acceptance, approval gating, record
  preview, and save behavior while preserving OSW's GUI safety rule against
  direct solver execution.
- Decision: Define the FEASpec human review GUI dialog as a design-only
  contract before adding any PySide6 source. The future dialog may map FEASpec
  files, no-run export preview summaries, no-run export write summaries, and
  future project context into read-only evidence panels plus explicit review
  actions. It must show disabled action reasons, keep blocker diagnostics
  unacceptably blocking, and keep CLI/GUI review semantics aligned.
- Consequences: No GUI implementation, result import implementation, run gate
  implementation, SolverAdapter or runner integration, subprocess or external
  command invocation, ProjectSchema mutation, VLM API, dependency install, live
  `ccx` validation, release mutation, asset upload, tag mutation, issue
  mutation, or solver execution is added by this design gate. View-model,
  widget implementation, save integration, and installed-only run behavior
  require separate future gates.

## ADR-0051: FEASpec Human Review Dialog View-Model Is UI-Agnostic

- Status: Accepted for experimental implementation
- Date: 2026-06-18
- Context: ADR-0050 defined the future GUI dialog contract without PySide6
  source. The next implementation step needs deterministic state and action
  availability evidence that a later GUI can bind to while preserving CLI/GUI
  semantics and the no-solver-execution boundary.
- Decision: Add a pure Python FEASpec human review dialog view-model under
  `src/osw/experimental/feaspec/`. The view-model computes panel identifiers,
  diagnostic rows, warning rows, action availability with disabled reasons,
  record preview, and save-plan path analysis from human-review evidence. It
  exports only UI-agnostic state objects and helper functions.
- Consequences: No PySide/Qt or GUI source, result import implementation, run
  gate implementation, SolverAdapter or runner integration, subprocess or
  external command invocation, ProjectSchema mutation, VLM API, dependency
  install, live `ccx` validation, issue mutation, release mutation, asset
  upload, tag mutation, or solver execution is added by this gate. Runtime GUI
  widgets, save integration, result import, and installed-only run behavior
  remain separate future gates.

## ADR-0052: FEASpec Human Review GUI Dialog Is Read-Only

- Status: Accepted for experimental implementation
- Date: 2026-06-18
- Context: ADR-0051 added the pure Python human-review dialog view-model. The
  next GUI slice needs a small PySide6 surface that displays the same review
  evidence without crossing into save integration, result import, run gates, or
  solver execution.
- Decision: Add `FEASpecHumanReviewDialog` under `src/osw/gui/dialogs/` as a
  read-only binding to the view-model. The dialog renders source evidence,
  diagnostics, warning rows, engineering/export summaries, action disabled
  reasons, safety copy, and record preview. Save remains disabled in this
  gate.
- Consequences: No record save integration, file dialog, result import
  implementation, installed-only run gate implementation, SolverAdapter or
  runner integration, subprocess or external command invocation, ProjectSchema
  mutation, VLM API, dependency install or upgrade, live `ccx` validation,
  issue mutation, release mutation, asset upload, tag mutation, or solver
  execution is added by this gate. Save integration, result import, and
  installed-only run behavior remain separate future gates.

## ADR-0053: FEASpec Human Review GUI Save Is Explicit JSON Only

- Status: Accepted for experimental implementation
- Date: 2026-06-18
- Context: ADR-0052 added a read-only PySide6 dialog around the human-review
  view-model. The next safe mutation is review-record persistence, but it must
  not become a file browser, export writer, result importer, run gate, or
  solver execution surface.
- Decision: Add GUI save behavior only for explicit caller-provided JSON paths.
  The dialog uses the existing view-model save plan and `dump_human_review_record`,
  validates the record preview before writing, refuses unacknowledged
  overwrites, and never creates parent directories implicitly.
- Consequences: The GUI can write one FEASpec human-review JSON record under a
  caller-provided path. It still adds no file dialog, export bundle write,
  `.inp` write, result import implementation, installed-only run gate,
  SolverAdapter or runner integration, subprocess or external command
  invocation, ProjectSchema mutation, VLM API, dependency install or upgrade,
  live `ccx` validation, issue mutation, release mutation, asset upload, tag
  mutation, or solver execution.

## ADR-0054: FEASpec Human Review File Dialog Starts As Design-Only

- Status: Accepted for experimental design
- Date: 2026-06-18
- Context: ADR-0053 added explicit caller-path JSON save behavior to the
  FEASpec human-review dialog. A future GUI may need a path chooser for that
  JSON record, but the chooser must not become export-bundle writing, result
  import, run-gate behavior, or solver execution.
- Decision: Define the future file-dialog behavior as design-only before any
  `QFileDialog` source is added. The design covers entry points, default
  filename sanitization, JSON filters, directory policy, overwrite
  confirmation, path safety, save-plan integration, error handling, and future
  implementation tests. The actual write path must continue to use the
  existing explicit JSON save integration.
- Consequences: No file dialog implementation, GUI source mutation, export
  bundle write, `.inp` write, result import implementation, installed-only run
  gate, SolverAdapter or runner integration, subprocess or external command
  invocation, ProjectSchema mutation, VLM API, dependency install or upgrade,
  live `ccx` validation, issue mutation, release mutation, asset upload, tag
  mutation, or solver execution is added by this gate. Future file-dialog
  implementation requires a separate prompt and focused GUI tests.

## ADR-0055: FEASpec Human Review File Dialog Is Review-Record JSON Only

- Status: Accepted for experimental implementation
- Date: 2026-06-18
- Context: ADR-0054 defined the path chooser contract for the human-review
  GUI. The next safe implementation step is a file dialog for selecting one
  review-record JSON save path while preserving the existing save integration
  and avoiding export/run/result behavior.
- Decision: Add a mockable `QFileDialog.getSaveFileName` path chooser to
  `FEASpecHumanReviewDialog`. The chooser uses a deterministic sanitized
  default filename, a narrow JSON filter, cancel no-op behavior, missing-parent
  guards, non-JSON and `.inp` rejection, explicit overwrite confirmation, and
  the existing view-model save plan.
- Consequences: Choosing a path writes nothing. The GUI can still write only
  one validated FEASpec human-review JSON record through the existing save
  integration. This gate adds no export bundle write, `.inp` write, result
  import implementation, installed-only run gate, SolverAdapter or runner
  integration, subprocess or external command invocation, ProjectSchema
  mutation, VLM API, dependency install or upgrade, live `ccx` validation,
  issue mutation, release mutation, asset upload, tag mutation, or solver
  execution.

## ADR-0056: FEASpec CalculiX Run Gate Is Installed-Only And Explicit

- Status: Accepted for experimental implementation
- Date: 2026-06-18
- Context: The FEASpec no-run export bundle, human-review evidence, and
  result-import/run-gate design define a path toward local CalculiX execution,
  but the first implementation must not become a solver installer, broad
  runner framework, ResultDataset importer, SolverAdapter handoff, GUI run
  button, ProjectSchema mutation, live issue `#8` closure, or release
  mutation.
- Decision: Add an experimental installed-only run gate under
  `src/osw/experimental/feaspec/`. The gate inspects an existing no-run export
  bundle, defaults to dry-run, discovers only an already installed `ccx`,
  requires explicit execute, run confirmation, README acknowledgement, timeout,
  and isolated run directory before subprocess execution, then records stdout,
  stderr, and `run_metadata.json` under the run directory. The CLI surface is
  `feaspec-calculix-run-installed-only`; tests use fake `ccx` shims for
  success, nonzero exit, timeout, missing executable, diagnostics, and JSON/text
  CLI behavior.
- Consequences: Real `ccx` smoke remains installed-only and
  environment-dependent; issue `#8` stays open until a prepared validation gate
  records live evidence. This gate adds no solver installation, dependency
  installation, result import, SolverAdapter or broad runner integration,
  ProjectSchema mutation, GUI direct execution, VLM API, release edit, asset
  upload/delete, tag mutation, issue creation, or issue closure.

## ADR-0057: FEASpec CalculiX Result Import Starts As Metadata-Only Planning

- Status: Accepted for experimental implementation
- Date: 2026-06-18
- Context: ADR-0047 separated FEASpec no-run export, installed-only run, result
  import, ResultDataset/report summary, and live issue `#8` validation. ADR-0056
  added an installed-only run gate that can write run metadata and logs, but the
  next result step must not become a `.frd`/`.dat` parser, ResultDataset
  persistence layer, solver retry path, SolverAdapter integration, runner
  refactor, ProjectSchema mutation, or live validation claim.
- Decision: Add an experimental FEASpec CalculiX result import model under
  `src/osw/experimental/feaspec/`. The model accepts an explicit result
  directory, reads JSON run/export metadata, classifies known CalculiX artifacts
  by suffix, records file size and SHA-256, emits `FI_*` diagnostics, preserves
  provenance, and builds a pure in-memory ResultDataset draft with artifact and
  field references.
- Consequences: The model does not parse numerical `.frd`, `.dat`, `.sta`, or
  `.cvg` contents, write ResultDataset files, perform CLI write behavior,
  execute CalculiX, call SolverAdapter or runner code, mutate ProjectSchema,
  install dependencies, add VLM APIs, validate issue `#8`, mutate
  releases/assets/tags, or close issues. Parser design, CLI preview,
  ResultDataset persistence, and live prepared-machine validation remain
  separate gates.

## ADR-0058: FEASpec CalculiX Result Import CLI Is Preview-Only

- Status: Accepted for experimental implementation
- Date: 2026-06-18
- Context: ADR-0057 added a metadata-only result import model that can inspect
  explicit CalculiX result directories and build an in-memory ResultDataset
  draft. The next useful surface is a CLI preview for reviewers, but it must not
  become a numerical parser, ResultDataset persistence path, solver retry/run
  path, SolverAdapter handoff, ProjectSchema mutation, or live issue `#8`
  validation claim.
- Decision: Add `feaspec-calculix-result-import-preview` as an experimental
  preview-only CLI command. It requires `--result-dir`, supports text or JSON
  output, can hide top-level artifacts/diagnostics, and returns strict exit code
  `2` when blocked, unsupported, or future-parser cases should fail automation.
  The command reports top-level `solver_execution_performed=false` for the
  preview itself while preserving source run metadata under provenance.
- Consequences: The preview writes no files, persists no ResultDataset, parses
  no numerical `.dat` or `.frd` content, executes no CalculiX process, calls no
  SolverAdapter or runner code, mutates no ProjectSchema, installs no
  dependencies, adds no VLM APIs or credentials, validates no issue `#8`,
  mutates no release/tag/asset state, and closes no issues. Numerical parser
  design, ResultDataset persistence, and live prepared-machine validation
  remain separate gates.

## ADR-0059: FEASpec CalculiX STA/CVG Status Scanner Is Text-Only

- Status: Accepted for experimental implementation
- Date: 2026-06-19
- Context: The result import model and CLI preview can classify existing
  CalculiX artifacts but still need safe status/progress evidence from `.sta`
  and `.cvg` files. This must not become numerical result parsing, convergence
  value interpretation, ResultDataset persistence, SolverAdapter handoff, runner
  integration, or live issue `#8` validation.
- Decision: Add an experimental text-only status scanner under
  `src/osw/experimental/feaspec/`. The scanner accepts explicit `.sta` and
  `.cvg` files, preserves metadata scanner size/hash/line evidence, classifies
  progress, convergence-message, warning, error, completion, failure,
  informational, and unknown lines, records bounded snippets and category
  counts, and integrates status summaries into result-import previews.
- Consequences: Numeric-looking convergence tokens remain text snippets and are
  not parsed as values. The scanner writes no files, parses no `.dat`/`.frd`
  numerical content, executes no solver, calls no SolverAdapter or runner code,
  mutates no ProjectSchema, installs no dependencies, adds no VLM APIs or
  credentials, validates no issue `#8`, mutates no release/tag/asset state, and
  closes no issues. Numerical parsers and live prepared-machine validation
  remain separate future gates.

## ADR-0060: FEASpec CalculiX DAT Parser Starts With A Minimal Design

- Status: Accepted for experimental design
- Date: 2026-06-19
- Context: Metadata and status scanning can classify CalculiX result artifacts,
  but `.dat` output can contain broad, solver-version-dependent text tables and
  numeric values. The next step needs a safe subset before any parser code can
  be reviewed.
- Decision: Define a design-only `.dat` minimal parser contract before
  implementation. The future parser may accept only explicit `.dat` files,
  known educational headings, bounded scalar summary candidates, and bounded
  small text-table candidates with line provenance. Unknown sections,
  ambiguous unitless values, oversized tables, malformed numeric cells, and
  missing units must produce `FP_DAT_*` diagnostics rather than hidden success.
- Consequences: This gate adds no `.dat` parser implementation, numerical
  extraction, ResultDataset persistence, SolverAdapter or runner integration,
  subprocess invocation, ProjectSchema mutation, dependency install, VLM API,
  release mutation, asset upload, tag mutation, issue mutation, live issue `#8`
  validation, bundled-solver claim, or certification claim. Implementation and
  live validation require separate future gates.

## ADR-0061: FEASpec CalculiX DAT Section Scanner Is Metadata-Only

- Status: Accepted for experimental implementation
- Date: 2026-06-19
- Context: ADR-0060 defined a minimal `.dat` parser design, but full `.dat`
  numeric parsing, table extraction, and unit handling remain too broad for the
  first implementation slice. The result import model can still benefit from
  section-level evidence for review previews.
- Decision: Add a `.dat` metadata section scanner under
  `src/osw/experimental/feaspec/`. It accepts explicit `.dat` files, preserves
  metadata scanner evidence, identifies conservative heading text, section
  spans, section kinds, unsupported and unknown sections, bounded snippets, and
  section counts, then attaches `dat_section_summary` metadata to result-import
  previews.
- Consequences: Numeric-looking tokens remain snippets and are not extracted as
  values. Table-like headings remain candidates and rows/columns are not
  extracted. The scanner infers no units, writes no files, persists no
  ResultDataset, executes no solver, calls no SolverAdapter or runner code,
  mutates no ProjectSchema, installs no dependencies, adds no VLM APIs or
  credentials, validates no issue `#8`, mutates no release/tag/asset state, and
  closes no issues. Minimal `.dat` value parsing and live prepared-machine
  validation remain separate future gates.

## ADR-0062: FEASpec CalculiX DAT Minimal Parser Is Bounded And Preview-Only

- Status: Accepted for experimental implementation
- Date: 2026-06-19
- Context: ADR-0061 provides section-level `.dat` evidence. The next parser
  slice can safely add value previews only for explicit, reviewed candidate
  sections without broadening into free-form CalculiX output parsing.
- Decision: Add a minimal `.dat` parser under
  `src/osw/experimental/feaspec/`. It consumes section-scanner output, accepts
  only explicit scalar candidates in `label = value unit` or
  `label: value unit` form, and accepts only small delimited table candidates
  with explicit unit rows or caller-provided `unit_context`. It preserves raw
  text, line provenance, section headings, diagnostics, and limitation flags,
  then exposes in-memory candidate summaries through the result import model
  and preview CLI.
- Consequences: This parser is not a free-form `.dat` parser, not an `.frd`
  parser, and not live CalculiX validation. It infers no units, reconstructs no
  mesh or field data, writes no ResultDataset files, executes no solver, calls
  no SolverAdapter or runner code, mutates no ProjectSchema, installs no
  dependencies, adds no VLM APIs or credentials, mutates no release/tag/asset
  state, and closes no issues. ResultDataset persistence, `.frd` parsing, and
  prepared-machine issue `#8` validation remain separate future gates.

## ADR-0063: FEASpec CalculiX FRD Block Scanner Starts As Design-Only

- Status: Accepted for experimental design
- Date: 2026-06-19
- Context: The result import path can now classify artifacts, scan `.sta` /
  `.cvg` status text, scan `.dat` sections, and parse a bounded `.dat` subset.
  `.frd` files can contain field arrays and mesh-related records that are too
  broad for an unreviewed parser implementation.
- Decision: Define a design-only `.frd` block scanner contract before adding
  code. The future scanner may identify block boundaries, block kinds, labels,
  field-reference candidates, mesh-reference candidates, unsupported blocks,
  diagnostics, provenance, and limitations. It must not parse numerical field
  values, reconstruct mesh topology, infer units, write ResultDataset files, or
  claim solver correctness.
- Consequences: This gate adds no `.frd` parser implementation, numerical field
  parsing, mesh reconstruction, ResultDataset persistence, SolverAdapter or
  runner integration, subprocess invocation, ProjectSchema mutation, dependency
  install, VLM API, release mutation, asset upload, tag mutation, issue
  mutation, live issue `#8` validation, bundled-solver claim, or certification
  claim. Implementation and live validation require separate future gates.

## ADR-0064: FEASpec CalculiX FRD Block Scanner Is Metadata-Only

- Status: Accepted for experimental implementation
- Date: 2026-06-19
- Context: The result import path can already enrich `.dat` artifacts with
  bounded explicit preview candidates and `.sta` / `.cvg` artifacts with
  text-only status summaries. `.frd` artifacts still need safer visibility for
  block boundaries and deferred references without parsing field values or
  rebuilding mesh topology.
- Decision: Implement a `.frd` block metadata scanner that records block labels,
  spans, block kinds, unsupported and unknown records, bounded snippets, and
  deferred reference candidates only. The scanner is integrated into result
  import artifact metadata and CLI preview summaries.
- Consequences: This gate adds no numerical `.frd` field parser, node or
  element value arrays, mesh reconstruction, visualization arrays, unit
  inference, ResultDataset persistence, SolverAdapter or runner integration,
  subprocess invocation, ProjectSchema mutation, dependency install, VLM API,
  release mutation, asset upload, tag mutation, issue mutation, live issue `#8`
  validation, bundled-solver claim, or certification claim.

## ADR-0065: FEASpec CalculiX ResultDataset Draft Mapping Is In-Memory

- Status: Accepted for experimental implementation
- Date: 2026-06-19
- Context: The result import path can now classify artifacts, summarize
  `.sta` / `.cvg` text status, parse a bounded `.dat` subset, and preserve
  `.frd` block-reference metadata. A stable handoff shape is needed before any
  reviewed ResultDataset persistence gate.
- Decision: Add an in-memory ResultDataset draft mapping layer under
  `src/osw/experimental/feaspec/`. It maps result-import artifacts, status
  summaries, bounded `.dat` scalar/table candidates, deferred `.frd`
  references, provenance, diagnostics, and limitations into a serializable
  draft payload and compact summary for the CLI preview.
- Consequences: This gate adds no ResultDataset persistence or file writes, no
  CLI persistence behavior in the mapping layer, no additional `.frd` numerical field parsing,
  no mesh reconstruction, no unit inference, no solver execution, no
  SolverAdapter or runner integration, no subprocess invocation, no
  ProjectSchema mutation, no dependency install, no VLM API, no release/tag or
  asset mutation, no issue mutation, no live issue `#8` validation, and no
  bundled-solver or certification claim.

## ADR-0066: FEASpec CalculiX ResultDataset Write Flow Is Design-Only

- Status: Accepted for experimental design
- Date: 2026-06-19
- Context: The result import path can now build an in-memory ResultDataset draft
  mapping from artifact metadata, status summaries, bounded `.dat` candidates,
  deferred `.frd` references, provenance, diagnostics, and limitations. A
  reviewed persistence contract is needed before any file-writing implementation
  can be considered.
- Decision: Add a design-only ResultDataset write contract that defines future
  output layout, schema/versioning, explicit path and overwrite policy,
  atomic-write strategy, artifact reference policy, validation-before-write
  rules, CLI/GUI future entry points, and `FDW_*` diagnostics.
- Consequences: This gate adds no ResultDataset persistence implementation, no
  file writes, no CLI or GUI implementation, no atomic-write
  code, no schema implementation, no `.frd` numerical field parsing, no mesh
  reconstruction, no solver execution, no SolverAdapter or runner integration,
  no subprocess invocation, no ProjectSchema mutation, no dependency install,
  no VLM API, no release/tag or asset mutation, no issue mutation, no live issue
  `#8` validation, and no bundled-solver or certification claim.

## ADR-0067: FEASpec CalculiX ResultDataset Write Planning Is In-Memory

- Status: Accepted for experimental implementation
- Date: 2026-06-20
- Context: ADR-0066 defined the reviewed persistence contract for
  ResultDataset drafts, but actual persistence remains too risky without a
  smaller planning model. The result import path can build a reviewed
  in-memory draft mapping, and the next safe slice is to validate output intent,
  path policy, artifact references, diagnostics, provenance, and limitations
  acknowledgement before any write-capable command exists.
- Decision: Add an experimental in-memory ResultDataset write plan model under
  `src/osw/experimental/feaspec/`. The planner consumes draft mappings,
  records explicit output-directory readiness, planned standard files, future
  atomic write paths, artifact references, and `FDW_*` diagnostics, and exposes
  validation/explanation helpers. All write flags remain false.
- Consequences: This gate adds no actual ResultDataset persistence, no file
  writes, no directory creation, no artifact copying, no CLI behavior in the
  write-plan model, no GUI behavior, no schema migration implementation, no `.frd` numerical
  field parsing, no mesh reconstruction, no solver execution, no SolverAdapter
  or runner integration, no subprocess invocation, no ProjectSchema mutation,
  no dependency install, no VLM API, no release/tag or asset mutation, no issue
  mutation, no live issue `#8` validation, and no bundled-solver or
  certification claim.

## ADR-0068: FEASpec CalculiX ResultDataset Schema Payloads Are In-Memory

- Status: Accepted for experimental implementation
- Date: 2026-06-20
- Context: ADR-0067 added an in-memory write plan for reviewed ResultDataset
  drafts. A future persistence gate still needs stable JSON-shaped payload
  records for the ResultDataset body, manifest, diagnostics, provenance, and
  review README before any file-writing implementation or CLI write surface can
  be reviewed.
- Decision: Add an experimental in-memory ResultDataset schema payload model
  under `src/osw/experimental/feaspec/`. The model consumes the reviewed draft
  mapping and write plan, assembles deterministic payload records, validates
  schema/provenance/artifact/manifest readiness with `FDS_*` diagnostics, and
  exposes explanation helpers. All persistence and write flags remain false.
- Consequences: This gate adds no actual ResultDataset persistence, no file
  writes, no directory creation, no artifact copying, no CLI behavior in the
  schema model, no GUI behavior, no atomic write implementation, no `.frd` numerical
  field parsing, no mesh reconstruction, no solver execution, no SolverAdapter
  or runner integration, no subprocess invocation, no ProjectSchema mutation,
  no dependency install, no VLM API, no release/tag or asset mutation, no issue
  mutation, no live issue `#8` validation, and no bundled-solver or
  certification claim.

## ADR-0069: FEASpec CalculiX ResultDataset Writer Is Library-Only

- Status: Accepted for experimental implementation
- Date: 2026-06-20
- Context: ADR-0067 and ADR-0068 added the reviewed write plan and deterministic
  schema payload records needed for ResultDataset persistence, but no file
  writer existed. The next useful slice is explicit library persistence for
  already reviewed plan/schema payloads without adding an import-write CLI or
  GUI path.
- Decision: Add an experimental library-only ResultDataset writer under
  `src/osw/experimental/feaspec/`. The writer validates the write plan and
  schema payload, writes exactly `result_dataset.json`,
  `result_dataset_manifest.json`, `diagnostics.json`, `provenance.json`, and
  `README_REVIEW_FIRST.txt` under the caller-reviewed output directory, uses
  temp-file plus replace behavior, returns file size/SHA-256 metadata, and
  blocks unplanned collisions, blocked plans, blocked schema payloads, and
  artifact-copy requests.
- Consequences: This gate adds actual library file writes only for the five
  standard ResultDataset review files. It contains no CLI or GUI behavior,
  copies no original solver artifacts, parses no additional
  numerical results, executes no solver, calls no SolverAdapter or runner code,
  invokes no external commands, mutates no ProjectSchema, installs no
  dependencies, adds no VLM API, mutates no release/tag or asset state, creates
  or closes no issues, records no live issue `#8` validation, and makes no
  bundled-solver or certification claim.

## ADR-0070: FEASpec CalculiX Result Import Write CLI Starts As Design-Only

- Status: Accepted for experimental design
- Date: 2026-06-20
- Context: ADR-0067, ADR-0068, and ADR-0069 provide the reviewed write plan,
  schema payload, and library writer needed for ResultDataset persistence, but
  exposing that persistence through a CLI needs a separate review contract
  before implementation.
- Decision: Define the future
  `feaspec-calculix-result-import-write` command as a design-only gate. The
  proposed command defaults to plan-only review, requires explicit result and
  output directories, records future acknowledgements for limitations, review,
  overwrite, and directory creation, defines text/JSON output and exit codes,
  and may call the library writer only in a later implementation gate when an
  explicit future `--write` mode and all preconditions are satisfied.
- Consequences: This gate registers no CLI command, changes no library writer
  behavior, writes no ResultDataset files, copies no original solver artifacts,
  parses no additional numerical results, executes no solver, calls no
  SolverAdapter or runner code, invokes no external commands, mutates no
  ProjectSchema, installs no dependencies, adds no VLM API, mutates no
  release/tag or asset state, creates or closes no issues, records no live
  issue `#8` validation, and makes no bundled-solver or certification claim.

## ADR-0071: FEASpec CalculiX Result Import Write CLI Implementation

- Status: Accepted for experimental implementation
- Date: 2026-06-20
- Context: ADR-0070 defined the review-gated command contract after the
  ResultDataset draft mapping, write plan, schema payload, and library writer
  layers were in place. The next bounded slice is to expose that reviewed
  persistence stack through a CLI without adding GUI write behavior, artifact
  copying, solver execution, or ProjectSchema mutation.
- Decision: Register `feaspec-calculix-result-import-write` as an experimental
  command. The command defaults to plan-only review, requires explicit
  `--write`, `--output-dir`, `--acknowledge-limitations`, and
  `--acknowledge-review-required` before invoking the library writer, and
  reports text/JSON status, diagnostics, planned files, written files, and
  safety flags.
- Consequences: The command writes only the standard ResultDataset review files
  through the existing library writer when all review gates pass. It copies no
  original solver artifacts, parses no additional numerical results, executes
  no solver, calls no SolverAdapter or runner code, invokes no external
  commands, mutates no ProjectSchema, installs no dependencies, adds no VLM
  API, mutates no release/tag or asset state, creates or closes no issues,
  records no live issue `#8` validation, and makes no bundled-solver or
  certification claim.

## ADR-0072: FEASpec CalculiX Result Import Write GUI Starts As Design-Only

- Status: Accepted for experimental design
- Date: 2026-06-20
- Context: ADR-0071 exposed the reviewed ResultDataset write stack through a
  CLI while deliberately leaving GUI write behavior absent. The next bounded
  step is to define the future GUI workflow contract before any PySide6 source,
  file-dialog, or persistence wiring is added.
- Decision: Add a design-only future GUI contract for FEASpec CalculiX result
  import writes. The contract defines preview entry points, a future
  ResultDataset write dialog, project-context entry behavior, panels/tabs,
  action states, disabled reasons, explicit output-directory file-dialog
  policy, limitations/review/overwrite/create-directory acknowledgements,
  CLI/GUI consistency, and future implementation tests.
- Consequences: This gate adds no GUI source, no file-dialog implementation,
  no CLI behavior change, no library writer change, no ResultDataset file
  write, no artifact copy, no solver execution, no SolverAdapter or runner
  integration, no subprocess use, no ProjectSchema mutation, no VLM API, no
  dependency install, no release/tag or asset mutation, no issue mutation, no
  live issue `#8` validation, and no bundled-solver or certification claim.

## ADR-0073: FEASpec CalculiX Result Write View-Model Is UI-Agnostic

- Status: Accepted for experimental implementation
- Date: 2026-06-20
- Context: ADR-0072 defined the future ResultDataset write GUI workflow while
  keeping GUI source and file-dialog behavior out of scope. The next bounded
  slice is a pure state layer that a future GUI can bind to without adding
  PySide/Qt dependencies or hidden persistence behavior.
- Decision: Add `calculix_result_write_viewmodel.py` as a UI-agnostic
  state/action model over existing result-import, draft-mapping, write-plan,
  schema-payload, and optional writer-result records. It computes panels, rows,
  action states, disabled reasons, acknowledgements, preview records, and
  lexical save-path plans.
- Consequences: The view-model adds no GUI dialog, no file dialog, no
  `QFileDialog`, no writer invocation, no CLI behavior change, no ResultDataset
  file write, no artifact copy, no solver execution, no SolverAdapter or
  runner integration, no subprocess use, no ProjectSchema mutation, no VLM API,
  no dependency install, no release/tag or asset mutation, no issue mutation,
  no live issue `#8` validation, and no bundled-solver or certification claim.

## ADR-0074: FEASpec CalculiX Result Write Dialog Is Display-Only

- Status: Accepted for experimental implementation
- Date: 2026-06-20
- Context: ADR-0073 added the UI-agnostic state layer for the ResultDataset
  write GUI while leaving PySide6 source, file-dialog behavior, and GUI writer
  invocation out of scope. The next bounded slice is to render that state in a
  GUI dialog without crossing the persistence boundary.
- Decision: Add `FEASpecCalculiXResultWriteDialog` as a display-only PySide6
  dialog over `FEASpecCalculiXResultWriteViewModel`. The dialog renders source,
  artifact, diagnostics, draft mapping, write plan, schema/manifest, safety,
  action, acknowledgement, and result-summary panels while keeping write and
  output-directory actions disabled.
- Consequences: The dialog adds no QFileDialog, no writer invocation, no CLI
  behavior change, no ResultDataset file write, no artifact copy, no solver
  execution, no SolverAdapter or runner integration, no subprocess use, no
  ProjectSchema mutation, no VLM API, no dependency install, no release/tag or
  asset mutation, no issue mutation, no live issue `#8` validation, and no
  bundled-solver or certification claim.

## ADR-0075: FEASpec CalculiX Result Write File Dialog Needs A Planning Gate

- Status: Accepted for experimental design
- Date: 2026-06-20
- Context: ADR-0074 added a display-only ResultDataset write dialog while
  intentionally leaving output-directory selection, QFileDialog behavior, and
  GUI writer invocation disabled. The next bounded step is to document the
  future chooser contract before any GUI source or persistence behavior is
  changed.
- Decision: Add a design/planning-only file-dialog contract for future FEASpec
  CalculiX ResultDataset write GUI work. The contract defines directory-only
  selection, default-directory policy, cancel no-op behavior, path validation,
  create-directory acknowledgement, overwrite acknowledgement, CLI/GUI
  consistency, and future mocked implementation tests.
- Consequences: This gate adds no QFileDialog implementation, no GUI source
  changes, no view-model source changes, no CLI behavior change, no library
  writer behavior change, no writer invocation, no ResultDataset file write,
  no directory creation during selection, no artifact copy, no solver
  execution, no SolverAdapter or runner integration, no subprocess use, no
  ProjectSchema mutation, no VLM API, no dependency install, no release/tag or
  asset mutation, no issue mutation, no live issue `#8` validation, and no
  bundled-solver or certification claim.

## ADR-0076: FEASpec CalculiX Result Write File Dialog Selects Directories Only

- Status: Accepted for experimental implementation
- Date: 2026-06-20
- Context: ADR-0075 defined the output-directory chooser contract for the
  ResultDataset write dialog. The next bounded slice is to let the dialog
  collect explicit output-directory intent without invoking the writer or
  creating any ResultDataset files.
- Decision: Enable the `CHOOSE_OUTPUT_DIRECTORY` action in
  `FEASpecCalculiXResultWriteDialog` and use directory-only
  `QFileDialog.getExistingDirectory` behavior. The dialog accepts an injectable
  chooser for tests, treats cancel as no-op, updates only dialog-local selected
  directory display, and refreshes visible save-plan analysis through the
  existing view-model helper.
- Consequences: This gate adds no writer invocation, no ResultDataset file
  write, no directory creation during selection, no artifact copying, no CLI
  behavior change, no library writer behavior change, no solver execution, no
  SolverAdapter or runner integration, no subprocess use, no ProjectSchema
  mutation, no VLM API, no dependency install, no release/tag or asset
  mutation, no issue mutation, no live issue `#8` validation, and no
  bundled-solver or certification claim.

## ADR-0077: FEASpec CalculiX Result Write GUI Writer Calls Need A Design Gate

- Status: Accepted for experimental design
- Date: 2026-06-20
- Context: ADR-0076 allowed the write dialog to collect an explicit output
  directory while intentionally keeping GUI writer invocation and GUI file
  writes out of scope. The next bounded step is to document the future
  confirmation, acknowledgement, writer-call, failure, retry, and post-write
  display contract before any GUI or view-model source changes.
- Decision: Add a design-only GUI writer-integration contract for FEASpec
  CalculiX ResultDataset writes. The contract requires explicit output
  directory selection, ready write-plan and schema evidence, limitations and
  review acknowledgements, overwrite/create-dir acknowledgements when needed,
  final confirmation, a single future library-writer call boundary, visible
  failure handling, post-write summary, retry rules, state refresh rules, and
  mocked tests.
- Consequences: This gate adds no GUI source mutation, no view-model source
  mutation, no writer invocation, no GUI file writes, no CLI behavior change,
  no library writer behavior change, no artifact copying, no solver execution,
  no SolverAdapter or runner integration, no subprocess use, no ProjectSchema
  mutation, no VLM API, no dependency install, no release/tag or asset
  mutation, no issue mutation, no live issue `#8` validation, and no
  bundled-solver or certification claim.

## ADR-0078: FEASpec CalculiX Result Write GUI Uses The Library Writer Only

- Status: Accepted for experimental implementation
- Date: 2026-06-20
- Context: ADR-0077 defined the GUI writer-integration contract. The bounded
  implementation slice is to let the write dialog persist reviewed
  ResultDataset files without changing CLI behavior, library writer behavior,
  parser behavior, solver execution policy, or issue state.
- Decision: Enable the `WRITE_RESULT_DATASET` action only when reviewed
  write-plan, schema, selected output directory, and acknowledgement gates are
  satisfied. Before writing, require explicit confirmation. On acceptance, call
  the existing library writer once and display writer status, diagnostics, and
  written-file metadata. Keep the writer injectable and confirmation injectable
  for tests.
- Consequences: This gate adds guarded GUI ResultDataset persistence through
  the existing library writer. It adds no CLI behavior change, no library
  writer behavior change, no artifact copying, no open-output-folder command,
  no solver execution, no SolverAdapter or runner integration, no subprocess
  use, no ProjectSchema mutation, no VLM API, no dependency install, no
  release/tag or asset mutation, no issue mutation, no live issue `#8`
  validation, and no bundled-solver or certification claim.

## ADR-0079: FEASpec CalculiX Result Write GUI Post-Write Display Is Polish Only

- Status: Accepted for experimental implementation
- Date: 2026-06-20
- Context: ADR-0078 added the guarded GUI call into the existing library writer.
  The next bounded step is to make successful and failed writer results easier
  to inspect without changing writer semantics or adding a new persistence path.
- Decision: Add dialog-layer post-write display/accessor helpers for status,
  written-file table rows, payload kind, size, SHA-256 hash, grouped
  diagnostics, grouped limitations, failure details, retry guidance, and
  deterministic copy-ready plain text.
- Consequences: This gate adds no OS clipboard integration, no open-output
  shell command, no artifact copying, no new writer invocation path, no CLI
  behavior change, no library writer behavior change, no solver execution, no
  SolverAdapter or runner integration, no subprocess use, no ProjectSchema
  mutation, no VLM API, no dependency install, no release/tag or asset
  mutation, no issue mutation, no live issue `#8` validation, and no
  bundled-solver or certification claim.

## ADR-0080: FEASpec CalculiX Result Write GUI Scope Is Closed Narrowly

- Status: Accepted for experimental closure
- Date: 2026-06-20
- Context: ADR-0078 added the guarded GUI call into the existing library writer,
  and ADR-0079 polished post-write display. The remaining step is to record
  whether this GUI write slice is complete or needs more runtime work.
- Decision: Close the experimental FEASpec CalculiX ResultDataset write GUI
  scope for review-file persistence. The closed workflow covers inspection,
  explicit output-directory selection, limitations and review acknowledgements,
  final confirmation, a single existing library-writer call boundary, standard
  ResultDataset review-file persistence, post-write status, hashes,
  diagnostics, limitations, and retry guidance.
- Consequences: This closure adds docs/tests only and no runtime behavior
  change, no source writer change, no parser change, no solver execution, no
  SolverAdapter or runner integration, no subprocess use, no ProjectSchema
  mutation, no VLM API, no dependency install, no release/tag or asset
  mutation, no issue mutation, no live issue `#8` validation, and no
  bundled-solver or certification claim.

## ADR-0081: Post-Experimental ResultDataset Scope Keeps Validation Open

- Status: Accepted for planning review
- Date: 2026-06-20
- Context: The FEASpec/CalculiX ResultDataset parser/import/write/GUI line is
  complete for experimental review-file persistence, and OSW-VALID-004 reran
  the installed-only live CalculiX validation gate. The local environment did
  not have `ccx`, so the validation result is `skipped-missing`.
- Decision: Record a docs/tests-only post-experimental scope review that
  separates completed ResultDataset work from open live optional validation and
  from future release-boundary decisions.
- Consequences: Develop is intentionally newer than the public `v0.1.4-rc1`
  tag while package metadata still reports `0.1.4rc1`. Issues `#6` through
  `#11`, including issue `#8`, remain open. New version metadata, release tags,
  release edits, asset builds/uploads, issue closure, solver execution, solver
  installation, ProjectSchema mutation, and VLM APIs remain out of scope until
  separate explicit gates.

## ADR-0082: Post-Experimental Boundary Selects v0.1.5-rc1

- Status: Accepted for release-boundary planning
- Date: 2026-06-20
- Context: After `v0.1.4-rc1`, `develop` gained a substantial
  FEASpec/CalculiX experimental line covering FEASpec models/validation/bridge,
  no-run CalculiX export, installed-only run-gate implementation, result
  import, scanner/parser layers, ResultDataset write planning/schema/writer,
  write CLI, and write GUI closure. OSW-VALID-004 remains `skipped-missing`
  because `ccx` was not installed.
- Decision: Select `v0.1.5-rc1` as the next prerelease boundary. This is a
  decision-only boundary selection; metadata alignment, final revalidation,
  tag creation, tag push, asset build/upload, release draft/publish, and any
  issue closure remain separate gates.
- Consequences: Package and CLI metadata still report `0.1.4rc1` until a
  future metadata-alignment gate. The selected target tag, GitHub Release, and
  assets do not exist as a result of this decision. Issues `#6` through `#11`
  remain open, and no live CalculiX validation pass or certification claim is
  made.

## ADR-0083: Align Metadata To v0.1.5rc1 Before Tagging

- Status: Accepted for release-candidate preparation
- Date: 2026-06-20
- Context: ADR-0082 selected `v0.1.5-rc1` as the next prerelease boundary
  after substantial post-`v0.1.4-rc1` FEASpec/CalculiX ResultDataset work.
- Decision: Align package, import, CLI, installed editable metadata, release
  metadata QA, and candidate docs/tests to version `0.1.5rc1`.
- Consequences: `develop` is prepared as a `v0.1.5-rc1` candidate branch, but
  the `v0.1.5-rc1` tag, GitHub Release, release assets, asset upload, issue
  closure, and live optional validation completion remain separate later gates.

## ADR-0084: Post-v0.1.5-rc1 Next Scope Is Release Body Note Cleanup

- Status: Accepted for post-public planning
- Date: 2026-06-23
- Context: `v0.1.5-rc1` is now a public prerelease with five expected assets,
  and the post-public download audit passed. Issues `#6` through `#11` remain
  open for prepared-machine live optional validation, with issue `#8`
  `skipped-missing` because `ccx` was absent. The release body may still contain
  stale wording that says the post-public audit is pending.
- Decision: Select a narrow release-body note update as the next work path,
  limited to replacing stale "post-public audit pending" wording. This
  planning gate does not edit the release, mutate issues, run solvers, bump
  versions, or change runtime source.
- Consequences: Prepared-machine validation and future experimental work remain
  important follow-ups, but public-facing release text should be corrected
  first through a separate release-body update gate. No issue closure or live
  validation pass is claimed.

## ADR-0085: Post-v0.1.5-rc1 Worktrack Selects Maintenance Hardening

- Status: Accepted for post-release planning
- Date: 2026-06-23
- Context: OSW-RELEASE-041 corrected the stale post-public-audit wording in the
  public `v0.1.5-rc1` release body. The release remains a public prerelease
  with five expected assets, while issues `#6` through `#11` remain open and
  issue `#8` remains `skipped-missing` because `ccx` was absent.
- Decision: Select maintenance hardening for GUI aggregate timeout behavior and
  release-monitoring notes as the next worktrack. Prepared-machine live
  optional validation remains deferred until a prepared environment is
  available.
- Consequences: No release edit, asset mutation, issue mutation, solver
  execution, source mutation, version bump, or dependency installation occurs
  in this planning gate. The next recommended gate is
  `OSW-MAINT-018_GUI_AGGREGATE_TIMEOUT_AND_RELEASE_MONITORING_HARDENING`.

## ADR-0086: GUI Aggregate Timeout Uses Complete Per-File Fallback

- Status: Accepted for maintenance QA
- Date: 2026-06-23
- Context: The aggregate GUI pytest command can time out in the local release
  environment after `v0.1.5-rc1`, while deterministic per-file GUI execution has
  passed in prior gates. The project needs a repeatable way to classify this
  condition without hiding actual GUI test failures.
- Decision: Treat aggregate GUI pass as sufficient and aggregate GUI failure as
  blocking. Treat aggregate GUI timeout as warning-only only when a complete
  deterministic per-file fallback covers every `tests/gui/test_*.py` file and
  every file passes or has expected skips. The fallback helper may invoke pytest
  subprocesses only for test orchestration and must not run solvers or mutate
  release, issue, source, tag, or asset state.
- Consequences: Release and maintenance gates can record aggregate timeout
  warnings without weakening GUI test coverage. Missing fallback coverage,
  failed per-file tests, or collection errors remain blocking.

## ADR-0087: Prepared-Machine Optional Validation Remains Installed-Only

- Status: Accepted for validation evidence
- Date: 2026-06-23
- Context: `v0.1.5-rc1` is public, and issues `#6` through `#11` remain open
  for live optional validation. OSW-VALID-005 reran discovery on the current
  machine after the release flow and found no target optional solver or science
  stack installed.
- Decision: Record each target as `skipped-missing` when its required installed
  executable or Python package is absent. Do not install dependencies or
  solvers. Do not treat skipped discovery as a pass. Do not close issues in the
  validation matrix gate; closure requires a later issue-specific review gate.
- Consequences: The current machine contributes updated skipped-missing
  evidence for `v0.1.5-rc1`, while prepared-machine validation remains open.
  Release, asset, tag, issue, runtime source, dependency, and solver state stay
  unchanged by this decision.

## ADR-0088: Next Experimental Line Selects Optional Solver Manifest UX

- Status: Accepted for experimental planning
- Date: 2026-06-23
- Context: `v0.1.5-rc1` is public, the fresh post-public audit passed, release
  body audit-pending wording was corrected, maintenance hardening completed,
  and OSW-VALID-005 classified issues `#6` through `#11` as
  `skipped-missing` because the target optional solver and science stacks were
  absent on this machine.
- Decision: Select `Plugin ecosystem / optional solver manifest UX` as the next
  experimental line. The follow-up should design optional solver/plugin
  manifest fields, health statuses, missing-dependency explanations, and user
  guidance without installing dependencies, bundling solvers, executing
  solvers, or claiming validation success.
- Consequences: Prepared-machine validation remains open and environment
  dependent. Issues `#6` through `#11` remain open. Release, asset, tag, issue,
  runtime source, dependency, solver, version, and certification state stay
  unchanged by this planning decision.

## ADR-0089: Optional Solver Manifest UX Starts Design-Only

- Status: Accepted for experimental design
- Date: 2026-06-23
- Context: OSW-EXP-054 selected Plugin ecosystem / optional solver manifest UX
  after OSW-VALID-005 classified all live optional validation targets as
  `skipped-missing`. Users need clearer optional stack guidance before future
  validation or plugin-health surfaces are implemented.
- Decision: Define a design-only manifest UX contract covering target stacks,
  manifest fields, health states, future CLI and GUI surfaces, plugin-provided
  manifest trust boundaries, validation relationships, and safety/privacy
  limits. Keep implementation of manifest schemas, discovery services, CLI
  commands, and GUI panels in later gates.
- Consequences: Issues `#6` through `#11` remain open. Skipped-missing
  evidence remains neither pass nor failure. No release, asset, tag, issue,
  runtime source, dependency, solver, version, ProjectSchema, VLM, bundled
  solver, or certification state changes in this design gate.

## ADR-0090: Optional Solver Manifest Schema Is Declarative Only

- Status: Accepted for experimental schema/model implementation
- Date: 2026-06-23
- Context: OSW-EXP-055 defined optional solver manifest UX as design-only.
  The next narrow slice needs typed records and built-in manifest data without
  crossing into discovery, CLI, GUI, or solver-health behavior.
- Decision: Add an experimental `osw.experimental.optional_solvers` package
  with typed manifest models, health/support enums, JSON helpers, structural
  diagnostics, and built-in declarative manifests for issues `#6` through
  `#11`. Keep probes as command-token declarations only.
- Consequences: Future discovery, CLI doctor preview, and GUI health surfaces
  remain separate gates. Issues `#6` through `#11` remain open, and no release,
  asset, tag, issue, dependency, solver, ProjectSchema, VLM, bundled solver,
  certification, or version state changes occur in this schema/model gate.

## ADR-0091: Optional Solver Discovery Service Starts As Design

- Status: Accepted for experimental design
- Date: 2026-06-23
- Context: OSW-EXP-056 added declarative optional solver manifest models and
  built-in stack records, but discovery, CLI, GUI, and health-check behavior
  remain out of scope. The next slice needs a service contract before source
  implementation so passive discovery, active validation, privacy, and plugin
  trust boundaries are explicit.
- Decision: Define the optional solver discovery service as design-only first.
  The design consumes `OptionalSolverManifest` records, separates passive
  metadata and future presence checks from active validation gates, defines
  result and diagnostic concepts, maps health states, redacts local environment
  details, and hands off to future CLI/GUI surfaces without implementing
  discovery source.
- Consequences: Future discovery implementation, CLI doctor preview, and GUI
  health panel work remain separate gates. Issues `#6` through `#11` remain
  open, skipped-missing evidence remains neither pass nor failure, and no
  release, asset, tag, issue, dependency, solver, ProjectSchema, VLM, bundled
  solver, certification, or version state changes occur in this design gate.

## ADR-0092: Optional Solver Discovery Service Is Passive Only

- Status: Accepted for experimental implementation
- Date: 2026-06-23
- Context: OSW-EXP-057 defined the discovery service contract after the
  manifest schema/model layer. The next slice needs source-level passive
  presence evidence without crossing into CLI, GUI, plugin loading, active
  health checks, solver execution, or dependency installation.
- Decision: Implement passive discovery under
  `src/osw/experimental/optional_solvers/` with discovery result models,
  injected resolvers, default passive resolvers, redacted report serialization,
  health-state mapping, diagnostics, built-in manifest discovery, and
  explanation helpers. Default executable lookup may use `shutil.which`;
  Python package lookup may use import metadata and `find_spec`; no optional
  solver package is imported.
- Consequences: Discovery can inform future validation and UX surfaces, but it
  is not validation-pass evidence and cannot close issues `#6` through `#11`.
  CLI doctor preview, GUI health panel work, plugin loading, active smoke
  validation, solver execution, dependency installation, release edits, issue
  mutation, bundled-solver claims, certification claims, and version changes
  remain out of scope.

## ADR-0093: Optional Solver CLI Doctor Preview Uses Passive Discovery Only

- Status: Accepted for experimental CLI implementation
- Date: 2026-06-24
- Context: OSW-EXP-058 added passive manifest-consuming discovery, but users
  still needed a command-line way to list built-in stacks, explain one stack,
  and inspect passive setup evidence without running solvers or installing
  dependencies.
- Decision: Add `optional-solver-list`, `optional-solver-doctor`, and
  `optional-solver-explain` as CLI preview commands over the built-in manifests
  and passive discovery reports. Support text and JSON output, redact paths by
  default, keep environment values out of output, allow full executable paths
  only by explicit `--show-full-paths`, and do not add install, run-smoke, or
  execute options.
- Consequences: The CLI can explain missing, partial, discovered, or unknown
  optional stack state, but it is not validation-pass evidence and cannot close
  issues `#6` through `#11`. GUI health panels, plugin loading, active smoke
  validation, solver execution, dependency installation, release edits, issue
  mutation, bundled-solver claims, certification claims, and version changes
  remain out of scope.

## ADR-0094: Optional Solver GUI Health Panel Starts Design-Only

- Status: Accepted for experimental GUI design
- Date: 2026-06-24
- Context: OSW-EXP-059 added passive optional solver CLI preview commands over
  the manifest and discovery layers. The next slice needs a GUI-facing health
  panel contract before any PySide/view-model source work so passive discovery
  semantics, redaction, validation history, user actions, plugin trust labels,
  and issue boundaries are explicit.
- Decision: Define the optional solver GUI health panel as design-only. The
  design covers future entry points, summary layout, stack cards, details,
  diagnostics, guidance, validation history, redaction/privacy behavior, user
  actions, accessibility, plugin trust labels, and a pure view-model boundary
  over passive discovery report objects.
- Consequences: Future view-model and GUI implementation remain separate
  gates. Issues `#6` through `#11` remain open, skipped-missing evidence remains
  neither pass nor failure, and no GUI source, view-model source, CLI behavior
  change, plugin loading, active smoke validation, solver execution, dependency
  installation, release edit, issue mutation, bundled-solver claim,
  certification claim, or version change occurs in this design gate.

## ADR-0095: Optional Solver GUI Health Panel View-Model Is Pure

- Status: Accepted for experimental view-model implementation
- Date: 2026-06-24
- Context: OSW-EXP-060 defined the future optional solver GUI health panel and
  separated widgets from passive discovery and validation behavior. The next
  narrow slice needs deterministic GUI-ready data records without importing
  PySide/Qt or performing discovery from GUI code.
- Decision: Implement a pure UI-agnostic view-model under
  `src/osw/experimental/optional_solvers/` that consumes supplied manifests and
  passive discovery reports and returns summary, stack card, details,
  diagnostics, guidance, validation-history, and action-state records. Action
  states are display data only; install, validation-run, issue-closure,
  clipboard, and docs-opening behavior stay in later explicit gates.
- Consequences: Future GUI widgets remain separate. Issues `#6` through `#11`
  remain open, skipped-missing evidence remains neither pass nor failure, and
  no PySide/Qt import, GUI widget, CLI behavior change, discovery execution,
  active smoke validation, solver execution, dependency installation, release
  edit, issue mutation, bundled-solver claim, certification claim, or version
  change occurs in this view-model gate.

## ADR-0096: Optional Solver GUI Health Panel Is Display-Only

- Status: Accepted for experimental GUI implementation
- Date: 2026-06-25
- Context: OSW-EXP-061S produced a pure optional solver health panel
  view-model. The next slice needs a PySide surface that renders the supplied
  view-model while preserving the no-discovery and no-solver-execution
  boundary.
- Decision: Implement `OptionalSolverHealthPanel` as a PySide dialog under
  `src/osw/gui/dialogs/` that accepts an already-built
  `OptionalSolverHealthPanelViewModel` and renders summary, stack cards,
  details, diagnostics, guidance, validation history, safety, and action-state
  sections. All future or unsafe actions remain disabled/display-only in this
  gate.
- Consequences: Future GUI entry points can embed or open the panel without
  duplicating rendering logic, but discovery refresh, validation execution,
  installation, clipboard export, browser opening, and issue closure remain
  separate explicit gates. No CLI behavior change, plugin loading, discovery
  execution, active smoke validation, solver execution, dependency
  installation, release edit, issue mutation, bundled-solver claim,
  certification claim, or version change occurs in this GUI gate.

## ADR-0097: Optional Solver GUI Summary Export Starts Design-Only

- Status: Accepted for experimental GUI export design
- Date: 2026-06-25
- Context: OSW-EXP-062 added a display-only optional solver GUI health panel
  with disabled future copy/open-docs placeholders. The next slice needs a
  privacy-preserving export contract before any payload builder, file dialog,
  clipboard, or write behavior exists.
- Decision: Define the optional solver GUI summary export workflow as
  design-only. The design covers redacted payload scope, supported future
  JSON/Markdown/plain-text formats, explicit save-path and overwrite policy,
  privacy opt-in for full paths, action states, a pure view-model-derived
  payload boundary, failure handling, and future implementation tests.
- Consequences: Future export view-model and implementation gates remain
  separate. Issues `#6` through `#11` remain open, skipped-missing evidence
  remains neither pass nor failure, and no runtime source, GUI source, CLI
  behavior change, export implementation, file dialog, clipboard integration,
  shell/browser action, discovery execution, solver execution, dependency
  installation, release edit, issue mutation, bundled-solver claim,
  certification claim, or version change occurs in this design gate.

## ADR-0098: Optional Solver GUI Summary Export Uses A Pure Payload Boundary

- Status: Accepted for experimental export view-model implementation
- Date: 2026-06-25
- Context: OSW-EXP-063 defined the future export summary workflow but kept all
  runtime export behavior out of scope. The next slice needs deterministic
  payload and renderer behavior that can be tested without GUI dialogs,
  clipboard access, shell/browser actions, discovery, solvers, or file writes.
- Decision: Implement the export summary as a pure
  `OptionalSolverHealthPanelViewModel` consumer under
  `src/osw/experimental/optional_solvers/`. It builds redacted payload records,
  renders JSON, Markdown, and plain text in memory, and analyzes future save
  paths while reporting diagnostics and privacy warnings.
- Consequences: GUI export wiring and actual writing remain separate future
  gates. Issues `#6` through `#11` remain open, skipped-missing evidence remains
  neither pass nor failure, and no GUI source, CLI behavior change, file
  dialog, file write, clipboard integration, shell/browser action, discovery
  execution, solver execution, dependency installation, release edit, issue
  mutation, bundled-solver claim, certification claim, or version change occurs
  in this payload/view-model gate.

## ADR-0099: Optional Solver GUI Summary Export Writes One Redacted File

- Status: Accepted for experimental GUI export implementation
- Date: 2026-06-25
- Context: OSW-EXP-064 produced a pure export payload, renderer, and save-plan
  layer for optional solver health summaries. The next slice needs user-visible
  GUI wiring while preserving redaction and avoiding clipboard, shell/browser,
  discovery, validation, install, issue, and release side effects.
- Decision: Add an `OptionalSolverHealthPanel` export action that renders a
  redacted summary through the pure export layer and writes exactly one
  explicitly selected `.json`, `.md`, or `.txt` file after save-plan checks and
  overwrite confirmation. Parent directories must already exist, unsupported
  extensions are rejected, and cancel writes nothing.
- Consequences: Users can save a portable setup summary for support or
  prepared-machine planning, but the summary is not validation evidence and
  cannot close issues `#6` through `#11`. Clipboard integration, open-output
  folder actions, shell/browser opening, discovery refresh, solver execution,
  dependency installation, release edits, issue mutation, bundled-solver
  claims, certification claims, and version changes remain out of scope.

## ADR-0100: Optional Solver GUI Discovery Refresh Starts Design-Only

- Status: Accepted for experimental GUI refresh design
- Date: 2026-06-25
- Context: OSW-EXP-065 added a redacted single-file export action to the
  optional solver health panel, while refresh passive discovery remained a
  disabled/display-only action. The next slice needs the refresh contract
  before any GUI source, worker source, or view-model source is changed.
- Decision: Define the future GUI discovery refresh workflow as design-only.
  The design requires explicit user action, passive discovery only, a future
  injected runner rather than widget-owned discovery calls, worker request ids,
  stale-result rejection, atomic view-model replacement, selected-stack and
  filter preservation where safe, redaction, export interaction rules, and
  validation-gate separation.
- Consequences: Future refresh view-model and GUI implementation gates remain
  separate. Issues `#6` through `#11` remain open, skipped-missing evidence
  remains neither pass nor failure, and no runtime source, GUI source,
  view-model source, CLI behavior change, background worker implementation,
  discovery refresh source, active validation, solver execution, dependency
  installation, release edit, issue mutation, bundled-solver claim,
  certification claim, or version change occurs in this design gate.

## ADR-0101: Optional Solver GUI Discovery Refresh State Is Pure

- Status: Accepted for experimental refresh view-model implementation
- Date: 2026-06-25
- Context: OSW-EXP-066 defined the future explicit passive refresh workflow,
  but kept GUI wiring, workers, threading, and discovery execution out of
  scope. The next slice needs deterministic state and apply behavior that can
  be tested without Qt, workers, discovery calls, solver commands, or file
  system side effects.
- Decision: Implement a pure refresh view-model under
  `src/osw/experimental/optional_solvers/` that records refresh states,
  request/result metadata, action states, stale-result handling,
  success/failure/cancel apply helpers, atomic health panel view-model
  replacement from supplied reports, selected-stack/filter preservation, and
  status/error text.
- Consequences: Future GUI refresh wiring and worker orchestration remain
  separate gates. Issues `#6` through `#11` remain open, skipped-missing
  evidence remains neither pass nor failure, and no GUI source, CLI behavior
  change, discovery execution, background worker, threading implementation,
  active validation, solver execution, dependency installation, release edit,
  issue mutation, bundled-solver claim, certification claim, or version change
  occurs in this view-model gate.

## ADR-0102: Optional Solver GUI Discovery Refresh Is Explicit And Passive

- Status: Accepted for experimental GUI refresh implementation
- Date: 2026-06-25
- Context: OSW-EXP-067 added a pure refresh state/apply layer. The health
  panel still needed a user-visible way to request passive discovery without
  adding startup scans, active validation, workers, solver execution, installs,
  issue mutation, or release mutation.
- Decision: Wire `Refresh Passive Discovery` in the PySide health panel as an
  explicit user action. The panel supports injected runners for deterministic
  tests and a default built-in passive discovery runner. Successful results
  replace the accepted health panel view-model through the pure apply helper;
  failed, canceled, and stale results preserve the prior view-model. Export
  summary continues to render the currently accepted view-model.
- Consequences: Refresh output is setup/health UX evidence only and is not
  validation evidence. Issues `#6` through `#11` remain open, skipped-missing
  evidence remains neither pass nor failure, and no automatic startup refresh,
  background worker, threading implementation, active smoke validation, solver
  execution, dependency installation, issue mutation, release edit,
  bundled-solver claim, certification claim, or version change occurs in this
  implementation gate.

## ADR-0103: Optional Solver Plugin Manifests Require Source And Trust Labels

- Status: Accepted for experimental plugin manifest loading design
- Date: 2026-06-25
- Context: OSW-EXP-068 completed explicit passive refresh for built-in
  manifests. The plugin ecosystem line now needs a design boundary for future
  plugin-contributed optional solver manifest metadata before any loader,
  scanner, CLI, or GUI source is changed.
- Decision: Define future optional solver manifest source categories and trust
  labels for built-in core, project-local, user-local, plugin-package, and
  organization-managed manifests. Built-ins win by default, plugin overrides
  are forbidden by default, plugin-provided manifests are third-party metadata,
  invalid records are quarantined as diagnostics, and CLI/GUI surfaces must
  display source and trust labels.
- Consequences: Future plugin manifest work remains data-only until a separate
  loader model gate. Issues `#6` through `#11` remain open, skipped-missing
  evidence remains neither pass nor failure, and no plugin loading
  implementation, filesystem plugin scan, network marketplace, plugin code
  execution, solver execution, dependency installation, release edit, issue
  mutation, bundled-solver claim, certification claim, or version change occurs
  in this design gate.

## ADR-0104: Optional Solver Plugin Manifest Loader Is Data-Only

- Status: Accepted for experimental plugin manifest loader model
- Date: 2026-06-25
- Context: OSW-EXP-069 defined source/trust labels and conflict policy for
  future plugin-provided optional solver manifests. The next slice needs a
  reusable model that can validate explicit manifest data without discovering
  plugins, importing packages, scanning directories, fetching network data, or
  changing CLI/GUI behavior.
- Decision: Implement a data-only loader under
  `src/osw/experimental/optional_solvers/` that accepts explicit dictionaries
  and explicit JSON files, reuses declarative optional solver manifest parsing
  and validation, records source/trust metadata, reports accepted and rejected
  manifests separately, detects duplicate stack ids, and blocks unsafe wording
  such as installer commands, executable code references, bundled-solver
  claims, and certification claims.
- Consequences: Future CLI preview and GUI display remain separate gates.
  Issues `#6` through `#11` remain open, skipped-missing evidence remains
  neither pass nor failure, and no CLI source, GUI source, plugin package
  import, directory scan, network fetch, discovery execution, solver execution,
  dependency installation, release edit, issue mutation, bundled-solver claim,
  certification claim, or version change occurs in this loader-model gate.

## ADR-0105: Optional Solver Plugin Manifest CLI Preview Uses Explicit Files Only

- Status: Accepted for experimental plugin manifest CLI preview
- Date: 2026-06-25
- Context: OSW-EXP-070 added a data-only plugin manifest loader model. The next
  slice needs a user-facing preview command that can inspect explicit JSON
  files without turning plugin manifests into package discovery, directory
  scanning, network fetching, solver checks, or validation evidence.
- Decision: Add `optional-solver-plugin-manifest-preview` with repeatable
  `--manifest`, text/JSON output, optional built-in conflict context, strict
  mode, and diagnostics/policy display. The command delegates to the loader
  model and reports accepted manifests, rejected manifests, conflicts, source
  types, trust labels, and diagnostics.
- Consequences: Future GUI display and explicit import flows remain separate
  gates. Issues `#6` through `#11` remain open, skipped-missing evidence remains
  neither pass nor failure, and no GUI source, plugin package import, directory
  scan, network fetch, discovery execution, solver execution, dependency
  installation, release edit, issue mutation, bundled-solver claim,
  certification claim, or version change occurs in this CLI preview gate.

## ADR-0106: Optional Solver Plugin Manifest GUI Starts As Review Design

- Status: Accepted for experimental plugin manifest GUI design
- Date: 2026-06-25
- Context: OSW-EXP-071 exposed explicit JSON plugin manifest loader reports in
  the CLI. A future GUI needs a review contract before any view-model, file
  dialog, activation, plugin package loading, directory scanning, network
  fetching, or discovery integration is implemented.
- Decision: Define a design-only future GUI workflow with health-panel,
  preview-dialog, and project-settings entry points; explicit-file preview
  flow; accepted/rejected/conflict panels; source/trust labels; diagnostics;
  safety/privacy messaging; health/export/refresh relationships; failure
  handling; and a future pure view-model boundary.
- Consequences: Future view-model and GUI implementation remain separate gates.
  Issues `#6` through `#11` remain open, skipped-missing evidence remains
  neither pass nor failure, and no runtime source, GUI source, CLI source,
  file-dialog source, plugin activation, plugin package import, directory scan,
  network fetch, discovery execution, solver execution, dependency
  installation, release edit, issue mutation, bundled-solver claim,
  certification claim, or version change occurs in this design gate.

## ADR-0107: Optional Solver Plugin Manifest GUI View-Model Is Pure

- Status: Accepted for experimental plugin manifest GUI view-model
- Date: 2026-06-25
- Context: OSW-EXP-072 defined a future GUI review surface for plugin manifest
  loader reports. The next implementation slice needs reusable GUI-ready data
  without adding PySide widgets, file dialogs, file loading, plugin package
  imports, directory scans, network fetches, discovery, solver execution, or
  validation evidence.
- Decision: Implement a pure view-model under
  `src/osw/experimental/optional_solvers/` that consumes
  `OptionalSolverPluginManifestLoadReport` and returns deterministic summary,
  accepted/rejected rows, conflict rows, diagnostic rows, trust badges,
  guidance, filters, and action-state placeholders. Activation, discovery with
  plugin manifests, validation, solver install, and issue closure remain
  unavailable.
- Consequences: Future PySide binding and activation remain separate gates.
  Issues `#6` through `#11` remain open, skipped-missing evidence remains
  neither pass nor failure, and no GUI source, CLI source, file dialog, plugin
  activation, plugin package import, directory scan, network fetch, discovery
  execution, solver execution, dependency installation, release edit, issue
  mutation, bundled-solver claim, certification claim, or version change occurs
  in this view-model gate.

## ADR-0108: Optional Solver Plugin Manifest GUI Is Display-Only

- Status: Accepted for experimental plugin manifest GUI implementation
- Date: 2026-06-25
- Context: OSW-EXP-073 added a pure GUI view-model for plugin manifest loader
  reports. Users now need a PySide review surface for those already-built
  records, but file dialogs, explicit import, activation, plugin package
  loading, discovery with plugin manifests, solver execution, and validation
  evidence remain later or out of scope.
- Decision: Implement `OptionalSolverPluginManifestPanel` as a PySide display
  component under `src/osw/gui/dialogs/`. The panel accepts an already-built
  `OptionalSolverPluginManifestGuiViewModel` and renders summary counts,
  accepted/rejected/conflict rows, diagnostics, trust/source labels, safety
  guidance, and disabled/future action states.
- Consequences: The plugin manifest preview can be reviewed in GUI tests and
  future entry points without adding file dialogs, file loading, plugin
  activation, plugin package import, directory scan, network fetch, discovery
  execution, solver execution, dependency installation, release edit, issue
  mutation, bundled-solver claim, certification claim, validation-pass claim,
  issue-closure claim, or version change.

## ADR-0109: Optional Solver Plugin Manifest Explicit Import GUI Starts As Design-Only

- Status: Accepted for experimental GUI design
- Date: 2026-06-25
- Context: OSW-EXP-074 added a display-only PySide panel
  (`OptionalSolverPluginManifestPanel`) over already-built
  `OptionalSolverPluginManifestGuiViewModel` records. The next UX step is to
  design explicit user-selected JSON manifest preview without implementing it,
  while preserving the display-only boundary and keeping preview distinct from
  activation, validation, discovery, installation, issue closure, and
  certification.
- Decision: Define explicit plugin manifest JSON import/preview GUI behavior as
  design-only. Specify future entry points, a user-initiated JSON-only file
  chooser, file safety and failure states, design-only `OSPMG_IMPORT_*`
  diagnostic code reservations, source/trust labels with user-selected files
  untrusted by default, built-ins-win conflict policy, and relationships to the
  CLI preview, health panel, and export summary. Preserve no file dialog
  implementation, no file loading implementation, no JSON parsing from GUI
  source, no plugin activation, no plugin package import, no directory scan, no
  network fetch, no discovery execution, no solver execution, no dependency
  installation, and no issue/release mutation.
- Consequences: Future implementation has a safety contract and test plan.
  Runtime behavior remains unchanged in this gate, and user-selected manifests
  remain untrusted preview data only. Issues `#6` through `#11` remain open,
  skipped-missing evidence remains neither pass nor failure, and no runtime
  source, GUI source, view-model source, CLI source, loader source, file dialog,
  plugin activation, plugin package import, directory scan, network fetch,
  discovery execution, solver execution, dependency installation, release edit,
  issue mutation, bundled-solver claim, certification claim, validation-pass
  claim, issue-closure claim, or version change occurs in this design gate.

## ADR-0110: Optional Solver Plugin Manifest Explicit Import ViewModel Is Pure And Side-Effect-Free

- Status: Accepted for experimental view-model implementation
- Date: 2026-06-26
- Context: OSW-EXP-075 defined explicit plugin manifest JSON import/preview GUI
  behavior as design-only. The next safe slice is a pure view-model that
  consumes already-produced loader/report data without adding file dialogs, file
  loading, JSON parsing from paths, plugin activation, discovery, validation,
  solver execution, or dependency installation.
- Decision: Implement a pure view-model under
  `src/osw/experimental/optional_solvers/plugin_manifest_explicit_import_gui_viewmodel.py`.
  It consumes an `OptionalSolverPluginManifestLoadReport` (or caller-supplied
  import diagnostics / cancel state) and produces summary, selected-source,
  accepted/rejected/conflict, loader-diagnostic, `OSPMG_IMPORT_*` import
  diagnostic, trust-badge, guidance, and action-state records, with redacted
  source references and honesty flags. It reuses the OSW-EXP-074 GUI view-model
  row semantics and performs no file IO, GUI widget behavior, activation,
  discovery, validation, solver execution, dependency installation, issue
  mutation, release mutation, or version change.
- Consequences: A future GUI implementation can bind to a deterministic state
  model. File dialog and file loading remain future-gated (OSW-EXP-077), and
  activation remains a later gate (OSW-EXP-078). User-selected and
  plugin-provided manifests remain untrusted preview data only. Issues `#6`
  through `#11` remain open, skipped-missing evidence remains neither pass nor
  failure, and no GUI source, CLI source, file dialog, file loading, JSON
  parsing from paths, plugin activation, plugin package import, directory scan,
  network fetch, discovery execution, solver execution, dependency installation,
  release edit, issue mutation, bundled-solver claim, certification claim,
  validation-pass claim, issue-closure claim, or version change occurs in this
  view-model gate.

## ADR-0111: Optional Solver Plugin Manifest Explicit Import GUI Is Preview-Only

- Status: Accepted for experimental GUI implementation
- Date: 2026-06-26
- Context: OSW-EXP-075 defined explicit plugin manifest JSON import/preview GUI
  behavior as design-only. OSW-EXP-076 added a pure side-effect-free
  view-model. The next safe slice is a PySide GUI surface for explicit local
  JSON preview.
- Decision: Implement a PySide explicit import preview panel under
  `src/osw/gui/dialogs/`. It supports user-initiated local JSON selection,
  loader/report preview, view-model display, cancellation/no-op, diagnostics,
  trust/source labels, and disabled/future-only unsafe actions. It does not
  activate manifests, import plugin packages, scan directories, fetch network
  manifests, run discovery, run validation, install dependencies, execute
  solvers, mutate issues/releases/tags/assets, or bump versions.
- Consequences: Users can preview explicit local plugin manifest JSON files in
  the GUI. Activation and discovery with plugin manifests remain future-gated.
  User-selected manifests remain untrusted preview data only.

## ADR-0112: Optional Solver Plugin Manifest Activation Starts As Design-Only

- Status: Accepted for experimental activation design
- Date: 2026-06-26
- Context: OSW-EXP-077 added preview-only explicit plugin manifest JSON GUI
  import. Users can preview manifests, but activation semantics remain
  undefined. Activation could be confused with trust, validation, discovery,
  installation, or solver execution without a design gate.
- Decision: Define plugin manifest activation semantics as design-only before
  implementation. Activation remains explicit, user-acknowledged, untrusted by
  default, and separate from validation, discovery execution, dependency
  installation, solver execution, issue closure, release mutation, and
  certification. Specify activation preconditions, acknowledgements, a
  source/trust/provenance model, a built-ins-win conflict policy, an
  unsafe-claim block policy, a future activation state machine, and design-only
  `OSPMG_ACTIVATION_*` diagnostic reservations.
- Consequences: Future view-model and GUI implementation gates have a safety
  contract. No runtime behavior changes in this gate, and user-selected and
  plugin-provided manifests remain preview-only until a future activation
  implementation gate. Issues `#6` through `#11` remain open, skipped-missing
  evidence remains neither pass nor failure, and no runtime source, GUI source,
  view-model source, CLI source, loader source, activation implementation,
  plugin package import, directory scan, network fetch, discovery execution,
  validation execution, solver execution, dependency installation, release edit,
  issue mutation, tag mutation, asset mutation, bundled-solver claim,
  certification claim, validation-pass claim, issue-closure claim, or version
  change occurs in this design gate.

## ADR-0113: Optional Solver Plugin Manifest Activation ViewModel Is Pure And Non-Executing

- Status: Accepted for experimental activation view-model implementation
- Date: 2026-06-26
- Context: OSW-EXP-078 defined activation semantics as design-only. The next safe
  slice is a pure view-model that models activation state, readiness,
  acknowledgements, diagnostics, and action availability without runtime side
  effects.
- Decision: Implement a pure activation view-model under
  `src/osw/experimental/optional_solvers/plugin_manifest_activation_viewmodel.py`.
  It consumes supplied preview/import/loader data or caller-supplied activation
  candidates plus acknowledgement/lifecycle state, and produces deterministic
  summary, candidate, acknowledgement, diagnostic, conflict, trust-badge, and
  action-state records over the OSW-EXP-078 state machine and `OSPMG_ACTIVATION_*`
  vocabulary, with redacted source references and honesty flags. It performs no
  file IO, GUI behavior, activation persistence, plugin import, discovery
  execution, validation, dependency installation, solver execution, issue
  mutation, release mutation, tag mutation, asset mutation, or version change.
- Consequences: Future GUI implementation can bind to a deterministic activation
  state model. Activation remains non-persistent and non-executing in this gate,
  and user-selected/plugin-provided manifests remain untrusted and non-validating
  until later explicit gates. Issues `#6` through `#11` remain open,
  skipped-missing evidence remains neither pass nor failure, and no GUI source,
  CLI source, activation persistence, plugin package import, directory scan,
  network fetch, discovery execution, validation execution, solver execution,
  dependency installation, release edit, issue mutation, tag mutation, asset
  mutation, bundled-solver claim, certification claim, validation-pass claim,
  issue-closure claim, or version change occurs in this view-model gate.

## ADR-0114: Optional Solver Plugin Manifest Activation GUI Is ViewModel-Driven And Non-Persistent

- Status: Accepted for experimental activation GUI implementation
- Date: 2026-06-26
- Context: OSW-EXP-078 defined activation semantics as design-only and
  OSW-EXP-079 added a pure activation view-model. The next safe slice is a
  PySide GUI surface that renders activation readiness and acknowledgements
  without persisting activation or executing discovery/validation/install/solver
  actions.
- Decision: Implement a PySide activation panel under `src/osw/gui/dialogs/`
  (`OptionalSolverPluginManifestActivationPanel`). The panel consumes
  `OptionalSolverPluginManifestActivationViewModel` records and renders summary,
  candidates, acknowledgements, diagnostics, conflicts, trust/provenance badges,
  safety guidance, and disabled/future action states. Acknowledgement
  interaction is widget-local and non-persistent via an injected pure callback
  that rebuilds a supplied view-model. The panel performs no activation
  persistence, plugin package import, directory scan, network fetch, discovery
  execution, validation, dependency installation, solver execution, issue
  mutation, release mutation, tag mutation, asset mutation, or version change.
- Consequences: Users can inspect activation readiness and safety requirements
  in the GUI. Activation persistence and discovery integration remain
  future-gated, and user/plugin manifests remain untrusted and non-validating.
  Issues `#6` through `#11` remain open, skipped-missing evidence remains neither
  pass nor failure, and no activation persistence, CLI activation, plugin
  package import, directory scan, network fetch, discovery execution, validation
  execution, solver execution, dependency installation, release edit, issue
  mutation, tag mutation, asset mutation, bundled-solver claim, certification
  claim, validation-pass claim, issue-closure claim, or version change occurs in
  this GUI gate.

## ADR-0115: Optional Solver Plugin Manifest Deactivation Starts As Design-Only

- Status: Accepted for experimental deactivation design
- Date: 2026-06-26
- Context: OSW-EXP-080 added a view-model-driven activation GUI surface.
  Activation state now has GUI visibility, but deactivation semantics remain
  undefined. Deactivation could be confused with file deletion, uninstall,
  validation failure, issue closure, release mutation, or discovery changes
  without a design gate.
- Decision: Define deactivation semantics as design-only before implementation.
  Deactivation remains explicit, acknowledged, provenance-preserving,
  non-deleting, non-uninstalling, non-executing, non-validating, and separate
  from discovery, issues, releases, tags, assets, and certification. Specify
  deactivation preconditions, acknowledgements, a source/trust/provenance model,
  a deactivation state machine, a conflict/shared-stack policy, a validation/
  evidence-retention policy, and design-only `OSPMG_DEACTIVATION_*` diagnostic
  reservations.
- Consequences: Future discovery integration and any future deactivation
  implementation have a safety contract. No runtime behavior changes in this
  gate, and active/deactivated candidates remain non-validating and untrusted
  unless separate evidence and trust gates exist. Issues `#6` through `#11`
  remain open, skipped-missing evidence remains neither pass nor failure, and no
  runtime source, GUI source, view-model source, CLI source, deactivation
  implementation, deactivation persistence, file deletion, dependency uninstall,
  solver uninstall, plugin package import, directory scan, network fetch,
  discovery execution, validation execution, solver execution, dependency
  installation, release edit, issue mutation, tag mutation, asset mutation,
  bundled-solver claim, certification claim, validation-pass claim,
  issue-closure claim, or version change occurs in this design gate.

## ADR-0116: Optional Solver Plugin Manifest Discovery Refresh Integration Starts As Design-Only

- Status: Accepted for experimental discovery-refresh integration design
- Date: 2026-06-27
- Context: OSW-EXP-080 added activation GUI review state and OSW-EXP-081 defined
  deactivation semantics. Activated/deactivated plugin manifest state could later
  affect optional solver discovery, but doing so without a design gate could be
  confused with validation, installation, solver execution, issue closure, or
  trusted plugin integration.
- Decision: Define discovery-refresh integration semantics as design-only before
  implementation. Discovery refresh integration remains explicit,
  provenance-preserving, non-validating, non-installing, non-executing, and
  separate from issue/release/tag/asset mutation. Built-ins remain authoritative
  by default; activated user/plugin manifest candidates remain untrusted unless
  later gates define trust behavior; deactivated candidates are excluded or shown
  inactive. Specify refresh modes, preconditions, acknowledgements, a
  source/trust/provenance model, a built-in/conflict policy, a deactivated
  candidate policy, an unsafe-claim policy, a refresh state machine, and
  design-only `OSPMG_DISCOVERY_REFRESH_*` diagnostic reservations.
- Consequences: Future view-model and GUI/source implementation gates have a
  safety contract. No runtime discovery behavior changes in this gate, and live
  optional validation issues `#6` through `#11` remain open and separate.
  Skipped-missing evidence remains neither pass nor failure, and no runtime
  source, GUI source, view-model source, CLI source, discovery integration,
  passive discovery behavior change, activation/deactivation persistence, plugin
  package import, directory scan, network fetch, discovery execution, validation
  execution, solver execution, dependency installation, release edit, issue
  mutation, tag mutation, asset mutation, bundled-solver claim, certification
  claim, validation-pass claim, issue-closure claim, or version change occurs in
  this design gate.

## ADR-0117: Optional Solver Plugin Manifest Discovery Refresh ViewModel Is Pure And Non-Executing

- Status: Accepted for experimental discovery-refresh view-model
- Date: 2026-06-27
- Context: OSW-EXP-082 defined the discovery-refresh integration contract as
  design-only. A view-model layer is needed before any GUI/source integration so
  that activated/deactivated candidate state can be translated into deterministic
  refresh readiness, source inclusion/exclusion, acknowledgement, diagnostic,
  conflict, unsafe-claim, trust, and action-state records without being confused
  with discovery execution, validation, installation, solver execution, issue
  closure, or trusted plugin integration.
- Decision: Implement the discovery-refresh view-model as pure and
  side-effect-free. It consumes a supplied activation view-model or
  caller-supplied discovery source records plus acknowledgement and refresh
  lifecycle inputs and produces deterministic records over the OSW-EXP-082
  refresh modes, refresh state machine, readiness rules, required
  acknowledgements, and `OSPMG_DISCOVERY_REFRESH_*` diagnostic vocabulary, with
  redacted source references and honesty flags that remain false. Built-ins stay
  authoritative; user/plugin candidates stay untrusted and are not validation
  evidence; deactivated candidates are excluded or inactive; refresh readiness is
  not discovery execution and not validation.
- Consequences: A future GUI/source discovery-refresh integration gate has a
  pure, testable contract. No runtime discovery integration, passive discovery
  behavior change, activation/deactivation persistence, GUI behavior, CLI
  behavior, PySide/Qt import, plugin package import, directory scan, network
  fetch, discovery execution, validation execution, solver execution, dependency
  installation, release edit, issue mutation, tag mutation, asset mutation,
  bundled-solver claim, certification claim, validation-pass claim, issue-closure
  claim, or version change occurs in this view-model gate, and live optional
  validation issues `#6` through `#11` remain open and separate with
  skipped-missing evidence still neither pass nor failure.

## ADR-0118: Optional Solver Plugin Manifest Discovery Refresh GUI Is ViewModel-Driven And Non-Executing

- Status: Accepted for experimental discovery-refresh GUI implementation
- Date: 2026-06-27
- Context: OSW-EXP-082 defined discovery-refresh integration semantics as
  design-only and OSW-EXP-083 added a pure discovery-refresh view-model. The next
  safe slice is a PySide GUI surface that renders refresh readiness, modes, source
  inclusion/exclusion, acknowledgements, diagnostics, conflicts, unsafe claims,
  and action availability without runtime discovery side effects.
- Decision: Implement a PySide discovery-refresh panel
  (`OptionalSolverPluginManifestDiscoveryRefreshPanel`) under
  `src/osw/gui/dialogs/`. The panel consumes
  `OptionalSolverPluginManifestDiscoveryRefreshViewModel` records and renders
  summary, refresh mode/state, discovery sources, deactivated candidates,
  acknowledgements, diagnostics, conflicts, unsafe claims, trust/provenance
  badges, safety guidance, and disabled/future action states. Acknowledgement
  interaction is widget-local and non-persistent via an injected pure callback;
  unsafe actions (run discovery, run validation, install dependency, execute
  solver, close issue) stay disabled/future-only. The panel performs no runtime
  discovery integration, passive discovery behavior change, activation/deactivation
  persistence, plugin package import, directory scan, network fetch, discovery
  execution, validation, dependency installation, solver execution, issue
  mutation, release mutation, tag mutation, asset mutation, or version change.
- Consequences: Users can inspect future discovery-refresh readiness and safety
  requirements in the GUI. Runtime discovery integration remains future-gated.
  Activated user/plugin manifest candidates remain untrusted and non-validating,
  built-ins remain authoritative, refresh-ready is not validation evidence, and
  live optional validation issues `#6` through `#11` remain open and separate with
  skipped-missing evidence still neither pass nor failure.

## ADR-0119: Optional Solver Plugin Manifest Deactivation ViewModel Is Pure And Non-Mutating

- Status: Accepted for experimental deactivation view-model implementation
- Date: 2026-06-27
- Context: OSW-EXP-081 defined deactivation semantics as design-only, and
  OSW-EXP-079 already included a generic `deactivated` activation state. The next
  safe slice is a pure view-model extension that models deactivation readiness,
  acknowledgements, evidence retention, diagnostics, shared-stack warnings, and
  action availability without runtime side effects.
- Decision: Implement a pure deactivation view-model
  (`OptionalSolverPluginManifestDeactivationViewModel`) under
  `src/osw/experimental/optional_solvers/`. The view-model consumes supplied
  activation/deactivation candidate data and produces deterministic
  deactivation-readiness, acknowledgement, diagnostic, shared-stack,
  evidence-retention, trust, and action-state records over the OSW-EXP-081
  deactivation state machine and `OSPMG_DEACTIVATION_*` vocabulary, with redacted
  source references and honesty flags that remain false. It performs no file IO,
  file deletion, GUI behavior, CLI behavior, activation/deactivation persistence,
  plugin import, directory scan, network fetch, discovery execution, validation,
  dependency install/uninstall, solver uninstall/execution, issue mutation,
  release mutation, tag mutation, asset mutation, or version change.
- Consequences: Future deactivation GUI or source-integration gates can bind to a
  deterministic state model. Deactivation remains non-persistent and non-mutating
  in this gate. User/plugin manifests remain untrusted, non-validating, and
  provenance-preserving; built-ins remain authoritative; historical validation
  evidence is retained; a deactivated candidate is not a validation failure; and
  live optional validation issues `#6` through `#11` remain open and separate with
  skipped-missing evidence still neither pass nor failure.

## ADR-0120: Optional Solver Plugin Manifest Deactivation GUI Is ViewModel-Driven And Non-Mutating

- Status: Accepted for experimental deactivation GUI implementation
- Date: 2026-06-27
- Context: OSW-EXP-081 defined deactivation semantics as design-only and
  OSW-EXP-085 added a pure deactivation view-model extension. The next safe slice
  is a PySide GUI surface that renders deactivation readiness, acknowledgements,
  diagnostics, evidence retention, shared-stack warnings, and action availability
  without runtime mutation.
- Decision: Implement a PySide deactivation panel
  (`OptionalSolverPluginManifestDeactivationPanel`) under `src/osw/gui/dialogs/`.
  The panel consumes `OptionalSolverPluginManifestDeactivationViewModel` records
  and renders summary, candidates, acknowledgements, diagnostics,
  shared-stack/conflict rows, evidence retention, trust/provenance badges, safety
  guidance, and disabled/future action states. Acknowledgement interaction is
  widget-local and non-persistent via an injected pure callback; unsafe actions
  (run discovery, run validation, uninstall dependency/solver, execute solver,
  close issue) stay disabled/future-only. The panel performs no runtime
  deactivation behavior, deactivation persistence, file deletion, dependency
  uninstall, solver uninstall, plugin package import, directory scan, network
  fetch, discovery execution, validation, solver execution, issue mutation,
  release mutation, tag mutation, asset mutation, or version change.
- Consequences: Users can inspect future deactivation readiness and safety
  requirements in the GUI. Deactivation persistence and source mutation remain
  future-gated. User/plugin manifests remain untrusted, non-validating, and
  provenance-preserving; built-ins remain authoritative; historical validation
  evidence is retained; a deactivated state is not a validation failure; and live
  optional validation issues `#6` through `#11` remain open and separate with
  skipped-missing evidence still neither pass nor failure.

## ADR-0121: Optional Solver Plugin Manifest Reactivation Starts As Design-Only

- Status: Accepted for experimental reactivation design
- Date: 2026-06-27
- Context: OSW-EXP-086 added a view-model-driven deactivation GUI surface.
  Deactivated candidate state now has GUI visibility, but reactivation semantics
  remain undefined. Reactivation could be confused with automatic activation,
  trust restoration, validation success, dependency installation, solver
  execution, issue closure, or release mutation without a design gate.
- Decision: Define reactivation semantics as design-only before implementation.
  Reactivation remains explicit, acknowledged, provenance-preserving,
  deactivation-history-retaining, non-validating, non-installing, non-executing,
  non-persistent, and separate from discovery, issues, releases, tags, assets, and
  certification. Specify reactivation preconditions, acknowledgements, a
  source/trust/provenance model, a reactivation state machine, a conflict/
  shared-stack policy, a stale-source/re-preview policy, a validation/evidence
  policy, and design-only `OSPMG_REACTIVATION_*` diagnostic reservations.
  Reactivation routes a deactivated candidate back through future activation
  review; it does not directly activate, trust, validate, install, uninstall,
  execute, or persist anything.
- Consequences: Future reactivation view-model and GUI implementation gates have a
  safety contract. No runtime behavior changes in this gate, and live optional
  validation issues `#6` through `#11` remain open and separate. User/plugin
  manifests remain untrusted and non-validating unless separate evidence and trust
  gates exist; built-ins remain authoritative; deactivation history and historical
  validation evidence are retained; and skipped-missing evidence remains neither
  pass nor failure. No runtime source, GUI source, view-model source, CLI source,
  reactivation implementation, reactivation persistence, automatic activation,
  trust restoration, file restore/rewrite/delete, dependency install/uninstall,
  solver uninstall, plugin package import, directory scan, network fetch, discovery
  execution, validation execution, solver execution, release edit, issue mutation,
  tag mutation, asset mutation, bundled-solver claim, certification claim,
  validation-pass claim, validation-fail claim, issue-closure claim, or version
  change occurs in this design gate.

## ADR-0122: Optional Solver Plugin Manifest Reactivation ViewModel Is Pure And Non-Mutating

- Status: Accepted for experimental reactivation view-model implementation
- Date: 2026-06-27
- Context: OSW-EXP-087 defined reactivation semantics as design-only, and
  OSW-EXP-085 added a pure deactivation view-model extension. The next safe slice
  is a pure view-model extension that models reactivation readiness,
  acknowledgements, stale-source/re-preview state, deactivation-history retention,
  evidence retention, diagnostics, shared-stack warnings, and action availability
  without runtime side effects.
- Decision: Implement a pure reactivation view-model
  (`OptionalSolverPluginManifestReactivationViewModel`) under
  `src/osw/experimental/optional_solvers/`. The view-model consumes supplied
  deactivation/activation/reactivation candidate data and produces deterministic
  reactivation-readiness, acknowledgement, diagnostic, shared-stack,
  stale-source/re-preview, deactivation-history, evidence-retention, trust, and
  action-state records over the OSW-EXP-087 reactivation state machine and
  `OSPMG_REACTIVATION_*` vocabulary, with redacted source references and honesty
  flags that remain false. Reactivation routes a deactivated candidate back toward
  future activation review; it performs no file IO, file restore/rewrite/delete,
  GUI behavior, CLI behavior, automatic activation, trust restoration,
  activation/deactivation/reactivation persistence, plugin import, directory scan,
  network fetch, discovery execution, validation, dependency install/uninstall,
  solver uninstall/execution, issue mutation, release mutation, tag mutation, asset
  mutation, or version change.
- Consequences: Future reactivation GUI or source-integration gates can bind to a
  deterministic state model. Reactivation remains non-persistent and non-mutating
  in this gate. User/plugin manifests remain untrusted, non-validating,
  provenance-preserving, and deactivation-history-retaining; built-ins remain
  authoritative; a stale/missing source requires re-preview; and live optional
  validation issues `#6` through `#11` remain open and separate with
  skipped-missing evidence still neither pass nor failure.

## ADR-0123: Optional Solver Plugin Manifest Reactivation GUI Is ViewModel-Driven And Non-Mutating

- Status: Accepted for experimental reactivation GUI implementation
- Date: 2026-06-27
- Context: OSW-EXP-087 defined reactivation semantics as design-only and
  OSW-EXP-088 added a pure reactivation view-model extension. The next safe slice
  is a PySide GUI surface that renders reactivation readiness, acknowledgements,
  stale-source/re-preview state, evidence/deactivation-history retention,
  shared-stack warnings, diagnostics, and action availability without runtime
  mutation.
- Decision: Implement a PySide reactivation panel
  (`OptionalSolverPluginManifestReactivationPanel`) under `src/osw/gui/dialogs/`.
  The panel consumes `OptionalSolverPluginManifestReactivationViewModel` records
  and renders summary, candidates, acknowledgements, diagnostics,
  shared-stack/conflict rows, stale-source/re-preview rows,
  evidence/deactivation-history retention, trust/provenance badges, safety
  guidance, and disabled/future action states. Acknowledgement interaction is
  widget-local and non-persistent via an injected pure callback; unsafe actions
  (run discovery, run validation, install/uninstall dependency, uninstall solver,
  execute solver, close issue) stay disabled/future-only, and reactivate/route
  actions remain future-only. The panel performs no runtime reactivation behavior,
  reactivation persistence, automatic activation, trust restoration, file
  restore/rewrite/delete, dependency install/uninstall, solver uninstall, plugin
  package import, directory scan, network fetch, discovery execution, validation,
  solver execution, issue mutation, release mutation, tag mutation, asset
  mutation, or version change.
- Consequences: Users can inspect future reactivation readiness and safety
  requirements in the GUI. Reactivation persistence and source mutation remain
  future-gated. User/plugin manifests remain untrusted, non-validating,
  provenance-preserving, and deactivation-history-retaining; built-ins remain
  authoritative; a stale/missing source requires re-preview; and live optional
  validation issues `#6` through `#11` remain open and separate with
  skipped-missing evidence still neither pass nor failure.

## ADR-0124: Optional Solver Plugin Manifest State Persistence Starts As Design-Only

- Status: Accepted for experimental state persistence design
- Date: 2026-06-27
- Context: OSW-EXP-089 added a view-model-driven reactivation GUI surface.
  Activation, deactivation, reactivation, and discovery-refresh UX state now has
  review surfaces, but state persistence semantics remain undefined. Persistence
  could be confused with automatic activation, trust restoration, validation
  success, dependency installation, solver execution, issue closure, release
  mutation, or certification without a design gate.
- Decision: Define optional solver plugin manifest state persistence semantics as
  design-only before implementation. Persistence remains explicit, versioned,
  redaction-first, provenance-preserving, acknowledgement-aware, history-retaining,
  non-validating, non-installing, non-executing, non-mutating, and separate from
  discovery, issues, releases, tags, assets, and certification. Specify
  persisted-state definition and forbidden content, storage location options,
  preconditions, an acknowledgement persistence/invalidation policy, a
  source/trust/provenance model, a redaction/privacy policy, a conceptual state
  schema model, a state-machine interaction with blocked transitions, a
  stale-source/re-preview policy, conflict/unsafe-claim policies, a
  validation/evidence policy, a ProjectSchema boundary, and design-only
  `OSPMG_PERSISTENCE_*` diagnostic reservations.
- Consequences: Future persistence view-model, schema, GUI, CLI, and
  export-summary gates have a safety contract. No runtime behavior changes in this
  gate, and live optional validation issues `#6` through `#11` remain open and
  separate. User/plugin manifests remain untrusted and non-validating unless
  separate evidence and trust gates exist; built-ins remain authoritative;
  deactivation/reactivation history and historical evidence are retained; and
  skipped-missing evidence remains neither pass nor failure. No runtime source,
  GUI source, view-model source, CLI source, ProjectSchema source, persistence
  implementation, file write, settings file, schema mutation, automatic
  activation, trust restoration, file restore/rewrite/delete, dependency
  install/uninstall, solver uninstall, plugin package import, directory scan,
  network fetch, discovery execution, validation execution, solver execution,
  release edit, issue mutation, tag mutation, asset mutation, bundled-solver claim,
  certification claim, validation-pass claim, validation-fail claim, issue-closure
  claim, or version change occurs in this design gate.

## ADR-0125: Optional Solver Plugin Manifest State Export Summary Starts As Design-Only

- Status: Accepted for experimental export-summary design
- Date: 2026-06-27
- Context: OSW-EXP-090 defined future state persistence semantics as design-only.
  The next adjacent need is a safe human-readable export summary for review and
  support, but export summaries could be confused with persistence, reloadable
  bundles, validation evidence, trust restoration, issue closure, or release
  mutation.
- Decision: Define optional solver plugin manifest state export-summary semantics
  as design-only before implementation. Export summaries remain explicit,
  redaction-first, provenance-preserving, acknowledgement-aware, history-retaining,
  non-validating, non-persistent, non-reloadable unless a future bundle gate says
  otherwise, non-installing, non-executing, non-mutating, and separate from
  discovery, issues, releases, tags, assets, and certification. Specify the
  export-summary definition and forbidden content, the export-summary vs
  persistence vs reloadable-bundle boundary, export preconditions, an
  acknowledgement model, a redaction/privacy policy, a conceptual summary content
  model, source/trust/provenance labels, a state coverage model with blocked
  interpretations, a stale-source/re-preview policy, conflict/unsafe-claim
  policies, a validation/evidence policy, a ProjectSchema boundary, and design-only
  `OSPMG_EXPORT_SUMMARY_*` diagnostic reservations.
- Consequences: Future export-summary view-model, GUI, CLI, report, and bundle
  gates have a safety contract. No runtime behavior changes in this gate, and live
  optional validation issues `#6` through `#11` remain open and separate.
  User/plugin manifests remain untrusted and non-validating unless separate
  evidence and trust gates exist; built-ins remain authoritative;
  deactivation/reactivation history and historical evidence are retained; and
  skipped-missing evidence remains neither pass nor failure. No runtime source, GUI
  source, view-model source, CLI source, ProjectSchema source, export
  implementation, file write, export file, reloadable bundle, clipboard behavior,
  open-output-folder behavior, persistence implementation, settings file, schema
  mutation, automatic activation, trust restoration, file restore/rewrite/delete,
  dependency install/uninstall, solver uninstall, plugin package import, directory
  scan, network fetch, discovery execution, validation execution, solver execution,
  release edit, issue mutation, tag mutation, asset mutation, bundled-solver claim,
  certification claim, validation-pass claim, validation-fail claim, issue-closure
  claim, or version change occurs in this design gate.

## ADR-0126: Optional Solver Plugin Manifest Persistence ViewModel Is Pure And Non-Writing

- Status: Accepted for experimental persistence view-model implementation
- Date: 2026-06-27
- Context: OSW-EXP-090 defined state persistence semantics as design-only, and
  OSW-EXP-091 defined adjacent export-summary semantics as design-only. The next
  safe slice is a pure view-model that can classify supplied optional solver
  plugin manifest UX state for future persistence review without writing state or
  changing runtime behavior.
- Decision: Implement a pure persistence view-model
  (`OptionalSolverPluginManifestPersistenceViewModel`) under
  `src/osw/experimental/optional_solvers/`. The view-model consumes supplied
  candidates, source/provenance data, acknowledgements, schema/migration
  metadata, stale-source state, conflicts, unsafe claims, evidence, and history,
  then produces deterministic summary, candidate, source, acknowledgement,
  diagnostic, redaction, schema, stale-source, conflict, unsafe-claim,
  evidence/history, trust, and action-state records. It performs no file IO,
  writes, settings-file creation, ProjectSchema mutation, GUI behavior, CLI
  behavior, reload, export, plugin package import, directory scan, network fetch,
  discovery execution, validation, install/uninstall, solver execution, issue
  mutation, release mutation, tag mutation, asset mutation, version bump,
  validation-pass/fail claim, issue-closure claim, bundled-solver claim, or
  certification claim.
- Consequences: Future persistence schema, writer, GUI, CLI, reload,
  export-summary, source-integration, discovery-integration, validation,
  install/uninstall, solver-execution, issue, and release gates have a stable
  data-only contract. User/plugin manifests remain untrusted and non-validating;
  built-ins remain authoritative; local path redaction remains visible;
  stale/missing sources require re-preview; deactivation/reactivation history and
  historical evidence remain retained; skipped-missing evidence remains neither
  pass nor failure; and live optional validation issues `#6` through `#11` remain
  open and separate.

## ADR-0127: Optional Solver Plugin Manifest Persistence Schema Model Is In-Memory And Non-Writing

- Status: Accepted for experimental persistence schema model implementation
- Date: 2026-06-27
- Context: OSW-EXP-090 defined state persistence semantics as design-only and
  OSW-EXP-092 implemented the pure persistence view-model. The next safe slice is
  a pure, in-memory schema model that defines the versioned record shape a future
  persistence writer would serialize, without writing state, creating a schema
  file, or changing runtime behavior.
- Decision: Implement a pure schema model
  (`OptionalSolverPluginManifestPersistenceSchemaModel`) under
  `src/osw/experimental/optional_solvers/`. It defines versioned, JSON-compatible,
  frozen record types (header, source, candidate, acknowledgement, diagnostic,
  redaction policy, migration, conflict, unsafe-claim, evidence/history,
  non-action flags, validation summary) and deterministic helpers for
  construction, `to_mapping`/`from_mapping` conversion, mapping validation,
  redaction, and adaptation from the OSW-EXP-092 persistence view-model. It reuses
  the reserved `OSPMG_PERSISTENCE_*` diagnostic vocabulary, keeps a redaction-first
  policy with raw absolute paths blocked, supports a current schema version plus
  the `osw-exp-092-preview` marker with migration treated as a diagnostic, and
  keeps all non-action flags false. It performs no file IO, writes, schema-file
  creation, settings-file creation, runtime state-file creation, ProjectSchema
  mutation, GUI behavior, CLI behavior, reload, export, plugin package import,
  directory scan, network fetch, discovery execution, validation, install/uninstall,
  solver execution, issue mutation, release mutation, tag mutation, asset mutation,
  version bump, validation-pass/fail claim, issue-closure claim, bundled-solver
  claim, or certification claim.
- Consequences: Future persistence writer, settings-file, runtime state-file,
  ProjectSchema-integration, GUI, CLI, reload, schema-migration, export-summary,
  source-integration, discovery-integration, validation, install/uninstall,
  solver-execution, issue, and release gates have a stable record-shape contract.
  User/plugin manifests remain untrusted and non-validating; built-ins remain
  authoritative; local path redaction remains enforced; stale/missing sources
  require re-preview; conflicts keep built-ins winning by default; unsafe claims
  are never accepted; deactivation/reactivation history and historical evidence
  remain retained; skipped-missing evidence remains neither pass nor failure; and
  live optional validation issues `#6` through `#11` remain open and separate.

## ADR-0128: Optional Solver Plugin Manifest Persistence GUI Starts As Design-Only

- Status: Accepted for experimental persistence GUI design
- Date: 2026-06-27
- Context: OSW-EXP-092 added a pure persistence view-model, and OSW-EXP-093
  added a pure in-memory persistence schema model. Future users need a GUI review
  surface for that state, but a persistence GUI could be mistaken for file
  writes, settings file creation, runtime state file creation, ProjectSchema
  mutation, automatic activation, trust restoration, validation evidence, issue
  closure, release mutation, tag mutation, asset mutation, or certification.
- Decision: Define persistence GUI semantics as design-only before
  implementation. The persistence GUI remains view-model/schema-model driven,
  explicit, redaction-first, acknowledgement-aware, schema/migration-aware,
  stale-source-aware, history-retaining, non-validating, non-writing,
  non-installing, non-executing, non-mutating, and separate from discovery,
  validation, issues, releases, tags, assets, reloads, exports, ProjectSchema,
  file dialogs, save dialogs, clipboard behavior, open-output-folder behavior,
  dependency install/uninstall, solver uninstall, solver execution, and
  certification.
- Consequences: Future persistence GUI implementation has a safety contract. No
  runtime behavior changes in this gate. No GUI source, runtime source,
  view-model source, schema-model source, CLI source, ProjectSchema source,
  persistence writer, settings file, runtime state file, schema file, export file,
  reloadable bundle, file dialog, save dialog, clipboard action,
  open-output-folder action, dependency install/uninstall, solver uninstall,
  plugin package import, directory scan, network fetch, discovery execution,
  validation execution, solver execution, issue mutation, release mutation, tag
  mutation, asset mutation, version bump, validation-pass claim, validation-fail
  claim, issue-closure claim, bundled-solver claim, or certification claim is
  added. User/plugin manifests remain untrusted and non-validating unless
  separate evidence and trust gates exist; built-ins remain authoritative;
  deactivation/reactivation history and historical evidence are retained; and
  live optional validation issues `#6` through `#11` remain open and separate.

## ADR-0129: Optional Solver Plugin Manifest Persistence GUI Is Review-Only And Non-Writing

- Status: Accepted for experimental persistence GUI implementation
- Date: 2026-06-27
- Context: OSW-EXP-092 added a pure persistence view-model, OSW-EXP-093 added a
  pure in-memory persistence schema model, and OSW-EXP-094 defined the GUI
  semantics as design-only. The next safe slice is a bounded PySide review
  surface that renders those supplied records without saving, reloading,
  exporting, activating, trusting, validating, or executing anything.
- Decision: Implement `OptionalSolverPluginManifestPersistencePanel` under
  `src/osw/gui/dialogs/` and expose it through the lazy `osw.gui.dialogs`
  package export. The panel renders summary, source, candidate, acknowledgement,
  diagnostic, redaction/privacy, schema/migration, stale-source/re-preview,
  conflict/shared-stack, unsafe-claim, evidence/history, trust/provenance,
  non-action flag, safety, and disabled action-state records from the persistence
  view-model and caller-supplied in-memory schema model records. Acknowledgement
  interaction is widget-local and non-persistent through an injected pure
  callback. All persistence, file, settings, runtime state, schema file,
  ProjectSchema, reload, export, file dialog, save dialog, clipboard,
  open-output-folder, CLI, automatic activation, trust restoration, discovery,
  validation, solver execution, install/uninstall, solver uninstall, issue,
  release, tag, asset, version, validation claim, issue-closure claim,
  bundled-solver claim, and certification actions remain disabled or absent.
- Consequences: Future persistence writer, settings-file, runtime state-file,
  ProjectSchema integration, CLI persistence, reload, export-summary,
  reloadable-bundle, source/discovery integration, validation, install/uninstall,
  solver-execution, issue, release, tag, asset, version, trust-elevation, and
  certification gates remain separate. Existing activation, deactivation,
  reactivation, discovery-refresh, persistence view-model, and schema-model
  behavior is not mutated. User/plugin manifests remain untrusted and
  non-validating; built-ins remain authoritative; stale sources require
  re-preview; unsafe claims remain blocked; deactivation/reactivation history and
  historical evidence are retained; skipped-missing evidence remains neither pass
  nor failure; package metadata remains `0.1.5rc1`; public prerelease remains
  `v0.1.5-rc1`; and live optional validation issues `#6` through `#11` remain
  open and separate.

## ADR-0130: Optional Solver Plugin Manifest Persistence CLI Starts As Design-Only

- Status: Accepted for experimental persistence CLI design
- Date: 2026-06-27
- Context: OSW-EXP-092 added a pure persistence view-model, OSW-EXP-093 added a
  pure in-memory persistence schema model, and OSW-EXP-095 added a
  view-model/schema-model driven PySide persistence GUI review surface. A future
  CLI surface is useful for headless review, CI, and support diagnostics, but CLI
  persistence could be mistaken for save/load/reload, file writes, settings file
  creation, runtime state file creation, schema file creation, ProjectSchema
  mutation, automatic activation, trust restoration, validation evidence, issue
  closure, release mutation, tag mutation, asset mutation, or certification.
- Decision: Define persistence CLI semantics as design-only before
  implementation. The persistence CLI remains dry-run/review/explain oriented,
  explicit, redaction-first, acknowledgement-aware, schema/migration-aware,
  stale-source-aware, history-retaining, non-validating, non-writing,
  non-installing, non-executing, non-mutating, and separate from discovery,
  validation, issues, releases, tags, assets, reloads, exports, ProjectSchema,
  save/load commands, clipboard behavior, open-output-folder behavior,
  dependency install/uninstall, solver uninstall, solver execution, and
  certification.
- Consequences: Future persistence CLI implementation has a safety contract. No
  runtime behavior changes in this gate. No CLI source, runtime source, GUI
  source, view-model source, schema-model source, ProjectSchema source,
  persistence writer, settings file, runtime state file, schema file, export
  file, reloadable bundle, clipboard action, open-output-folder action,
  dependency install/uninstall, solver uninstall, plugin package import,
  directory scan, network fetch, discovery execution, validation execution,
  solver execution, issue mutation, release mutation, tag mutation, asset
  mutation, version bump, validation-pass claim, validation-fail claim,
  issue-closure claim, bundled-solver claim, or certification claim is added.
  User/plugin manifests remain untrusted and non-validating unless separate
  evidence and trust gates exist; built-ins remain authoritative;
  deactivation/reactivation history and historical evidence are retained; and
  live optional validation issues `#6` through `#11` remain open and separate.

## ADR-0131: Optional Solver Plugin Manifest Export Summary ViewModel Is Pure And Non-Writing

- Status: Accepted for experimental export-summary view-model implementation
- Date: 2026-06-27
- Context: OSW-EXP-091 defined export-summary semantics as design-only, while
  OSW-EXP-092 through OSW-EXP-096 added persistence view-model, schema model, GUI
  review, and CLI design contracts. Future GUI, CLI, report, support-summary,
  file-export, clipboard, and bundle gates need a deterministic in-memory summary
  model, but that model could be mistaken for export, persistence, reloadability,
  validation evidence, trust restoration, issue closure, release mutation, or
  certification.
- Decision: Implement a pure export-summary view-model
  (`OptionalSolverPluginManifestExportSummaryViewModel`) under
  `src/osw/experimental/optional_solvers/`. The view-model consumes supplied
  sources, candidates, acknowledgements, diagnostics, redaction/privacy state,
  stale-source/re-preview state, conflicts, unsafe claims, evidence, and history,
  then produces deterministic header, section, source/provenance, candidate,
  acknowledgement, diagnostic, redaction, stale-source, conflict, unsafe-claim,
  evidence/history, limitation, non-action flag, and disabled/future action-state
  records. It adapts supplied persistence view-model and schema-model records
  without mutating them. It performs no file IO, writes, export file creation,
  clipboard behavior, report attachment, reloadable bundle creation, runtime
  persistence behavior, settings-file creation, runtime state-file creation,
  schema-file creation, ProjectSchema mutation, GUI behavior, CLI behavior,
  reload behavior, source behavior mutation, automatic activation, trust
  restoration, file restore/rewrite/delete, dependency install/uninstall, solver
  uninstall, plugin package import, directory scan, network fetch, discovery
  execution, validation execution, solver execution, issue mutation, release
  mutation, tag mutation, asset mutation, version bump, validation-pass/fail
  claim, issue-closure claim, bundled-solver claim, or certification claim.
- Consequences: Future export-summary GUI, CLI, report/support, file export,
  clipboard, reloadable-bundle, persistence writer, source-integration,
  discovery-integration, validation, install/uninstall, solver-execution, issue,
  release, tag, and asset gates have a stable data-only contract. Export
  summaries remain in-memory, non-writing, non-reloadable by default,
  non-validating, and non-mutating in this gate. User/plugin manifests remain
  untrusted by default; built-ins remain authoritative; local path redaction
  remains enforced; stale sources require re-preview; conflicts keep built-ins
  winning by default; unsafe claims are never accepted; deactivation/reactivation
  history and historical evidence remain retained; skipped-missing evidence
  remains neither pass nor failure; package metadata remains `0.1.5rc1`; public
  prerelease remains `v0.1.5-rc1`; and live optional validation issues `#6`
  through `#11` remain open and separate.

## ADR-0132: Optional Solver Plugin Manifest Export Summary GUI Starts As Design-Only

- Status: Accepted for experimental export-summary GUI design
- Date: 2026-06-27
- Context: OSW-EXP-091 defined state export-summary semantics as design-only,
  and OSW-EXP-097 added a pure export-summary view-model. Future users need a
  GUI review surface, but export-summary GUI could be mistaken for file export,
  clipboard behavior, report attachment, reloadable bundle creation, persistence,
  validation evidence, issue closure, release mutation, or certification.
- Decision: Define export-summary GUI semantics as design-only before
  implementation. Export-summary GUI remains view-model driven, explicit,
  redaction-first, acknowledgement-aware, stale-source-aware, limitation-visible,
  history-retaining, non-validating, non-writing, non-persistent,
  non-reloadable, non-installing, non-executing, non-mutating, and separate from
  discovery, validation, issues, releases, tags, assets, clipboard, report
  attachments, reloadable bundles, file export, file writes, ProjectSchema,
  persistence, reload behavior, dependency install/uninstall, solver uninstall,
  solver execution, trust restoration, and certification.
- Consequences: Future export-summary GUI implementation has a safety contract.
  No runtime behavior changes in this gate. No GUI source, runtime source,
  view-model source, schema-model source, CLI source, ProjectSchema source,
  persistence writer, settings file, runtime state file, schema file, export
  file, report file, reloadable bundle, file dialog, save dialog, clipboard
  action, report attachment action, open-output-folder action, dependency
  install/uninstall, solver uninstall, plugin package import, directory scan,
  network fetch, discovery execution, validation execution, solver execution,
  issue mutation, release mutation, tag mutation, asset mutation, version bump,
  validation-pass claim, validation-fail claim, issue-closure claim,
  bundled-solver claim, or certification claim is added. User/plugin manifests
  remain untrusted and non-validating unless separate evidence and trust gates
  exist; built-ins remain authoritative; deactivation/reactivation history and
  historical evidence are retained; skipped-missing remains neither pass nor
  failure; package metadata remains `0.1.5rc1`; public prerelease remains
  `v0.1.5-rc1`; and live optional validation issues `#6` through `#11` remain
  open and separate.

## ADR-0133: Optional Solver Plugin Manifest Export Summary GUI Is Review-Only

- Status: Accepted for experimental export-summary GUI implementation
- Date: 2026-06-27
- Context: OSW-EXP-091 defined export-summary semantics, OSW-EXP-097 added a
  pure export-summary view-model, and OSW-EXP-098 defined the export-summary GUI
  safety contract. Users need a PySide review surface, but a GUI could be
  mistaken for file export, clipboard behavior, report attachment, reloadable
  bundle creation, persistence, validation evidence, issue closure, release
  mutation, tag mutation, asset mutation, or certification.
- Decision: Implement `OptionalSolverPluginManifestExportSummaryPanel` as a
  view-model-driven PySide review panel over supplied in-memory export-summary
  records. The panel renders header, sections, source/provenance, candidate,
  acknowledgement, diagnostics, redaction/privacy, stale-source/re-preview,
  conflict/shared-stack, unsafe-claim, evidence/history, limitation,
  trust/provenance, non-action flag, safety, and disabled/future action-state
  data. Acknowledgement interaction is optional, widget-local, non-persistent,
  and callback-injected. The panel performs no file export, file writes, export
  file creation, report file creation, clipboard behavior, report attachment,
  open-output-folder behavior, reloadable bundle creation, runtime persistence
  behavior, settings-file creation, runtime-state-file creation, schema-file
  creation, ProjectSchema mutation, CLI behavior, reload behavior, source
  mutation, automatic activation, trust restoration, file restore/rewrite/delete,
  dependency install/uninstall, solver uninstall, plugin package import,
  directory scan, network fetch, discovery execution, validation execution,
  solver execution, issue/release/tag/asset mutation, version bump,
  validation-pass/fail claim, issue-closure claim, bundled-solver claim, or
  certification claim.
- Consequences: Users can inspect export-summary limitations in GUI without
  creating export files or changing runtime state. Actual file export,
  clipboard, report attachment, reloadable bundles, CLI export, persistence
  writer, ProjectSchema integration, and report integration remain future-gated.
  User/plugin manifests remain untrusted, non-validating, redaction-first,
  provenance-preserving, limitation-visible, and history-retaining. Package
  metadata remains `0.1.5rc1`, public prerelease remains `v0.1.5-rc1`, and live
  optional validation issues `#6` through `#11` remain open and separate.

## ADR-0134: Optional Solver Plugin Manifest State Writer Starts As Design-Only

- Status: Accepted for experimental state writer design
- Date: 2026-06-28
- Context: OSW-EXP-090 defined state persistence semantics. OSW-EXP-092 added a
  pure persistence view-model. OSW-EXP-093 added a pure in-memory persistence
  schema model. OSW-EXP-095 added a non-writing persistence GUI review surface.
  OSW-EXP-096 defined persistence CLI semantics as dry-run/review/explain only.
  OSW-EXP-097 and OSW-EXP-099 added export-summary view-model and GUI review
  surfaces. A future writer is useful, but a writer can easily be mistaken for
  validation evidence, trust restoration, automatic activation, ProjectSchema
  mutation, reload, export, issue closure, or release mutation.
- Decision: Define state writer semantics as design-only before implementation.
  The future writer must be explicit, redaction-first, schema-versioned,
  acknowledgement-aware, stale-source-aware, conflict-aware,
  unsafe-claim-blocking, history-retaining, non-validating,
  non-trust-restoring, non-activating, non-installing, non-executing,
  issue/release-safe, and separate from reload/export/report/ProjectSchema
  behavior.
- Consequences: Future writer implementation has a safety contract. No runtime
  behavior changes in this gate. No files are written in this gate. User/plugin
  manifests remain untrusted and non-validating unless separate evidence and
  trust gates exist. Package metadata remains `0.1.5rc1`, public prerelease
  remains `v0.1.5-rc1`, and live optional validation issues `#6` through `#11`
  remain open and separate.

## ADR-0135: Optional Solver Plugin Manifest State Writer ViewModel Is Pure And Non-Writing

- Status: Accepted for experimental state-writer view-model/schema-extension implementation
- Date: 2026-06-28
- Context: OSW-EXP-100 defined state-writer safety semantics as design-only.
  OSW-EXP-092/093 already provide pure persistence view-model and schema-model
  records, and OSW-EXP-097/099 provide export-summary records and GUI review.
  The next safe slice is a deterministic state-writer readiness/write-plan
  view-model that can review supplied state without writing files.
- Decision: Implement
  `OptionalSolverPluginManifestStateWriterViewModel` as a pure, side-effect-free,
  in-memory planning layer. It exposes storage options, write plans,
  file-format/schema-boundary records, source/trust/provenance rows, candidate
  writer rows, acknowledgement/expiry rows, redaction/privacy rows,
  schema/migration rows, stale-source rows, conflict/shared-stack rows,
  unsafe-claim rows, evidence/history rows, atomicity/error-plan rows,
  non-action flags, disabled/future action states, mapping/text renderers, and
  `OSPMG_STATE_WRITER_*` diagnostics. It adapts supplied persistence
  view-model, persistence schema-model, and export-summary view-model records
  without mutating them.
- Consequences: This gate adds automated view-model evidence only. It adds no
  actual writer implementation, file write, directory creation, runtime state
  file, settings file, schema file, export/report file, reloadable bundle,
  ProjectSchema mutation, GUI behavior, CLI behavior, reload/export behavior,
  clipboard/report/open-folder behavior, automatic activation, trust
  restoration, file restoration/rewrite/deletion, dependency install/uninstall,
  solver uninstall, plugin package import, directory scan, network fetch,
  discovery execution, validation execution, solver execution, issue/release/
  tag/asset mutation, version bump, validation-pass/fail claim, issue-closure
  claim, bundled-solver claim, or certification claim. Package metadata remains
  `0.1.5rc1`, public prerelease remains `v0.1.5-rc1`, and live optional
  validation issues `#6` through `#11` remain open and separate.

## ADR-0136: Optional Solver Plugin Manifest State Writer Is Explicit And Local-Only

- Status: Accepted for experimental state-writer implementation
- Date: 2026-06-28
- Context: OSW-EXP-100 defined state-writer semantics as design-only.
  OSW-EXP-101 added a pure state-writer readiness/write-plan view-model. A
  writer implementation is useful, but file writing can be mistaken for
  persistence integration, ProjectSchema mutation, reload behavior, export or
  report behavior, validation evidence, issue closure, release mutation, trust
  restoration, automatic activation, or certification.
- Decision: Implement an explicit local state writer under
  `src/osw/experimental/optional_solvers/`. The writer requires
  caller-supplied target paths and explicit write acknowledgement. It produces
  deterministic JSON payloads from supplied view-model/write-plan data, performs
  local preflight checks, and uses same-directory atomic temp-file/replace
  behavior. It does not choose default app/project/user paths, create
  directories, create settings/schema/export/report files, create reloadable
  bundles, mutate ProjectSchema, add GUI/CLI/reload/export/clipboard/report/
  open-folder behavior, run discovery/validation/solver execution,
  install/uninstall dependencies or solvers, import plugin packages, scan
  directories, fetch network manifests, mutate issues/releases/tags/assets,
  bump versions, or claim validation/certification.
- Consequences: Future reload, GUI writer controls, CLI writer commands,
  ProjectSchema integration, export/report integration, settings/runtime state
  files, schema files, reloadable bundles, source/discovery integration,
  validation, install/uninstall, solver execution, issue closure, release/tag/
  asset mutation, trust elevation, and certification claims remain
  future-gated. Written state files are local UX state only, not validation
  evidence, trust restoration, automatic activation, issue closure, release
  mutation, bundled-solver evidence, or certification.

## ADR-0137: Optional Solver Plugin Manifest Persistence CLI Is Explicit And Dry-Run-First

- Status: Accepted for experimental persistence CLI implementation
- Date: 2026-06-28
- Context: OSW-EXP-096 defined persistence CLI semantics as dry-run/review/
  explain. OSW-EXP-101 added a deterministic state-writer view-model.
  OSW-EXP-102 added an explicit local state-writer library. Users and
  maintainers need a CLI surface, but CLI persistence can be mistaken for live
  discovery, validation, ProjectSchema mutation, reload, report/export
  creation, issue closure, release mutation, trust restoration, automatic
  activation, or certification.
- Decision: Implement a bounded CLI surface over the state-writer view-model and
  state-writer library. The CLI defaults to review/dry-run. Actual write
  requires an explicit target path, explicit write mode, explicit
  acknowledgement, and writer preflight success. The CLI does not perform
  discovery, validation, solver execution, dependency install/uninstall, plugin
  package import, directory scan, network fetch, ProjectSchema mutation, GUI
  behavior, reload, report/export/clipboard/open-folder behavior, issue
  mutation, release mutation, tag mutation, asset mutation, or version changes.
- Consequences: Maintainers can exercise writer behavior from CLI without
  adding GUI controls or live discovery integration. Future reload, GUI writer
  controls, live state source integration, report/export CLI, prepared-machine
  validation, install/uninstall, solver execution, issue closure,
  release/tag/asset mutation, and certification remain future-gated. Written
  state files remain local UX state only, not validation evidence, trust
  restoration, automatic activation, issue closure, release mutation,
  bundled-solver evidence, or certification.

## ADR-0138: Optional Solver Plugin Manifest Export Summary CLI Starts As Design-Only

- Status: Accepted for experimental export-summary CLI design
- Date: 2026-06-28
- Context: OSW-EXP-091 defined export-summary semantics. OSW-EXP-097 added a
  pure export-summary view-model. OSW-EXP-099 added an export-summary GUI review
  panel. OSW-EXP-103 added a persistence CLI over the state-writer library. An
  export-summary CLI is useful, but it could be mistaken for report generation,
  reloadable bundle creation, persistence, validation evidence, issue closure,
  release mutation, tag mutation, asset mutation, or certification.
- Decision: Define export-summary CLI semantics as design-only before
  implementation. Future CLI must be explicit, redaction-first, stdout-first,
  human-reviewable, non-validating, non-trust-restoring, non-activating,
  non-reloading, non-discovering, non-executing, no-report-attachment,
  no-clipboard, no-open-folder, and issue/release-safe.
- Consequences: Future export-summary CLI implementation has a safety contract.
  No runtime behavior changes in this gate. No CLI source is edited in this
  gate. No export/report/reloadable-bundle output is created in this gate.

## ADR-0139: Optional Solver Plugin Manifest Export Summary CLI Is Stdout-First And Non-Exporting

- Status: Accepted for experimental export-summary CLI implementation
- Date: 2026-06-28
- Context: OSW-EXP-104 designed export-summary CLI semantics. OSW-EXP-097 added
  a pure export-summary view-model. OSW-EXP-099 added a GUI review panel.
  OSW-EXP-103 added persistence CLI over the state-writer library.
  Export-summary CLI can be useful for maintainers, but could be mistaken for
  file export, report generation, reloadable bundles, ProjectSchema mutation,
  validation evidence, issue closure, release mutation, tag mutation, asset
  mutation, or certification.
- Decision: Implement a bounded stdout-first export-summary CLI review surface.
  The CLI uses deterministic sample/unavailable state and existing
  export-summary view-model semantics. It does not perform live discovery,
  passive refresh, plugin import, directory scan, network fetch, validation,
  solver execution, dependency install/uninstall, ProjectSchema mutation, GUI
  behavior, reload, file export, report generation, clipboard, report
  attachment, open-output-folder behavior, issue/release/tag/asset mutation,
  version bump, validation-pass/fail claim, bundled-solver claim, or
  certification claim.
- Consequences: Users can inspect export-summary semantics from CLI. Actual
  file-output, report, reloadable-bundle, and live source integration behavior
  remain future-gated. Export-summary output remains human-review-only and
  non-validating.

## ADR-0140: Optional Solver Plugin Manifest Reload Starts As Design-Only

- Status: Accepted for experimental reload design
- Date: 2026-06-28
- Context: OSW-EXP-102 added an explicit local state writer. OSW-EXP-103 added
  a persistence CLI that can write state through the writer. OSW-EXP-105 added
  stdout-first export-summary CLI review. Reloading persisted state is useful
  but can be mistaken for trust restoration, automatic activation, validation
  evidence, ProjectSchema mutation, discovery, issue closure, or release
  mutation.
- Decision: Define reload semantics as design-only before implementation.
  Future reload must be explicit, user-selected, schema-aware,
  redaction-first, acknowledgement-aware, stale-source-aware, conflict-aware,
  unsafe-claim-blocking, history-retaining, non-validating,
  non-trust-restoring, non-activating, non-discovering, non-executing,
  ProjectSchema-safe, and issue/release-safe. This gate edits docs/tests only
  and adds no runtime source behavior.
- Consequences: Future reload view-model, GUI, CLI, and file-reader gates have
  a safety contract. Reload implementation remains future-gated. No persisted
  state file is read or parsed in this gate. No ProjectSchema, discovery,
  validation, solver, issue, release, tag, asset, or version behavior changes
  occur.

## ADR-0141: Optional Solver Plugin Manifest Reload View-Model Is Pure And Mapping-Only

- Status: Accepted for experimental reload view-model implementation
- Date: 2026-06-28
- Context: OSW-EXP-106 defined reload semantics as design-only. OSW-EXP-102
  added an explicit state writer. A reload view-model is needed before any file
  reader, GUI, or CLI reload behavior. Reload can be mistaken for trust
  restoration, automatic activation, validation evidence, ProjectSchema
  mutation, discovery, issue closure, release mutation, or certification.
- Decision: Implement a pure reload view-model under
  `src/osw/experimental/optional_solvers/`. It consumes caller-supplied payload
  mappings/records only. It does not read files, parse from paths, scan
  directories, fetch network data, import plugin packages, run discovery, run
  validation, execute solvers, mutate ProjectSchema, close issues, mutate
  releases/tags/assets, restore trust, or activate candidates. It exposes
  schema, redaction, acknowledgement, stale-source, conflict, unsafe-claim,
  evidence/history, trust diagnostics, and disabled/future actions.
- Consequences: Future reload file-reader, GUI, and CLI gates have a pure model
  to render. Runtime reload behavior remains future-gated. Written state remains
  local UX state only, not validation evidence, trust restoration, automatic
  activation, issue closure, release mutation, or certification.

## ADR-0142: Optional Solver Plugin Manifest Reload GUI Starts As Review-Only Design

- Status: Accepted for experimental reload GUI design
- Date: 2026-06-28
- Context: OSW-EXP-106 defined reload semantics as design-only. OSW-EXP-107
  added a pure reload view-model over caller-supplied mappings. Users need a
  future GUI review surface for reload state, but a GUI can be mistaken for
  file loading, runtime reload, trust restoration, automatic activation,
  validation evidence, ProjectSchema mutation, issue closure, release mutation,
  or certification.
- Decision: Define reload GUI semantics as design-only before implementation.
  Future reload GUI must consume already-built reload view-model records, remain
  read-only/review-only, and render schema, redaction, acknowledgement-expiry,
  stale-source, conflict, unsafe-claim, evidence/history, trust/provenance,
  diagnostics, disabled/future actions, and safety guidance. This gate adds no
  GUI source and no runtime behavior.
- Consequences: Future reload GUI implementation has a safety contract. File
  dialogs, file readers/parsers, runtime reload, ProjectSchema integration,
  activation, discovery, validation, solver execution, issue/release mutation,
  and certification claims remain future-gated. No persisted state file is read
  or parsed in this gate.

## ADR-0143: Optional Solver Plugin Manifest Reload GUI Is Review-Only

- Status: Accepted for experimental reload GUI implementation
- Date: 2026-06-28
- Context: OSW-EXP-106 defined reload semantics as design-only. OSW-EXP-107
  added a pure reload view-model over caller-supplied mappings. OSW-EXP-108
  designed a reload GUI review surface. Users need a GUI panel to inspect
  reload state, but it must not become a file dialog, runtime reload path,
  trust restoration surface, automatic activation surface, validation evidence
  surface, ProjectSchema mutation surface, issue closure tool, release mutation
  tool, or certification claim.
- Decision: Implement `OptionalSolverPluginManifestReloadPanel` as a read-only
  PySide review panel over already-built reload view-model records. The panel
  renders summary, source/provenance, schema/migration, candidates,
  acknowledgements/expiry, redaction/privacy, stale-source/re-preview,
  conflicts/shared stacks, unsafe claims, evidence/history, diagnostics,
  disabled/future actions, and safety guidance. The panel does not read files,
  parse files, open file dialogs, perform runtime reload, run discovery, run
  validation, execute solvers, mutate ProjectSchema, activate candidates,
  restore trust, close issues, mutate releases/tags/assets, or claim
  certification.
- Consequences: Future reload GUI entry points can reuse the panel. File
  dialog, file reader/parser, runtime reload, activation, discovery refresh,
  validation, ProjectSchema integration, CLI reload, and prepared-machine
  validation remain future-gated. No persisted state file is read or parsed in
  this gate.

## ADR-0144: Optional Solver Plugin Manifest Reload CLI Starts As Review-Only Design

- Status: Accepted for experimental reload CLI design
- Date: 2026-06-30
- Context: OSW-EXP-106 defined reload semantics as design-only. OSW-EXP-107
  added a pure reload view-model over caller-supplied mappings. OSW-EXP-109
  implemented a read-only reload GUI review panel. A CLI review surface is
  useful for maintainers and tests, but it can be mistaken for runtime file
  reading, state parsing, reload acceptance, trust restoration, automatic
  activation, validation evidence, ProjectSchema mutation, issue closure,
  release mutation, or certification.
- Decision: Define reload CLI semantics as design-only before implementation.
  Future reload CLI must consume already-built reload view-model records,
  remain headless/stdout-first/review-only, and render summary, source,
  schema, candidate lifecycle, acknowledgements, redaction, stale-source,
  conflict, unsafe-claim, evidence/history, diagnostics, disabled/future
  actions, file-reader boundaries, reload-acceptance boundaries, and
  non-validating exit-code semantics. This gate adds no CLI source and no
  runtime behavior.
- Consequences: Future reload CLI implementation has a safety contract. File
  readers/parsers, runtime reload, default paths, background reload,
  ProjectSchema integration, activation, discovery, validation, solver
  execution, issue/release mutation, and certification claims remain
  future-gated. No persisted state file is read or parsed in this gate.

## ADR-0145: Optional Solver Plugin Manifest Reload CLI Is Stdout-First Review-Only

- Status: Accepted for experimental reload CLI implementation
- Date: 2026-06-30
- Context: OSW-EXP-110 defined reload CLI semantics as design-only. OSW-EXP-107
  already provides a pure mapping-only reload view-model, and OSW-EXP-109
  provides a read-only GUI review panel. Maintainers need a headless CLI review
  surface, but the command could be mistaken for a persisted-state file reader,
  runtime reload path, trust restoration surface, automatic activation surface,
  validation evidence, ProjectSchema mutation, issue closure, release mutation,
  or certification.
- Decision: Implement `optional-solver-plugin-manifest-reload` as a
  stdout-first, review-only CLI over deterministic in-memory reload view-model
  state. The command supports text and JSON output for summary, schema, source,
  candidate, acknowledgement, diagnostic, redaction, stale-source, conflict,
  unsafe-claim, evidence/history, and action-state sections. `load-preview` is
  registered only as a disabled future action and returns `2` without implying
  validation failure. The implementation does not read files, parse persisted
  state, choose default paths, perform runtime reload, mutate ProjectSchema,
  run discovery, import plugin packages, validate, execute solvers, activate
  candidates, restore trust, close issues, mutate releases/tags/assets, bump
  versions, or certify manifests.
- Consequences: Reload review is available in headless workflows and tests
  without adding reload acceptance. File reader/parser behavior, runtime reload,
  schema migration, activation review, discovery refresh, ProjectSchema
  integration, validation, issue/release workflows, and certification remain
  future-gated.

## ADR-0146: Optional Solver Plugin Manifest Reload File Reader Requires Explicit Local Path Design

- Status: Accepted for experimental reload file-reader design
- Date: 2026-06-30
- Context: OSW-EXP-102 added an explicit state writer that can write local UX
  state files. OSW-EXP-107 added a pure reload view-model over caller-supplied
  mappings, and OSW-EXP-109 and OSW-EXP-111 added GUI/CLI review surfaces that
  deliberately avoid reading files. Users need a future bridge from explicit
  local state files into reload review, but file reading can be mistaken for
  trust restoration, automatic activation, validation evidence, ProjectSchema
  mutation, issue closure, release mutation, or certification.
- Decision: Define reload file-reader semantics as design-only before any
  implementation. The future reader must accept explicit caller-provided local
  paths only, with no default path, no background reload, no directory scan, no
  network fetch, and no plugin package import. It must validate file eligibility,
  size, encoding, JSON structure, payload kind, schema version, writer metadata,
  non-action flags, redaction/privacy, unsafe claims, stale-source state,
  conflicts, acknowledgement expiry, and trust/provenance, then return a safe
  in-memory mapping (or a diagnostic reader report) suitable for OSW-EXP-107
  reload view-model review. It reserves an `OSPMG_RELOAD_READER_*` diagnostics
  vocabulary. This gate adds no source, no CLI source, no GUI source, and no
  runtime file reading or parsing.
- Consequences: A future file-reader implementation (OSW-EXP-113) has a safety
  contract. Default paths, background reload, GUI file dialogs, CLI explicit-path
  reload, runtime reload acceptance, schema migration, discovery, validation,
  solver execution, ProjectSchema integration, issue/release/tag/asset mutation,
  and certification claims remain future-gated. No persisted state file is read or
  parsed in this gate; user/plugin files remain untrusted by default; built-ins
  remain authoritative; skipped-missing remains skipped-missing; and live optional
  validation issues `#6` through `#11` remain open and separate.

## ADR-0147: Optional Solver Plugin Manifest Reload File Reader Is Explicit-Path And Review-Only

- Status: Accepted for experimental reload file-reader implementation
- Date: 2026-06-30
- Context: OSW-EXP-102 added an explicit state writer, OSW-EXP-107 added a pure
  reload view-model over caller-supplied mappings, and OSW-EXP-109/111 added
  GUI/CLI review surfaces that avoid file reading. OSW-EXP-112 designed an explicit
  local file-reader boundary. Users need a safe bridge from explicit local state
  files into reload review, but file reading can be mistaken for trust restoration,
  automatic activation, validation evidence, ProjectSchema mutation, issue closure,
  release mutation, or certification.
- Decision: Implement a library-level reload file reader
  (`OptionalSolverPluginManifestReloadFileReader` /
  `read_optional_solver_plugin_manifest_reload_file`) under
  `src/osw/experimental/optional_solvers/`. It reads exactly one explicit
  caller-provided local path (no default path, no background reload, no directory
  scan, no network fetch, no glob, no plugin import) and validates file eligibility,
  size, UTF-8 encoding, JSON object shape, duplicate keys, payload kind, schema
  version/migration, non-action flags, redaction/privacy, unsafe claims,
  stale-source state, conflicts, evidence/history, acknowledgements, and provenance.
  It returns `OSPMG_RELOAD_READER_*` diagnostics and, only when no blockers remain,
  a sanitized in-memory mapping suitable for OSW-EXP-107 reload view-model review.
  It writes/creates/deletes no files and is not wired into the CLI or GUI.
- Consequences: Future CLI explicit-path (OSW-EXP-114/115) and GUI file-dialog
  (OSW-EXP-116/117) gates can reuse the reader. Runtime reload acceptance,
  activation review, discovery refresh, validation, ProjectSchema integration,
  issue/release/tag/asset mutation, and certification remain future-gated. No
  default path or background reload exists; user/plugin files remain untrusted by
  default; built-ins remain authoritative; skipped-missing remains skipped-missing;
  and live optional validation issues `#6` through `#11` remain open and separate.

## ADR-0148: Optional Solver Plugin Manifest Reload CLI Explicit Path Is Design-Only

- Status: Accepted for experimental reload CLI explicit-path design
- Date: 2026-06-30
- Context: OSW-EXP-111 implemented a stdout-first reload CLI review surface that
  keeps `load-preview` disabled/future-only, and OSW-EXP-113 implemented a
  library-level explicit-path reload file reader. A future CLI bridge is useful,
  but it can be mistaken for default/background reload, trust restoration,
  automatic activation, validation evidence, ProjectSchema mutation, issue
  closure, release mutation, or certification.
- Decision: Define CLI explicit-path semantics as design-only before
  implementation. Future `load-preview --path` must use the library reader,
  render reader diagnostics, route only reader `safe_mapping` output into the
  reload view-model, keep text/JSON stdout-first, preserve redaction/privacy, and
  use non-validation exit-code semantics. This gate adds no CLI source, no path
  argument implementation, no runtime file reading/parsing, and no runtime
  behavior.
- Consequences: Future OSW-EXP-115 implementation has a safety contract. Default
  paths, background reload, directory scans, network fetches, plugin imports, GUI
  file dialogs, runtime reload acceptance, activation, discovery, validation,
  solver execution, ProjectSchema integration, issue/release/tag/asset mutation,
  and certification claims remain future-gated. No persisted state file is read
  or parsed in this gate.

## ADR-0149: Optional Solver Plugin Manifest Reload CLI Explicit Path Uses Reader-First Review

- Status: Accepted for experimental reload CLI explicit-path implementation
- Date: 2026-06-30
- Context: OSW-EXP-111 added stdout-first reload CLI review over deterministic
  in-memory states. OSW-EXP-113 added an explicit-path library reload file
  reader. OSW-EXP-114 designed CLI explicit-path preview. Users need
  `load-preview --path` to inspect state-writer files from the CLI, but path
  loading can be mistaken for default/background reload, trusted reload
  acceptance, automatic activation, validation evidence, ProjectSchema mutation,
  issue closure, release mutation, or certification.
- Decision: Implement `load-preview --path` as reader-first, stdout-first
  review. Reader diagnostics render before view-model preview. Reader blockers
  prevent view-model preview. Reader safe mappings feed the reload view-model
  only for review. Text/JSON output preserve non-validation exit-code semantics
  and redacted diagnostics. There is no GUI file dialog, runtime reload
  acceptance, default path, ProjectSchema mutation, discovery/validation/solver
  execution, activation, trust restoration, issue/release/tag/asset mutation, or
  certification claim.
- Consequences: CLI can preview explicitly supplied local reload state files
  safely. GUI file dialog, runtime reload acceptance, activation, discovery
  refresh, validation, ProjectSchema integration, and prepared-machine validation
  remain future-gated. No default/background reload exists.

## ADR-0150: Optional Solver Plugin Manifest Reload GUI File Dialog Starts As Design-Only

- Status: Accepted for experimental reload GUI file-dialog design
- Date: 2026-06-30
- Context: OSW-EXP-109 implemented a read-only reload GUI review panel over
  already-built reload view-model records. OSW-EXP-113 added an explicit-path
  library reload file reader, and OSW-EXP-115 added reader-first CLI
  explicit-path preview. A future GUI file chooser is useful, but it can be
  mistaken for default/background reload, trusted reload acceptance, automatic
  activation, validation evidence, ProjectSchema mutation, issue closure,
  release mutation, or certification.
- Decision: Define GUI file-dialog semantics as design-only before
  implementation. Future GUI file-dialog preview must require explicit user file
  selection, call the OSW-EXP-113 reader, render reader diagnostics first, feed
  only reader `safe_mapping` output into the OSW-EXP-107 reload view-model, and
  keep the OSW-EXP-109 panel pure view-model rendering. This gate adds no GUI
  source, no CLI source, no runtime source, no file-reader source, no reload
  view-model source, no file dialog widgets, no file opening behavior, no
  runtime file reading/parsing, no runtime reload acceptance, no default path,
  no background reload, no CLI subprocess use, no ProjectSchema mutation, no
  discovery/validation/solver execution, no activation, no trust restoration,
  no issue/release/tag/asset mutation, and no certification claim.
- Consequences: Future OSW-EXP-117 implementation has a safety contract.
  Runtime reload acceptance, activation review, discovery refresh, validation,
  ProjectSchema integration, issue/release workflows, export/report integration,
  and certification remain future-gated. No persisted state file is read or
  parsed in this gate.

## ADR-0151: Optional Solver Plugin Manifest Reload GUI File Dialog Is Reader-First Preview

- Status: Accepted for experimental reload GUI file-dialog implementation
- Date: 2026-06-30
- Context: OSW-EXP-109 implemented a read-only reload GUI review panel over
  already-built reload view-model records. OSW-EXP-113 added an explicit-path
  library reload file reader, OSW-EXP-115 added reader-first CLI explicit-path
  preview, and OSW-EXP-116 designed GUI file-dialog semantics. Users need a GUI
  path to preview a state-writer UX state file, but GUI file selection can be
  mistaken for default/background reload, trusted runtime reload acceptance,
  automatic activation, validation evidence, ProjectSchema mutation, issue
  closure, release mutation, or certification.
- Decision: Implement `OptionalSolverPluginManifestReloadFileDialogPanel` as an
  outer PySide chooser/controller around the existing reload panel. It opens no
  native dialog during construction, supports injected file picker/reader/request
  and view-model factories for tests, reads only one explicitly selected path
  through `OptionalSolverPluginManifestReloadFileReader`, renders reader
  diagnostics before view-model preview, blocks view-model construction when the
  reader reports blockers, and routes only reader `safe_mapping` output into
  `OptionalSolverPluginManifestReloadViewModel.from_payload_mapping` for the
  existing review panel. Cancellation is non-error and preserves the prior
  preview. Selected-file display is redacted.
- Consequences: GUI users can explicitly preview reload state files without
  accepting runtime reload state. There is no default reload path, background
  reload, directory scan, network fetch, plugin package import, CLI subprocess
  bridge, ProjectSchema mutation, discovery/validation/solver execution,
  automatic activation, trust restoration, issue/release/tag/asset mutation,
  export/report/reloadable-bundle creation, version bump, validation-pass/fail
  claim, issue-closure claim, bundled-solver claim, or certification claim.

## ADR-0152: Optional Solver Plugin Manifest Reload Acceptance Starts As Session-Scoped Design

- Status: Accepted for experimental reload acceptance design
- Date: 2026-06-30
- Context: OSW-EXP-113 added an explicit-path reader, OSW-EXP-115 added
  reader-first CLI preview, and OSW-EXP-117 added GUI file-dialog preview.
  These surfaces can produce reviewed reload previews, but accepting a preview
  can be mistaken for trusted runtime reload, automatic activation,
  ProjectSchema mutation, persistence, discovery, validation evidence, issue
  closure, release mutation, or certification.
- Decision: Define reload acceptance as a future explicit user/caller action
  after reader and view-model review. Future acceptance may copy reviewed safe
  redacted non-trusted UX state into bounded in-memory/session review state and
  mark the preview acknowledged for that session. This gate adds no reload
  acceptance implementation, no runtime source, no GUI source, no CLI source, no
  file-reader source, no reload view-model source, no acceptance button, no
  acceptance CLI command, no persistence write, no ProjectSchema mutation, no
  runtime reload acceptance, no default/background reload, no discovery,
  validation, solver execution, automatic activation, trust restoration,
  issue/release/tag/asset mutation, validation-pass/fail claim, bundled-solver
  claim, or certification claim.
- Consequences: Future OSW-EXP-119+ implementation has a safety contract.
  Runtime reload acceptance, activation review, discovery refresh, validation,
  ProjectSchema integration, persistence writes, issue/release workflows,
  export/report/reloadable-bundle integration, and certification remain
  future-gated. No accepted state is created in this gate.

## ADR-0153: Optional Solver Plugin Manifest Reload Acceptance ViewModel Is Pure And Side-Effect-Free

- Status: Accepted for experimental reload acceptance view-model implementation
- Date: 2026-06-30
- Context: OSW-EXP-118 designed reload acceptance as a future explicit
  reviewed-preview-to-session UX state boundary. Existing reload reader, CLI, and
  GUI file-dialog preview surfaces remain preview/review-only. A view-model is
  needed before GUI/CLI acceptance implementation so readiness, blockers,
  acknowledgements, diagnostics, non-action flags, and future action states can
  be tested without mutating runtime state.
- Decision: Implement a pure reload acceptance view-model under
  `src/osw/experimental/optional_solvers/`. It consumes supplied reload
  preview/view-model records only. It models missing preview, not requested,
  blocked, ready, accepted-for-session-review, future activation/discovery
  review, and error states. It exposes `OSPMG_RELOAD_ACCEPTANCE_*` diagnostics,
  acknowledgements, expiry reasons, non-action flags, and disabled/future action
  states. It performs no file IO, reader invocation, GUI/CLI behavior, runtime
  reload acceptance, persistence writes, ProjectSchema mutation, discovery,
  validation, solver execution, activation, trust restoration,
  issue/release/tag/asset mutation, or certification claim.
- Consequences: Future GUI/CLI acceptance gates have a deterministic, testable
  contract. Runtime reload acceptance, persistence, activation, discovery
  refresh, validation, ProjectSchema integration, issue/release mutation, and
  prepared-machine validation remain future-gated. No accepted runtime state is
  created by this gate.

## ADR-0154: Optional Solver Plugin Manifest Reload Acceptance GUI Starts As Design-Only

- Status: Accepted for experimental reload acceptance GUI design
- Date: 2026-06-30
- Context: OSW-EXP-119 added a pure reload acceptance view-model over supplied
  reload preview records. A future PySide review surface is useful, but GUI
  acceptance can be mistaken for acceptance buttons, callbacks, runtime reload
  acceptance, persistence writes, ProjectSchema mutation, validation evidence,
  automatic activation, trust restoration, issue closure, release mutation, or
  certification.
- Decision: Define reload acceptance GUI review as design-only. The future GUI
  must consume `OptionalSolverPluginManifestReloadAcceptanceViewModel` and
  render summary/readiness, blockers, acknowledgements, acknowledgement expiry,
  accepted-for-session-review state, reader/preview provenance, schema/migration,
  redaction/privacy, stale-source, conflict/shared-stack, unsafe-claim,
  evidence/history, `OSPMG_RELOAD_ACCEPTANCE_*` diagnostics, non-action flags,
  and disabled/future actions. This gate adds no GUI source, no runtime source,
  no CLI source, no file-reader source, no reload view-model source, no reload
  acceptance view-model source, no acceptance buttons, no acceptance callbacks,
  no acceptance CLI commands, no persistence writes, no ProjectSchema mutation,
  no runtime reload acceptance, no default/background reload, no discovery,
  validation, solver execution, activation, trust restoration,
  issue/release/tag/asset mutation, validation-pass/fail claim, bundled-solver
  claim, or certification claim.
- Consequences: Future OSW-EXP-121 implementation has a safety contract.
  Runtime reload acceptance, persistence writes, activation, discovery refresh,
  validation, ProjectSchema integration, issue/release workflows, export/report/
  reloadable-bundle behavior, and certification remain future-gated. No GUI
  acceptance behavior is implemented in this gate.

## ADR-0155: Optional Solver Plugin Manifest Reload Acceptance GUI Is View-Model-Only

- Status: Accepted for experimental reload acceptance GUI implementation
- Date: 2026-06-30
- Context: OSW-EXP-119 added a pure reload acceptance view-model and OSW-EXP-120
  designed a future PySide review surface. The implementation must make
  acceptance readiness inspectable without converting preview or file selection
  into runtime acceptance, persistence, ProjectSchema mutation, validation
  evidence, automatic activation, trust restoration, issue closure, release
  mutation, or certification.
- Decision: Implement
  `OptionalSolverPluginManifestReloadAcceptancePanel` as a view-model-only
  PySide panel over already-built
  `OptionalSolverPluginManifestReloadAcceptanceViewModel` records. The panel
  renders summary/readiness, blockers, acknowledgements, expiry,
  accepted-state scope, reader/preview provenance, schema/migration,
  redaction/privacy, candidate lifecycle, stale-source, conflict/shared-stack,
  unsafe claims, evidence/history, trust/provenance, diagnostics, non-action
  flags, disabled/future actions, and safety guidance. It opens no file dialog,
  performs no file IO, invokes no reader, calls no CLI bridge, creates no
  output files, writes no persistence, mutates no ProjectSchema, runs no
  discovery, validation, solver execution, install, or uninstall, activates no
  candidates, restores no trust, mutates no issues/releases/tags/assets, bumps
  no version, and claims no validation pass/fail, bundled solver support, or
  certification.
- Consequences: Reload acceptance can now be reviewed in the GUI as automated
  GUI evidence while runtime acceptance remains future-gated. Future CLI
  acceptance, accepted-state storage, activation/discovery review consumption,
  ProjectSchema integration, prepared-machine validation, issue/release
  workflows, output creation, and certification remain separate gates.

## ADR-0156: Optional Solver Plugin Manifest Reload Acceptance CLI Starts As Design-Only

- Status: Accepted for experimental reload acceptance CLI design
- Date: 2026-07-01
- Context: OSW-EXP-119 added a pure reload acceptance view-model and OSW-EXP-121
  added a view-model-only GUI acceptance review panel. A future stdout-first CLI
  review surface is useful for terminal and CI review, but CLI acceptance can be
  mistaken for acceptance commands, flags, callbacks, runtime reload acceptance,
  hidden file reads, reader invocation, persistence writes, ProjectSchema
  mutation, validation evidence, automatic activation, trust restoration, issue
  closure, release mutation, or certification.
- Decision: Define reload acceptance CLI review as design-only. A future CLI
  must consume supplied `OptionalSolverPluginManifestReloadAcceptanceViewModel`
  records and render summary/readiness, blockers, acknowledgements,
  acknowledgement expiry, accepted-state scope, reader/preview provenance,
  schema/migration, redaction/privacy, candidate lifecycle, stale-source,
  conflict/shared-stack, unsafe-claim, evidence/history,
  `OSPMG_RELOAD_ACCEPTANCE_*` diagnostics, non-action flags, disabled/future
  actions, and exit-code semantics. This gate adds no CLI source, no GUI source,
  no runtime source, no file-reader source, no reload view-model source, no
  reload acceptance view-model source, no acceptance CLI commands, no acceptance
  flags, no acceptance callbacks, no file IO, no reader invocation, no GUI
  subprocess use, no persistence writes, no ProjectSchema mutation, no runtime
  reload acceptance, no default/background reload, no discovery, validation,
  solver execution, activation, trust restoration, issue/release/tag/asset
  mutation, validation-pass/fail claim, bundled-solver claim, or certification
  claim.
- Consequences: Future OSW-EXP-123 implementation has a safety contract.
  Runtime reload acceptance, persistence writes, activation, discovery refresh,
  validation, ProjectSchema integration, issue/release workflows, export/report/
  reloadable-bundle behavior, and certification remain future-gated. No CLI
  acceptance behavior is implemented in this gate.

## ADR-0157: Optional Solver Plugin Manifest Reload Acceptance CLI Is Review-Only

- Status: Accepted for experimental reload acceptance CLI implementation
- Date: 2026-07-01
- Context: OSW-EXP-119 added a pure reload acceptance view-model. OSW-EXP-121
  added a view-model-only GUI review panel. OSW-EXP-122 designed a stdout-first
  CLI review surface. Users need CLI visibility into acceptance readiness, but
  CLI acceptance can be mistaken for runtime reload acceptance, automatic
  activation, validation evidence, ProjectSchema mutation, persistence write,
  issue closure, release mutation, or certification.
- Decision: Implement a stdout-first reload acceptance CLI review module under
  `src/osw/cli/`. It consumes deterministic in-memory
  `OptionalSolverPluginManifestReloadAcceptanceViewModel` records only and
  renders summary, blockers, acknowledgements, expiry, accepted-state scope,
  provenance, diagnostics, non-action flags, disabled/future actions, and
  safety guidance. `accept-future` remains disabled/future-only and
  non-mutating. The CLI performs no file IO, file parsing, reader invocation,
  GUI calls, GUI subprocess use, runtime reload acceptance, persistence write,
  ProjectSchema mutation, discovery, validation, solver execution, activation,
  trust restoration, issue/release/tag/asset mutation, or certification claim.
- Consequences: Future runtime acceptance, if any, remains separately gated.
  Existing reload CLI explicit-path preview remains preview-only. Existing GUI
  acceptance panel remains review-only. No accepted runtime state is created by
  this gate.

## ADR-0158: Optional Solver Plugin Manifest Reload Acceptance Persistence Remains Explicit and Non-Authoritative

- Status: Accepted for experimental reload acceptance persistence design
- Date: 2026-07-02
- Context: OSW-EXP-119 added a pure reload acceptance view-model. OSW-EXP-121
  added a view-model-only GUI review panel. OSW-EXP-123 added a stdout-first CLI
  review surface. Users may want persistence of reviewed acceptance UX state,
  but persistence can be mistaken for runtime reload acceptance, trust
  restoration, automatic activation, validation evidence, validation failure,
  ProjectSchema mutation, issue closure, release mutation, or certification.
- Decision: Define reload acceptance persistence as an explicit, redacted,
  non-authoritative future record derived from OSW-EXP-119 acceptance view-model
  records. This gate adds no source and no writer behavior. Future persistence
  must be explicit, dry-run-first, redaction-first, acknowledgement-bound,
  expiry-aware, stale-source-aware, conflict-visible, unsafe-claim-blocked,
  ProjectSchema-safe, issue/release-safe, and certification-safe. Runtime
  acceptance, persistence implementation, ProjectSchema mutation, discovery,
  validation, solver execution, activation, trust restoration,
  issue/release/tag/asset mutation, and certification claims remain
  future-gated.
- Consequences: Future OSW-EXP-125/126 have a deterministic persistence
  contract. GUI and CLI acceptance review remain review-only. No persisted
  acceptance state or runtime accepted state is created by this gate.

## ADR-0159: Optional Solver Plugin Manifest Reload Acceptance Persistence ViewModel Is Non-Writing

- Status: Accepted for experimental reload acceptance persistence view-model
  implementation
- Date: 2026-07-02
- Context: OSW-EXP-119 added a pure reload acceptance view-model. OSW-EXP-123
  added a stdout-first CLI review surface. OSW-EXP-124 designed future reload
  acceptance persistence. Persistence planning can be mistaken for runtime
  acceptance, trusted reload, validation evidence, ProjectSchema mutation, issue
  closure, release mutation, or certification.
- Decision: Implement a pure reload acceptance persistence view-model under
  `src/osw/experimental/optional_solvers/`. The view-model consumes supplied
  acceptance records and renders future persistence readiness, write-plan data,
  storage policy, acknowledgements, expiry, blockers, diagnostics, non-action
  flags, disabled/future actions, and safety guidance. It performs no file IO,
  no writer invocation, no reader invocation, no CLI/GUI calls, no subprocess,
  no runtime reload acceptance, no persistence write, no ProjectSchema mutation,
  no discovery, no validation, no solver execution, no activation, no trust
  restoration, no issue/release/tag/asset mutation, and no certification claim.
- Consequences: Future OSW-EXP-126 has a deterministic view-model contract.
  Persistence writer behavior remains separately gated. GUI and CLI acceptance
  review remain review-only. No persisted acceptance state or runtime accepted
  state is created by this gate.

## ADR-0160: Optional Solver Plugin Manifest Reload Acceptance Persistence Writer Is Explicit and Non-Authoritative

- Status: Accepted for experimental reload acceptance persistence writer
  implementation
- Date: 2026-07-02
- Context: OSW-EXP-124 designed future reload acceptance persistence.
  OSW-EXP-125 added a pure persistence view-model. Users need a bounded way to
  write reviewed UX state, but persistence can be mistaken for runtime reload
  acceptance, trust restoration, automatic activation, validation evidence,
  ProjectSchema mutation, issue closure, release mutation, or certification.
- Decision: Implement an explicit-path, dry-run-first, redacted writer for
  reload acceptance persistence review records. Actual writes require caller
  acknowledgement and an explicit target path. The writer performs no runtime
  reload acceptance, no active acceptance mutation, no ProjectSchema mutation,
  no discovery, no validation, no solver execution, no activation, no trust
  restoration, no issue/release/tag/asset mutation, and no certification claim.
  The writer does not read input state files or invoke the reload file reader.
- Consequences: Reviewed reload acceptance UX state can be written as a local
  non-authoritative record. Persistence writer success remains distinct from
  runtime acceptance and validation evidence. CLI/GUI integration remains
  separately gated.

## ADR-0161: Optional Solver Plugin Manifest Reload Acceptance Persistence CLI Starts As Design-Only

- Status: Accepted for experimental reload acceptance persistence CLI design
- Date: 2026-07-03
- Context: OSW-EXP-125 added a pure persistence view-model for reload
  acceptance review records. OSW-EXP-126 added an explicit-path,
  dry-run-first writer API. A future stdout-first CLI can make persistence
  readiness and write plans inspectable, but CLI persistence can be mistaken for
  actual persistence writes, runtime reload acceptance, trusted reload state,
  automatic activation, validation evidence, validation failure, ProjectSchema
  mutation, issue closure, release mutation, or certification.
- Decision: Define the reload acceptance persistence CLI as design-only. A
  future CLI may render deterministic in-memory
  `OptionalSolverPluginManifestReloadAcceptancePersistenceViewModel` records,
  dry-run/write-plan data, explicit target path policy, writer result review,
  acknowledgements, expiry, schema/migration, redaction/privacy, provenance,
  stale-source, conflict/shared-stack, unsafe-claim, evidence/history,
  `OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_CLI_*` diagnostics, non-action flags,
  disabled/future actions, exit-code semantics, and safety guidance. This gate
  adds no CLI implementation, no source edits, no writer invocation, no file
  writes, no input state file reading/parsing, no reload file-reader
  invocation, no OSW-EXP-102 state-writer invocation, no GUI behavior, no
  subprocess use, no runtime reload acceptance, no active acceptance mutation,
  no ProjectSchema mutation, no default/background write, no discovery, no
  validation, no solver execution, no activation, no trust restoration, no
  issue/release/tag/asset mutation, no validation-pass/fail claim, no
  bundled-solver claim, and no certification claim.
- Consequences: Future persistence CLI implementation has a safety contract.
  Existing acceptance CLI/GUI review surfaces remain review-only. The
  OSW-EXP-126 writer remains a separately invoked local API until a future CLI
  implementation gate wires it intentionally. No persisted acceptance record is
  created by this gate.

## ADR-0162: Optional Solver Plugin Manifest Reload Acceptance Persistence CLI Is Dry-Run-Only

- Status: Accepted for experimental reload acceptance persistence CLI
  implementation
- Date: 2026-07-03
- Context: OSW-EXP-126 added an explicit-path dry-run-first writer.
  OSW-EXP-127 designed a persistence CLI review/write-plan surface. Exposing
  persistence through CLI can be mistaken for runtime acceptance, trusted reload
  state, ProjectSchema mutation, validation evidence, issue closure, release
  mutation, or certification.
- Decision: Implement a stdout-first persistence CLI that renders deterministic
  in-memory
  `OptionalSolverPluginManifestReloadAcceptancePersistenceViewModel` records and
  dry-run writer plans. The CLI calls the writer only through
  `plan_reload_acceptance_persistence_write` with `dry_run=True`.
  `write-future` remains disabled/future-only and non-mutating. The CLI
  performs no actual file writes, no writer call with `dry_run=False`, no input
  state-file reading/parsing, no reload file-reader invocation, no OSW-EXP-102
  state-writer invocation, no GUI behavior, no subprocess use, no runtime reload
  acceptance, no active acceptance mutation, no ProjectSchema mutation, no
  default/background write, no discovery, no validation, no solver execution,
  no activation, no trust restoration, no issue/release/tag/asset mutation, and
  no certification claim.
- Consequences: Users can inspect persistence readiness and dry-run write plans
  from the CLI without creating persisted records. Actual CLI write behavior,
  GUI persistence review, ProjectSchema integration, prepared-machine
  validation, issue/release workflows, and certification-safe release evidence
  remain separately gated.

## ADR-0163: Optional Solver Plugin Manifest Reload Acceptance Persistence GUI Review Is Display-Only

- Status: Accepted for experimental reload acceptance persistence GUI review
  design
- Date: 2026-07-03
- Context: OSW-EXP-125 added a pure persistence view-model. OSW-EXP-126
  added an explicit-path dry-run-first writer. OSW-EXP-128 added a
  dry-run-only persistence CLI review surface. A GUI surface may be useful for
  reviewing persistence state and writer plans, but GUI persistence can be
  mistaken for runtime acceptance, ProjectSchema mutation, validation evidence,
  issue closure, release mutation, or certification.
- Decision: Design a future PySide GUI review surface that displays
  persistence readiness, writer dry-run/result data, target/storage policy,
  acknowledgements, expiry, diagnostics, non-action flags, disabled/future
  actions, and safety guidance. This gate adds no GUI source and invokes no
  writer. Runtime reload acceptance, actual writes through GUI, ProjectSchema
  mutation, discovery, validation, solver execution, activation, trust
  restoration, issue/release/tag/asset mutation, and certification claims
  remain out of scope.
- Consequences: OSW-EXP-130 has a deterministic GUI review design contract.
  The OSW-EXP-126 writer remains not reachable from GUI until a separate
  implementation gate. Persistence records remain non-authoritative local
  review records.

## ADR-0164: Optional Solver Plugin Manifest Reload Acceptance Persistence GUI Review Panel Is Display-Only

- Status: Accepted for experimental reload acceptance persistence GUI review
  implementation
- Date: 2026-07-03
- Context: OSW-EXP-125 added a pure persistence view-model. OSW-EXP-126 added
  an explicit-path dry-run-first writer. OSW-EXP-128 added a dry-run-only
  persistence CLI review surface. OSW-EXP-129 designed a display-only
  persistence GUI review surface. A GUI implementation can be mistaken for
  writer invocation, file writes, runtime reload acceptance, ProjectSchema
  mutation, validation evidence, issue closure, release mutation, or
  certification.
- Decision: Implement a PySide GUI review panel under `src/osw/gui/dialogs/`
  that consumes supplied persistence view-model records and supplied writer
  dry-run/result records only. It renders persistence readiness, writer result
  data, target/storage policy, acknowledgements, expiry, schema/migration,
  redaction/privacy, provenance, lifecycle, stale-source, conflict,
  unsafe-claim, evidence/history, diagnostics, non-action flags,
  disabled/future actions, and safety guidance. It performs no writer
  invocation, no file IO, no input state-file parsing, no reload file-reader
  invocation, no CLI/subprocess use, no runtime reload acceptance, no active
  acceptance mutation, no ProjectSchema mutation, no discovery, no validation,
  no solver execution, no activation, no trust restoration, no
  issue/release/tag/asset mutation, and no certification claim.
- Consequences: Users can review persistence readiness and writer-result
  records in the GUI without mutation. Any GUI write workflow remains
  separately gated. Persistence records remain non-authoritative local review
  records.

## ADR-0165: Optional Solver Plugin Manifest Reload Acceptance Persistence GUI Write Is Explicit And Dry-Run-First

- Status: Accepted for experimental reload acceptance persistence GUI write
  design
- Date: 2026-07-03
- Context: OSW-EXP-125 added a pure persistence view-model. OSW-EXP-126 added
  an explicit-path dry-run-first writer. OSW-EXP-128 added a dry-run-only
  persistence CLI review/write-plan surface. OSW-EXP-130 added a display-only
  persistence GUI review panel. A future GUI write workflow may be useful for
  persisting local review records, but GUI write affordances can be mistaken
  for runtime reload acceptance, ProjectSchema mutation, validation evidence,
  issue closure, release mutation, or certification.
- Decision: Design a future GUI write workflow that starts from the
  display-only persistence GUI review panel, requires explicit target
  selection, requires dry-run-first writer planning, requires acknowledgement
  review, requires explicit confirmation, and uses the OSW-EXP-126 writer API
  for any future local review-record write. This gate adds no GUI source,
  invokes no writer, writes no files, reads or parses no input state files,
  invokes no reload file reader, invokes no OSW-EXP-102 state writer, calls no
  CLI code, uses no subprocesses, accepts no runtime reload, mutates no
  ProjectSchema, runs no discovery, validation, or solver execution, performs
  no activation or trust restoration, mutates no issues/releases/tags/assets,
  and makes no certification claim.
- Consequences: OSW-EXP-132 has a deterministic GUI write design contract if a
  write UI is ever needed. The OSW-EXP-130 panel remains display-only until a
  separate implementation gate. Persistence records remain non-authoritative
  local review records and remain separate from runtime acceptance, validation,
  ProjectSchema state, issue state, release state, and certification.

## ADR-0166: Optional Solver Plugin Manifest Reload Acceptance Persistence GUI Write Is Explicit, Dry-Run-First, And Non-Authoritative

- Status: Accepted for experimental reload acceptance persistence GUI write
  implementation
- Date: 2026-07-03
- Context: OSW-EXP-126 added an explicit-path dry-run-first writer. OSW-EXP-130
  added a display-only GUI review panel. OSW-EXP-131 designed a future GUI
  write workflow. GUI writes can be mistaken for runtime acceptance,
  ProjectSchema mutation, validation evidence, issue closure, release mutation,
  or certification.
- Decision: Implement a GUI write panel requiring explicit target, dry-run,
  acknowledgement, and confirmation before invoking the OSW-EXP-126 writer.
  The panel writes only local review-record persistence files through the
  OSW-EXP-126 writer. It performs no write on construction, refresh, target
  assignment, or dry-run; selects no default target path; performs no
  background write; performs no input state-file parsing; invokes no reload
  file reader or OSW-EXP-102 state writer; uses no CLI/subprocess bridge;
  performs no runtime reload acceptance or ProjectSchema mutation; runs no
  discovery, validation, or solver execution; performs no activation or trust
  restoration; mutates no issues/releases/tags/assets; and makes no
  certification claim.
- Consequences: Users can perform an explicit local review-record persistence
  write from GUI when all gates pass. GUI write success remains distinct from
  runtime acceptance and validation evidence. Any ProjectSchema or validation
  integration remains separately gated.

## ADR-0167: Optional Solver Plugin Manifest Reload Acceptance Persistence CLI Write Is Explicit, Dry-Run-First, And Non-Authoritative

- Status: Accepted for experimental reload acceptance persistence CLI write
  design
- Date: 2026-07-03
- Context: OSW-EXP-126 added an explicit-path dry-run-first writer.
  OSW-EXP-128 added a dry-run-only persistence CLI review surface. OSW-EXP-132
  added an explicit-target, dry-run-first, acknowledgement-gated,
  confirmation-gated GUI write panel. Future CLI writes can be mistaken for
  runtime acceptance, ProjectSchema mutation, validation evidence, issue
  closure, release mutation, or certification.
- Decision: Design a future CLI write workflow requiring explicit target,
  dry-run-first planning, caller acknowledgement, write confirmation, and
  explicit replacement policy before invoking the OSW-EXP-126 writer. This gate
  adds no CLI source, invokes no writer, writes no files, reads or parses no
  input state files, invokes no reload file reader, invokes no OSW-EXP-102
  state writer, calls no GUI code, uses no subprocesses, accepts no runtime
  reload, mutates no ProjectSchema, runs no discovery, validation, or solver
  execution, performs no activation or trust restoration, mutates no
  issues/releases/tags/assets, and makes no certification claim.
- Consequences: OSW-EXP-134 has a deterministic CLI write design contract if a
  future actual-write command is implemented. CLI write success, if later
  implemented, remains explicit local review-record persistence only and
  remains separate from runtime acceptance, validation, ProjectSchema state,
  issue state, release state, and certification.

## ADR-0168: Optional Solver Plugin Manifest Reload Acceptance Persistence CLI Write Uses The Writer Gate Only

- Status: Accepted for experimental reload acceptance persistence CLI write
  implementation
- Date: 2026-07-03
- Context: OSW-EXP-126 added an explicit-path dry-run-first persistence writer.
  OSW-EXP-128 added a stdout-first dry-run-only persistence CLI review surface.
  OSW-EXP-133 designed a future explicit-target, dry-run-first,
  acknowledgement-gated, confirmation-gated CLI write workflow. Actual CLI
  writes can be mistaken for runtime reload acceptance, ProjectSchema mutation,
  validation evidence, issue closure, release mutation, trust restoration,
  automatic activation, bundled solver support, or certification.
- Decision: Implement the `write` subcommand for
  `optional-solver-plugin-manifest-reload-acceptance-persistence`. The command
  requires explicit `--target`, `--acknowledge-persistence-write`, and
  `--confirm-persistence-write`; calls the OSW-EXP-126 writer first with
  `dry_run=True`; stops if the dry run is blocked; and calls the writer with
  `dry_run=False` only for the confirmed explicit local review-record write.
  It does not read or parse input state files, invoke the reload file reader,
  invoke the OSW-EXP-102 state writer, call GUI code, use subprocesses, accept
  runtime reload, mutate ProjectSchema, run discovery, validation, or solver
  execution, activate candidates, restore trust, mutate issues/releases/tags/
  assets, bump versions, or claim validation success, validation failure,
  issue closure, bundled solver support, or certification.
- Consequences: The CLI can persist a local non-authoritative review record
  when all gates pass. Review subcommands remain non-writing. Persisted records
  remain separate from runtime acceptance, ProjectSchema state, validation
  evidence, issue state, release state, and certification.

## ADR-0169: Optional Solver Plugin Manifest Reload Acceptance Persistence Summary Audit Is Non-Authoritative

- Status: Accepted for experimental reload acceptance persistence summary audit
  design
- Date: 2026-07-03
- Context: OSW-EXP-124 through OSW-EXP-134 completed the local reload
  acceptance persistence chain across design, view-model, writer, CLI, and GUI
  surfaces. Users may need a summary/audit view of what was reviewed or written.
  Such audit output can be mistaken for runtime reload acceptance, validation
  evidence, ProjectSchema state, issue closure, release mutation, or
  certification.
- Decision: Design a future summary/audit surface that reports chain coverage,
  supplied CLI/GUI write results, diagnostics, acknowledgements, expiry,
  non-action flags, disabled/future actions, and safety boundaries. Summary
  audit remains non-authoritative and consumes supplied records only. This gate
  adds no source, invokes no writer, reads or writes no files, calls no CLI or
  GUI behavior, mutates no ProjectSchema, performs no discovery, validation, or
  solver execution, and makes no issue, release, bundled-solver, or
  certification claims.
- Consequences: OSW-EXP-136 has a deterministic summary/audit contract.
  Summary audit output remains distinct from runtime acceptance and validation
  evidence. Prepared-machine validation and ProjectSchema integration remain
  separately gated.

## ADR-0170: Optional Solver Plugin Manifest Reload Acceptance Persistence Summary Audit Is Supplied-Record-Only

- Status: Accepted for experimental reload acceptance persistence summary audit
  implementation
- Date: 2026-07-03
- Context: OSW-EXP-124 through OSW-EXP-134 completed a local reload acceptance
  persistence chain across design, view-model, writer, CLI, and GUI surfaces.
  OSW-EXP-135 designed a non-authoritative summary/audit surface. A summary
  audit can be mistaken for runtime acceptance, validation evidence,
  ProjectSchema state, issue closure, release mutation, or certification.
- Decision: Implement a pure in-memory summary/audit model that consumes
  supplied records only. The audit renders chain coverage, supplied CLI/GUI
  write summaries, diagnostics, acknowledgements, expiry, redaction,
  non-action flags, disabled/future actions, and safety boundaries. The audit
  performs no writer invocation, no file IO, no reader invocation, no CLI/GUI
  calls, no subprocess use, no ProjectSchema mutation, no discovery, no
  validation, no solver execution, no activation, no trust restoration, no
  issue/release/tag/asset mutation, and no certification claim.
- Consequences: Maintainers can review persistence chain state without
  mutation. Summary audit output remains distinct from runtime acceptance and
  validation evidence. Prepared-machine validation and ProjectSchema
  integration remain separately gated.

## ADR-0171: Reload Acceptance Persistence Must Not Mutate ProjectSchema Without a Separate Gate

- Status: Accepted for experimental ProjectSchema boundary design
- Date: 2026-07-03
- Context: OSW-EXP-124 through OSW-EXP-136 completed local reload acceptance
  persistence and summary audit surfaces. Persistence records and summary
  audits can be mistaken for ProjectSchema state or validation evidence.
  ProjectSchema mutation has stronger semantics than local UX review
  persistence.
- Decision: Define a strict boundary that reload acceptance persistence
  records, writer results, CLI/GUI writes, and summary audits do not mutate
  ProjectSchema and are not ProjectSchema evidence. Any future ProjectSchema
  integration requires separate design, implementation, prepared-machine
  validation, explicit user review, and trust/provenance/stale/conflict/
  unsafe-claim review gates. This gate adds no source and performs no
  ProjectSchema mutation.
- Consequences: Persistence and ProjectSchema semantics remain separate.
  Future ProjectSchema work has a deterministic boundary contract. Local
  persistence records remain non-authoritative UX review records.

## ADR-0172: Reload Acceptance Persistence ProjectSchema Boundary Is Supplied-Record-Only

- Status: Accepted for experimental ProjectSchema boundary implementation
- Date: 2026-07-03
- Context: OSW-EXP-137 designed a strict ProjectSchema boundary for local
  reload acceptance persistence records, writer results, CLI/GUI writes, and
  summary audits. Those records can be mistaken for ProjectSchema state,
  ProjectSchema validation evidence, trust restoration, activation, issue
  closure, release mutation, or certification.
- Decision: Implement a pure in-memory, supplied-record-only, deterministic,
  redaction-first ProjectSchema boundary model. The model consumes supplied
  persistence, persistence view-model, writer, CLI write, GUI write, and
  summary audit mappings only; renders ProjectSchema non-meaning, schema
  separation, prohibited automatic flows, future preconditions, permitted
  non-authoritative candidates, blockers, validation-evidence boundaries,
  trust/provenance boundaries, lifecycle boundaries, built-in/shared-stack
  boundaries, issue/release/certification boundaries, redaction/privacy rows,
  diagnostics, non-action flags, and disabled/future actions; and performs no
  ProjectSchema source edit, ProjectSchema mutation, ProjectSchema field
  addition, ProjectSchema migration, ProjectSchema validation evidence, file
  IO, writer invocation, reader invocation, CLI/GUI call, subprocess use,
  runtime reload acceptance, discovery, validation, solver execution,
  activation, trust restoration, issue/release/tag/asset mutation, version
  bump, or certification claim.
- Consequences: Maintainers can review whether supplied reload acceptance
  persistence records remain outside ProjectSchema without mutating project
  state. Prepared-machine validation, ProjectSchema integration, issue/release
  work, and certification claims remain separately gated.

## ADR-0173: Prepared-Machine Optional Solver Validation Requires Explicit Local Prerequisites and a Runnable Command

- Status: Accepted for validation prerequisite documentation
- Date: 2026-07-03
- Context: `OSW-VALID-OPTIONAL_PREPARED_MACHINE_MANIFEST_STATE_VALIDATION`
  parked after OSW-EXP-138. Required regression and QA/static checks passed,
  but no current runnable prepared-machine manifest-state validation command
  was found in the repository and required optional solver/package
  prerequisites were missing on this machine.
- Decision: Document the missing prerequisites and command requirements before
  retrying prepared-machine validation. Focused regressions, GUI tests, QA
  checks, persistence records, summary audit output, and ProjectSchema boundary
  output must not be treated as prepared-machine success. This documentation
  gate installs no dependencies, installs no solvers, runs no solver execution,
  implements no validation command, mutates no ProjectSchema, mutates no
  issues/releases/tags/assets, and makes no validation-pass, validation-fail,
  issue-closure, bundled-solver, or certification claim.
- Consequences: Prepared-machine validation remains parked until operator
  preparation or a separate command design/implementation gate provides a safe
  runnable command and the required local prerequisites are present. Issues
  `#6` through `#11` remain open. Package metadata remains `0.1.5rc1`, public
  prerelease remains `v0.1.5-rc1`, and a future validation retry has explicit
  prerequisites and evidence boundaries.

## ADR-0174: Optional Solver Prepared-Machine Validation Requires an Explicit Local Command

- Status: Accepted for validation command design
- Date: 2026-07-03
- Context: Prepared-machine validation is parked. Missing prerequisites have
  been documented. There is no current safe runnable prepared-machine
  manifest-state validation command. Focused regression tests are not a
  substitute for prepared-machine validation.
- Decision: Design a future explicit local command with preflight, plan, run,
  diagnostics, prerequisites, evidence, and safety outputs. Future
  implementation must not install dependencies, mutate ProjectSchema, mutate
  issues/releases/tags/assets, or claim certification. Skipped-missing must
  remain separate from pass.
- Consequences: Validation retry has a deterministic command contract.
  Prepared-machine validation remains parked until implementation and local
  prerequisites exist. Issues `#6` through `#11` remain open.

## ADR-0175: Optional Solver Prepared-Machine Validation Command Is Local-Only and Non-Installing

- Status: Accepted for validation command implementation
- Date: 2026-07-03
- Context: Prepared-machine validation was parked. OSW-EXP-139 designed an
  explicit local command because no safe runnable prepared-machine
  manifest-state validation command existed. Missing prerequisites must not
  trigger automatic installation, solver execution, ProjectSchema mutation,
  issue/release mutation, or certification claims.
- Decision: Implement a local-only prepared-machine validation command with
  `explain`, `prerequisites`, `preflight`, `plan`, `run`, `diagnostics`,
  `evidence`, and `safety` subcommands. The command detects prerequisites with
  `shutil.which` and `importlib.util.find_spec`, without installing
  dependencies, importing optional packages, executing solvers, running
  arbitrary user workloads, or scanning arbitrary locations. Evidence writing
  is explicit and local only through `--write-evidence --evidence-dir`. The
  command does not mutate ProjectSchema, issues, releases, tags, assets, or
  versions, and it does not claim certification.
- Consequences: The next OSW-VALID retry has a runnable command. Missing
  prerequisites still park validation rather than becoming pass/fail
  overclaims. Issues `#6` through `#11` remain open until a separate triage
  gate.

## ADR-0176: OpenFOAM Template Compatibility Requires Variant-Aware Property File Generation

- Status: Accepted for OpenFOAM template compatibility fix design
- Date: 2026-07-04
- Context: GitHub issue `#18` was created for the `transportProperties` vs
  `physicalProperties` mismatch. OpenFOAM Foundation v11/v12 expects
  `constant/physicalProperties`, while the existing OSW OpenFOAM templates and
  golden fixtures assume `constant/transportProperties`. ESI OpenFOAM and older
  Foundation releases may still require `transportProperties`. Live validation
  (WSL-only) showed the OSW-generated cavity case failing under OpenFOAM 12 while
  OpenFOAM Foundation 12's official `icoFoam` cavity tutorial ran end-to-end.
- Decision: Design a variant-aware template generation policy rather than a
  blanket rename. Future implementation (OSW-EXP-142) must preserve legacy/ESI
  `transportProperties` support while adding Foundation v11/v12
  `physicalProperties` behavior, select the variant via an explicit option or
  passive detection (no background detection, no solver execution required),
  reserve an `OSW_OPENFOAM_TEMPLATE_*` diagnostic vocabulary, and cover both modes
  with unit/golden tests. Live solver validation remains a separate gate.
- Consequences: Issue `#18` has a safe, non-breaking fix path. Implementation
  requires source/template/golden updates in OSW-EXP-142; this design gate makes
  none. No certification, production-readiness, bundled-solver, or
  native-Windows-validation claim is made. At this design gate, issue `#18`
  remained open until implementation and validation occurred; ADR-0180 records
  the later WSL-scoped closure.

## ADR-0177: OpenFOAM Property File Generation Is Variant-Aware

- Status: Accepted for OpenFOAM template compatibility implementation
- Date: 2026-07-04
- Context: GitHub issue `#18` tracks Foundation v11/v12 `physicalProperties`
  support. OSW's legacy OpenFOAM templates, case generator, and golden fixtures
  used `constant/transportProperties`; OpenFOAM Foundation v11/v12 instead reads
  `constant/physicalProperties`, while ESI OpenFOAM and Foundation <= 10 keep the
  legacy file. ADR-0176 designed a variant-aware fix rather than a blanket rename;
  OSW-EXP-142 implements it.
- Decision: Implement an explicit `OpenFOAMPropertyFileLayout` selector
  (`legacy` → `transportProperties`, `foundation_v11_plus` →
  `physicalProperties`) on the cavity/duct configs, the request metadata, and the
  `openfoam-write-case --property-file-layout` CLI option. Preserve the legacy
  layout as the default so existing behavior, fixtures, and callers are
  unchanged. Add the Foundation `physicalProperties` template content (matching
  OpenFOAM 12's `icoFoam` cavity tutorial evidence: a single dimensioned `nu`
  entry, no `transportModel`) and add Foundation v11/v12 golden fixtures beside
  the retained legacy fixtures. Unknown selectors raise a deterministic
  `OSW_OPENFOAM_TEMPLATE_VARIANT_UNSUPPORTED` error. Do not run OpenFOAM in
  implementation tests; keep live validation a separate gate.
- Consequences: Issue `#18` has an implemented, non-breaking source fix. Live
  OpenFOAM validation remains separate (WSL-only evidence; `foamVersion` wrapper
  caveat). No certification, production-readiness, bundled-solver, or
  native-Windows-validation claim is made. At this implementation gate, issue
  `#18` remained open until the live-validation and issue-update gates completed;
  ADR-0180 records the later WSL-scoped closure. Package metadata remains
  `0.1.5rc1`; public prerelease remains `v0.1.5-rc1`.

## ADR-0178: OpenFOAM PISO Templates Need Algorithm-Aware pFinal Generation

- Status: Accepted for OpenFOAM pFinal fix design
- Date: 2026-07-04
- Context: GitHub issue `#19` tracks a missing `pFinal` entry in
  `system/fvSolution/solvers`. Live validation (OSW-VALID, WSL-only) showed the
  OSW-EXP-142 Foundation v11/v12 generated cavity case reading
  `constant/physicalProperties` and passing `blockMesh`, but `icoFoam` then failed
  with `keyword pFinal is undefined` on the PISO final corrector. `pFinal` appears
  nowhere in tracked source/tests/docs. SIMPLE/`simpleFoam` steady-state cases (the
  duct default) have no final-corrector pressure solve and are not affected the
  same way. This is a separate blocker from the `physicalProperties` fix (issue
  `#18`).
- Decision: Design an algorithm-aware `fvSolution` policy. Add a `pFinal` solver
  entry (preferred form `pFinal { $p; relTol 0; }`, mirroring the OpenFOAM 12
  `icoFoam` cavity tutorial) for PISO/`icoFoam` cases where the solver requires a
  final-pressure solve; keep SIMPLE/`simpleFoam` behavior unchanged (no `pFinal`).
  Gate the entry on the selected algorithm/solver, not on the property-file layout.
  Reserve an `OSW_OPENFOAM_FVSOLUTION_*` diagnostic vocabulary. Keep the source
  implementation, golden fixtures, and live validation in later gates
  (OSW-EXP-144 and a live-validation retry).
- Consequences: Issue `#19` has a safe, algorithm-aware design path. Implementation
  must update source/templates/golden/tests in OSW-EXP-144 (the cavity `fvSolution`
  golden gains `pFinal`; the duct `simpleFoam` golden is unchanged). Issue `#18`
  remains open until the generated cavity runs `icoFoam` end-to-end, which requires
  both the `physicalProperties` fix (landed) and the `pFinal` fix (designed here).
  No certification, production-readiness, bundled-solver, or
  native-Windows-validation claim is made. Package metadata remains `0.1.5rc1`;
  public prerelease remains `v0.1.5-rc1`.

## ADR-0179: OpenFOAM PISO fvSolution Generation Includes pFinal

- Status: Accepted for OpenFOAM pFinal implementation
- Date: 2026-07-04
- Context: Issue `#19` tracks a missing `pFinal` solver entry in
  `system/fvSolution/solvers`. The OSW-EXP-142 Foundation v12 generated cavity
  reads `constant/physicalProperties` and passes `blockMesh`, but `icoFoam` fails
  when `pFinal` is absent (PISO final corrector). SIMPLE/`simpleFoam` cases have no
  final-corrector pressure solve and do not require the entry. ADR-0178 designed an
  algorithm-aware fix; OSW-EXP-144 implements it.
- Decision: Add algorithm-aware `pFinal` generation. A `_PFINAL_SOLVER_BLOCK`
  (`pFinal { $p; relTol 0; }`) is injected via a `$pfinal_block` placeholder into
  the cavity/duct `fvSolution` `solvers` dictionary. The cavity always emits it
  (always `icoFoam`); the duct emits it only for `icoFoam` (PISO) and omits it for
  `simpleFoam` (SIMPLE), whose generated output is byte-identical to before. The
  `pFinal` entry reuses the `p` solver via the OpenFOAM `$p` macro and sets
  `relTol 0`. Gating is on the selected algorithm, not the property-file layout;
  `physicalProperties` behavior is unchanged. The cavity `fvSolution` golden gains
  `pFinal`; the duct golden is unchanged. Tests assert PISO and SIMPLE layouts
  separately and never run OpenFOAM.
- Consequences: Issue `#19` has an implemented source fix. Issue `#18` end-to-end
  live validation can be retried (both the `physicalProperties` and `pFinal` fixes
  now exist). At this implementation gate, live solver validation remained a
  separate gate and issues `#18` and `#19` remained open. No certification,
  production-readiness, bundled-solver, or native-Windows-validation claim is made.
  Package metadata remains `0.1.5rc1`; public prerelease remains `v0.1.5-rc1`.

## ADR-0180: OpenFOAM v12 Template Compatibility Issues Closed With WSL-Scoped Evidence

- Status: Accepted for issue closure status
- Date: 2026-07-04
- Context: After OSW-EXP-142 and OSW-EXP-144, a WSL-scoped live OpenFOAM
  validation gate generated the Foundation cavity case with
  `constant/physicalProperties` and `system/fvSolution` `pFinal`. The run
  reported `blockMesh` exit 0, `icoFoam` exit 0 end-to-end, time directories from
  `0` to `1`, an end marker, and no recurrence of the previous `pFinal` fatal
  error. Duct status remains generation/layout-verified only.
- Decision: Treat GitHub issues `#18` and `#19` as closed for the bounded
  OpenFOAM v12 template compatibility criteria. Issue `#18` covers
  `physicalProperties`/layout compatibility; issue `#19` covers the `pFinal`
  solver entry for OpenFOAM 12 PISO cavity generation. Closure comments were
  posted before closure and labels remained intact.
- Consequences: Optional live validation issue `#9` remains open, as do issues
  `#6` through `#11`. The evidence is WSL-only, local validation artifacts are
  not release assets, and the `foamVersion` delegation-wrapper caveat remains.
  No native-Windows validation, certification, production-readiness,
  bundled-solver, or release-readiness claim is made. Package metadata remains
  `0.1.5rc1`; public prerelease remains `v0.1.5-rc1`.
