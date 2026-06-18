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
  `.cvg` contents, write ResultDataset files, add a write-capable import CLI,
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
