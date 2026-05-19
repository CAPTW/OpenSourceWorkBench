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
