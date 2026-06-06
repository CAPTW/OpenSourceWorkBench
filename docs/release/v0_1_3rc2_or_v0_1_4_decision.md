# v0.1.3rc2 vs v0.1.4-rc1 release boundary decision

Date: 2026-06-06

Repo HEAD reviewed: `e889eb56591b9c36673c38fb9f7fa7749e05f72f`

## Public Release Baseline

- Current public release: `v0.1.3-rc1`
- Public release tag target: `a6e8d3a8211e02359841d10e1947e16ab847b132`
- GitHub Release state: published prerelease, not draft
- Release assets: wheel, sdist, Windows portable ZIP, `SHA256SUMS.txt`, and
  `release_asset_manifest.json`

OpenSolver Workbench remains educational/research software. It is not a stable
production CAE platform, an industrial-certified solver product, a MATLAB,
Simulink, ANSYS, Abaqus, or commercial CAD clone, or a bundled-solver
distribution.

## Current Develop

- Branch: `develop`
- HEAD: `e889eb56591b9c36673c38fb9f7fa7749e05f72f`
- Active version: `0.1.3rc2.dev0`

This decision gate does not change package metadata. If maintainers accept the
recommended boundary below, a later metadata-alignment gate must update version
metadata deliberately.

## Completed Work Since v0.1.3-rc1

The changes on `develop` after the public `v0.1.3-rc1` tag include:

- public documentation polish and release-status reconciliation;
- release asset download smoke automation and offline CI workflow;
- Windows portable ZIP UX checks and documentation;
- duplicate hygiene, maintenance revalidation, and issue closure triage;
- onboarding examples, tutorials, examples index updates, and closure evidence;
- code signing / installer strategy documentation and closure evidence;
- v0.1.4 feature selection, scope lock, and completion review;
- Plugin Manager UX / install receipt implementation and closure;
- ResultViewer / FieldViewer workflow implementation and closure;
- VFEA experimental scope definition and closure;
- release trust, docs, and test/QA hardening.

## Closed Issue Classification

| Issue | Title | Category | Release classification |
| --- | --- | --- | --- |
| `#1` | Clean remaining local duplicate-file hygiene records | maintenance hygiene | `0.1.3rc2` maintenance-compatible |
| `#2` | Automate release asset download smoke | release automation | `0.1.3rc2` maintenance-compatible |
| `#3` | Add post-public release checklist | release documentation | `0.1.3rc2` maintenance-compatible |
| `#4` | Review Windows portable ZIP user experience | packaging / release trust | `0.1.3rc2` maintenance-compatible |
| `#5` | Prepare v0.1.3rc2 maintenance revalidation gate | maintenance validation | `0.1.3rc2` maintenance-compatible |
| `#12` | Plan v0.1.4 development cycle | roadmap planning | `v0.1.4` feature-line planning |
| `#13` | Improve onboarding examples and tutorials | docs / onboarding | compatible with either boundary |
| `#14` | Enhance ResultViewer and FieldViewer workflow | GUI / result workflow feature | `v0.1.4` feature-line candidate |
| `#15` | Improve Plugin Manager UX and install receipts | plugin / GUI feature | `v0.1.4` feature-line candidate |
| `#16` | Evaluate code signing and installer strategy | release trust planning | compatible with either boundary |
| `#17` | Define VFEA experimental plugin scope | experimental roadmap planning | `v0.1.4` feature-line planning |

## Remaining Open Issues

| Issue | Title | Environment requirement |
| --- | --- | --- |
| `#6` | Run live Gmsh validation | local Gmsh executable and suitable fixtures |
| `#7` | Run live GNU Octave validation | local GNU Octave executable |
| `#8` | Run live CalculiX ccx validation | local `ccx` executable |
| `#9` | Run live OpenFOAM validation | configured OpenFOAM environment |
| `#10` | Run live CoolProp and Cantera validation | optional CoolProp and Cantera Python packages |
| `#11` | Run live PyVista and meshio validation | optional PyVista/meshio packages and suitable display or off-screen setup |

These issues remain valuable validation evidence, but they are
environment-dependent and should stay separate from the release boundary
decision unless maintainers require live optional validation before any next
prerelease.

## Option Analysis

### Option A: `0.1.3rc2`

Use this option if maintainers want the next public prerelease to stay on the
existing active metadata line and treat most post-public work as maintenance,
release trust, docs, and small UX polish.

Strengths:

