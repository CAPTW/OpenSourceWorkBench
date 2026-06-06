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
  package and CLI version `0.1.3rc2.dev0`, while the current public release
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
  validation, ProjectSchema bridging, CalculiX case planning, Abaqus export
  planning, VLM integration, and any solver execution remain separate future
  gates.

## ADR-0035: FEASpec Validator Contract Precedes Runtime Validation

- Status: Accepted for experimental design
- Date: 2026-06-07
- Context: The FEASpec Python model layer can load, basic-check, and serialize
  examples and benchmark seeds, but it is intentionally structural only. A
  future semantic validator needs stable diagnostic categories, severity
  taxonomy, approval rules, solver handoff blockers, and benchmark readiness
  rules before any runtime validator, ProjectSchema bridge, or solver exporter
  exists.
- Decision: Define the FEASpec validator as a design-only contract first. The
  contract reserves required diagnostic codes, requires human review before an
  approved FEASpec can proceed toward future solver handoff, keeps
  CalculiX-first compatibility planning, and treats Abaqus as optional and
  non-default only.
- Consequences: Runtime validator implementation, ProjectSchema bridging,
  CalculiX case planning, Abaqus export planning, VLM integration, and solver
  execution remain separate future gates. Candidates remain untrusted and must
  not be treated as solver-ready.