- aligns with current active metadata `0.1.3rc2.dev0`;
- keeps release continuity from `v0.1.3-rc1`;
- fits the duplicate hygiene, release asset smoke, portable ZIP UX, onboarding,
  code-signing strategy, and revalidation work.

Weaknesses:

- under-communicates the completed v0.1.4 feature-line work;
- Plugin Manager UX/install receipts and ResultViewer / FieldViewer workflow
  are visible public UX improvements;
- issues `#12`, `#14`, `#15`, and `#17` were explicitly planned, executed, and
  closed under the `v0.1.4` milestone.

### Option B: `v0.1.4-rc1`

Use this option if maintainers want the next public prerelease boundary to match
the completed feature-line scope.

Strengths:

- matches the closed `v0.1.4` milestone work;
- communicates feature-level public UX improvements clearly;
- separates v0.1.3 post-public maintenance from the completed v0.1.4
  workflow/product-polish and VFEA scope-definition line;
- gives release notes a cleaner story: Plugin Manager UX, ResultViewer /
  FieldViewer workflow, onboarding/tutorials, release trust, and VFEA planning.

Weaknesses:

- current metadata still reports `0.1.3rc2.dev0`;
- requires a later metadata-alignment gate before any tag or release asset work;
- live optional validation remains open and must be called out as
  environment-dependent.

### Option C: Defer Release Prep

Use this option if maintainers want additional design or validation before any
new public prerelease boundary.

Good reasons to defer:

- continue with `OSW-EXP-002_FEASPEC_IR_DESIGN` before release planning;
- run one or more live optional validation gates on a machine with required
  solvers/packages;
- perform another release-readiness pass after external validation evidence is
  available.

Cost:

- delays a public prerelease that already has a completed v0.1.4 planned scope;
- keeps the current active metadata line disconnected from completed
  feature-line planning for longer.

## Recommendation

Recommended option: `v0.1.4-rc1`.

Rationale:

- `#12`, `#14`, `#15`, and `#17` were planned and closed as v0.1.4 scope.
- The completed Plugin Manager UX and ResultViewer / FieldViewer workflow work
  is user-visible feature-line improvement, not only release maintenance.
- The v0.1.4 completion review already records the planned scope as complete.
- The remaining open issues are live optional validation, which is useful but
  environment-dependent and not required to define the feature-line boundary.

This is a decision only. The current active version remains `0.1.3rc2.dev0`.

Follow-up metadata status: the release-boundary decision was accepted by
[v0.1.4-rc1 candidate metadata alignment](v0_1_4_rc1_candidate.md), which
aligns package and CLI metadata to `0.1.4rc1` while leaving the `v0.1.4-rc1`
tag, assets, and GitHub Release for later dedicated gates.

## Required Next Gates If Accepted

If maintainers accept `v0.1.4-rc1`, run separate gates in order:

1. Metadata alignment gate:
   - decide package version such as `0.1.4rc1`;
   - align package metadata, CLI version, release notes, and docs;
   - preserve existing public tags unchanged.
2. Final revalidation gate:
   - rerun focused and broad QA;
   - verify docs links, scope drift, architecture boundaries, release gate, and
     solver artifact checks.
3. Tag gate:
   - create an annotated local tag only after metadata and QA pass;
   - verify the tag object and peeled target;
   - keep tag push separate unless explicitly approved.
4. Asset build / download smoke gate:
   - build wheel, sdist, and portable ZIP if desired;
   - verify `SHA256SUMS.txt`, manifest, archive safety, and smoke checks.
5. Release draft / publish gate:
   - create or update GitHub Release only in a dedicated release gate;
   - publish only after assets, checksums, limitations, and prerelease wording
     are verified.

## Non-Goals

- No version bump in this gate.
- No tag creation, deletion, retargeting, or push in this gate.
- No GitHub Release edit or creation in this gate.
- No release asset build, upload, overwrite, or replacement in this gate.
- No issue closure or issue mutation in this gate.
- No FEASpec or VFEA implementation.
- No live optional validation execution.

## Known Risks

- Active metadata `0.1.3rc2.dev0` does not match the recommended
  `v0.1.4-rc1` boundary until a later metadata gate.
- Live optional validation issues `#6` through `#11` remain environment
  dependent.
- The current public release remains a prerelease.
- The Windows portable ZIP remains unsigned, with no MSI, MSIX, or code
  signing.
- External solvers are optional and not bundled.
- VFEA remains experimental, planning-only, and unimplemented.
- Public docs on `develop` may be newer than the tagged `v0.1.3-rc1` source.
