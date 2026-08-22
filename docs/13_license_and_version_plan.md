# License And Version Plan

Status: historical license/version plan; current package metadata is `0.1.5`
and current public prerelease is `v0.1.5-rc3`

This historical document records the v0.1 maintainer license decision, package
version scheme, tag plan, and release artifact policy. Older `v0.1.3-rc1`
references in this file describe the release-candidate line at the time of that
gate, not the current public prerelease. It does not provide legal advice,
create a Git tag, announce a public release, or approve redistribution of
third-party solver binaries.

## Release validation interpreter contract

Repository source metadata is authoritative. The release-metadata check first
requires `pyproject.toml`, `src/osw/__init__.py`, and the QA helper target to
agree on the exact package version. Its default command reports the driver
interpreter and validates source, license, and tag metadata without treating
whatever distribution happens to be installed in that driver as repository
evidence.

Complete unit, GUI, changed-test, and optional-dependency validation continues
to use the explicitly prepared complete-test interpreter. Installed repository
metadata is a separate check and requires both
`--installed-metadata-python <absolute-python>` and
`--installed-metadata-root <absolute-repository-root>`. The checker logs both
roles and invokes only the named metadata interpreter, without a shell,
automatic `.venv` discovery, PATH fallback, or dependency installation.

The selected metadata environment must report its executable, Python version,
`open-solver-workbench` distribution version, imported `osw.__version__`,
imported `osw.__file__`, and editable `direct_url.json`. The selected root's
source metadata, distribution metadata, and imported package must agree with
the source-under-test version. A missing or stale distribution, invalid
observation, differently rooted import or direct URL, or version mismatch is a
hard failure. In particular, `0.1.2` is not equivalent to `0.1.5rc1`.

Selecting a metadata interpreter never substitutes it for the complete-test
interpreter or reduces optional-dependency coverage. Focused success is not
publication readiness; complete validation and a separately authorized
full-range readiness gate remain required.

## Historical License State Inventory

| Area | Recorded state at this gate | Release impact |
| --- | --- | --- |
| `LICENSE` | Present and replaced with the canonical GNU GPL version 3 text from a trusted local source: `D:\Program Files\Git\mingw64\share\licenses\xz\COPYING.GPLv3` (SHA-256 `3972DC9744F6499F0F9B2DBF76696F2AE7AD8AF9B23DDE66D6AF86C9DFB36986`). | Source license text is present. The "or later" grant is recorded in project metadata and release docs. |
| `pyproject.toml` license metadata | Aligned to `GPL-3.0-or-later`; package version was `0.1.3rc1` for this historical gate. | OSW-AUTO-077 published the historical `v0.1.2` source branch and tag at `c39f21372ef837f096aa0d430cced82adc6f3485`. The then-current candidate line was `0.1.3rc1` / `v0.1.3-rc1`; OSW-RELEASE-008 pushed only that tag to `origin`, and branch push / GitHub Release / artifacts remained separate gates. |
| README license statement | Dedicated License and Release Candidate Status sections link this plan, known limitations, and third-party notices. | README is aligned with the maintainer decision. |
| `docs/10_release_checklist.md` | License, pyproject metadata, README license section, release notes, and third-party notices are marked PASS when this step's checks pass. | The v0.1.2 source branch and final tag are published; artifacts, GitHub Release notes, and announcement text remain separate gates. |
| `docs/09_risk_register.md` | Tracks license metadata drift, third-party notice review, external solver redistribution, and tag-control risks. | License decision risk is lowered; redistribution and tag risks remain monitored. |
| `docs/07_decision_log.md` | Records the maintainer GPL-3.0-or-later decision and rc package/tag naming policy. | Future release prompts have an auditable decision record. |
| Plugin manifest expectations | `docs/03_plugin_contract.md` and `src/osw/plugins/manifest.py` require a manifest `license` field. Built-in solver/property plugin manifests currently use `GPL-3.0-or-later`. | Plugin metadata must stay explicit. Third-party plugin packages remain responsible for their own license terms. |
| Optional dependency assumptions | Installation docs treat CalculiX, OpenFOAM, Gmsh, GNU Octave, Cantera, and CoolProp as optional external tools or optional Python dependencies. | v0.1 release artifacts must not bundle external solver binaries unless license compatibility and redistribution obligations are explicitly reviewed. |
| Git tag state | Local `v0.1.0-rc1` exists as OSW-AUTO-043 historical evidence and points to `29c5c8bec8df30c7f7be72fc9be5e5409794968e`. Local `v0.1.0-rc2` exists as OSW-AUTO-045/046 historical evidence and points to `684dc6138d4257564bbcdd176a9d5ed311a7316d`. Local `v0.1.0-rc3` exists as OSW-AUTO-049 historical evidence and points to `dc7df75c53f0a4acb0a1ccf33d97c01ffdde4b16`. Local `v0.1.0` exists as OSW-AUTO-054 historical evidence and points to `da8728adf679314442755ed781c1dd57d1c6ed27`. Local `v0.1.1-rc1` exists as OSW-AUTO-060 patch RC evidence and points to `da1a2c9e2d27674dc4bb85a2800138170c4c4dec`. Local `v0.1.1` exists as OSW-AUTO-063 historical final evidence and points to `7b232f5003fcc8eb207846570499ffb3442d3197`. Local `v0.1.2-rc1` exists as OSW-AUTO-070 patch RC evidence and points to `28b30c1f79d4c62d160629e96fc1fcefa2382ebe`. Published `v0.1.2` points to `c39f21372ef837f096aa0d430cced82adc6f3485`. Local and remote `v0.1.3-rc1` existed as the then-current release-candidate tag and peel to `a6e8d3a8211e02359841d10e1947e16ab847b132`. | Existing rc and final tags must not be moved, recreated, retargeted, overwritten, deleted, force-updated, or reused as current. OSW-AUTO-077 published only `develop` and `v0.1.2`; OSW-RELEASE-008 pushed only `v0.1.3-rc1`. |

## Maintainer Decision Recorded

The maintainer selected `GPL-3.0-or-later` for the OpenSolver Workbench v0.1
repository source license on 2026-05-14. The `LICENSE` file contains the
canonical GNU GPL version 3 license text, while the "or later" grant is recorded
through `pyproject.toml`, README wording, this plan, the decision log, and the
release checklist.

Before any artifact, installer, or announcement gate, maintainers must still
review third-party notices, confirm that no external solver binaries are bundled
by default, rerun the requested release QA, and use a dedicated prompt for that
scope.

This document is planning guidance for maintainers. It is not legal advice.

## Selected Default For v0.1

The selected default for v0.1 is a GPL-compatible open-source path:
`GPL-3.0-or-later`. This fits OSW's optional integration surface with
GPL-family solver and workflow ecosystems and aligns with built-in plugin
manifest metadata.

Separate these layers:

- Repository source license: the license that governs OSW source code,
  documentation, tests, examples, and bundled project files.
- Optional Python dependencies: packages installed by users through extras such
  as `gui`, `mesh`, `viz`, `thermo`, `chm`, and `mscript`.
- Optional external runtime tools: separately installed tools such as CalculiX,
  OpenFOAM, Gmsh, GNU Octave, and SU2.
- Plugin packages: local or third-party add-ins that must declare their own
  license and dependency expectations in manifests.

Choosing a GPL-compatible repository license does not mean OSW bundles or
redistributes every optional runtime. The v0.1 source release should keep those
tools optional and documented unless redistribution duties are explicitly
reviewed.

## License Decision Options

| Option | Description | v0.1 fit | Notes |
| --- | --- | --- | --- |
| Option 1: GPL-3.0-only | License OSW source under GPL version 3 only. | Viable if maintainers want a fixed GPL version. | Less flexible for future compatibility than an "or later" license. |
| Option 2: GPL-3.0-or-later | License OSW source under GPL version 3 or any later GPL version. | Selected for v0.1. | Aligns with maintainer decision and built-in plugin manifest metadata. |
| Option 3: split/dual model | Use different licenses for different parts, or offer a dual-license model. | Future consideration, not the v0.1 default. | Requires a sharper contribution and ownership policy before it is safe to adopt. |

Do not change this selected license in a future prompt without another explicit
maintainer decision.

## Distribution Policy

- Do not bundle external solver binaries in v0.1 release artifacts unless
  maintainers explicitly review license compatibility, redistribution
  obligations, notices, source-offer duties, and platform packaging risks.
- Treat CalculiX, OpenFOAM, Gmsh, GNU Octave, and SU2 as optional external
  runtime tools installed by users according to platform-specific instructions.
- Treat Cantera and CoolProp as optional Python dependencies installed by users
  through optional extras or environment files.
- Keep base OSW install, CLI smoke, and unit tests free of mandatory heavy
  optional stacks.
- Plugin manifests must document license and dependency expectations. Manifest
  validation must not execute plugin code or import heavy dependencies.
- Curated examples and test fixtures may remain in the repository only when
  their source and license status are understood and they are not uncontrolled
  solver runtime outputs.

## Required Maintainer Checklist

Before a public v0.1 release:

- [x] Final license selected by maintainers: `GPL-3.0-or-later`.
- [x] `LICENSE` file replaced with the full GNU GPL version 3 license text.
- [x] `pyproject.toml` license metadata aligned with the selected license.
- [x] README license section aligned with the selected license.
- [x] `docs/10_release_checklist.md` updated for release metadata readiness.
- [x] Third-party notices draft created for source-distribution review.
- [x] Built-in plugin manifest license fields reviewed for consistency.
- [x] Release notes or `CHANGELOG.md` updated with the selected release version.
- [x] Local `v0.1.0` tag gate completed as local evidence before
  source-install UAT blockers were fixed.
- [x] Patch release candidate metadata/tag gate completed for local
  `v0.1.1-rc1`.
- [x] Local final `v0.1.1` tag created and parked as local-only evidence.
- [x] Next patch release candidate metadata prepared for `0.1.2rc1`.
- [x] Local `v0.1.2-rc1` tag created after OSW-AUTO-070 post-merge,
  source-install, and compact GUI workflow checks passed.
- [x] Final package metadata prepared for `0.1.2`.
- [x] Local `v0.1.2` final tag created after OSW-AUTO-073 final local tag gate
  passed.
- [x] Remote `develop` and annotated `v0.1.2` published by OSW-AUTO-077.
- [x] Next current release candidate line selected and metadata aligned as
  `0.1.3rc1` / `v0.1.3-rc1`.
- [x] Local annotated `v0.1.3-rc1` tag created by OSW-RELEASE-005 and pushed
  tag-only by OSW-RELEASE-008.
- [ ] GitHub Release page, source/wheel artifacts, installers, and public
  announcement text remain separate gates.

## Version Scheme

Use PEP 440 compatible Python/package versions.

Recommended package versions:

| Release stage | Package version | Notes |
| --- | --- | --- |
| Previous development placeholder | `0.1.0a0` | Superseded by the release-candidate metadata update. |
| Historical release candidate | `0.1.0rc1` | Local-only rc1 evidence from OSW-AUTO-043. It is not current after OSW-AUTO-044A. |
| Historical release candidate | `0.1.0rc2` | Local-only rc2 evidence from OSW-AUTO-045/046. It is not current after OSW-AUTO-047/048. |
| Historical release candidate | `0.1.0rc3` | Local-only rc3 evidence from OSW-AUTO-049/052. It is not current after final metadata prep advances `develop`. |
| Historical local final evidence | `0.1.0` | Local `v0.1.0` evidence from OSW-AUTO-054. It is not publishable as current after OSW-AUTO-057 advanced `develop` with source-run fixes. |
| Historical patch release candidate | `0.1.1rc1` | Local `v0.1.1-rc1` evidence from OSW-AUTO-060. It remains preserved after the docs-only OSW-AUTO-061A cleanup and final metadata prep. |
| Historical local patch final evidence | `0.1.1` | Prepared by OSW-AUTO-062 and locally tagged by OSW-AUTO-063. It must remain local-only historical evidence after OSW-AUTO-067 advanced `develop` with GUI workflow glue. |
| Historical patch release candidate | `0.1.2rc1` | Prepared and locally tagged by OSW-AUTO-070 after OSW-AUTO-068 verified the GUI workflow fix with no P0/P1 blockers. |
| Historical GitHub source release | `0.1.2` | Prepared by OSW-AUTO-072 after OSW-AUTO-071 found no RC1 P0/P1 blockers, locally tagged by OSW-AUTO-073, and published to GitHub by OSW-AUTO-077. |
| Historical patch release candidate metadata | `0.1.3rc1` | Prepared by OSW-RELEASE-003 as the then-current candidate metadata line, locally tagged by OSW-RELEASE-005, and pushed tag-only by OSW-RELEASE-008. |

Recommended Git tag names:

| Release stage | Git tag |
| --- | --- |
| Historical release candidate | `v0.1.0-rc1` |
| Historical release candidate | `v0.1.0-rc2` |
| Historical release candidate | `v0.1.0-rc3` |
| Historical local final evidence | `v0.1.0` |
| Historical patch release candidate | `v0.1.1-rc1` |
| Historical local patch final evidence | `v0.1.1` |
| Historical patch release candidate | `v0.1.2-rc1` |
| Historical published patch final | `v0.1.2` |
| Historical pushed patch release candidate | `v0.1.3-rc1` |

The package version and Git tag do not have to use identical syntax. Package
metadata should follow PEP 440; Git tags may use the common `v` prefix and a
hyphenated release-candidate suffix.

## Tag Policy

- No tag is created in OSW-AUTO-041 or OSW-AUTO-042.
- Local `v0.1.0-rc1` remains historical evidence and must not be moved,
  retargeted, or pushed as the current RC after OSW-AUTO-044A/045.
- Local `v0.1.0-rc2` remains historical local-only evidence after
  OSW-AUTO-047/048 and must not be pushed as the current RC.
- Local `v0.1.0-rc3` remains historical evidence after OSW-AUTO-052 local UAT
  and OSW-AUTO-053 final metadata prep.
- Local `v0.1.0` remains historical local evidence after OSW-AUTO-056 found
  source-install blockers and OSW-AUTO-057 advanced `develop`; it must not be
  moved, retargeted, deleted, recreated, overwritten, or published as current.
- The patch release-candidate path is `v0.1.1-rc1` followed by `v0.1.1`;
  OSW-AUTO-060 created local annotated `v0.1.1-rc1` only after merge,
  post-merge QA, source-install validation, and tag preservation checks passed.
- OSW-AUTO-062 prepares final package metadata as `0.1.1` after the maintainer
  accepted the docs-only post-RC delta from OSW-AUTO-061A.
- Local final `v0.1.1` exists at
  `7b232f5003fcc8eb207846570499ffb3442d3197` as historical local-only
  evidence. It must not be moved, retargeted, deleted, recreated, overwritten,
  pushed, or published as current after OSW-AUTO-067 advanced `develop`.
- The selected next patch path is `v0.1.2-rc1` followed by `v0.1.2`;
  OSW-AUTO-070 prepared package metadata `0.1.2rc1` and local annotated
  `v0.1.2-rc1`, and OSW-AUTO-072 prepares final package metadata `0.1.2`.
  OSW-AUTO-073 created local annotated `v0.1.2`, and OSW-AUTO-077 published
  `develop` plus `v0.1.2` to GitHub.
- At this tag-only gate, the patch release-candidate line was `v0.1.3-rc1`.
  OSW-RELEASE-003
  prepared package metadata as `0.1.3rc1`, OSW-RELEASE-005 created the
  annotated local tag, OSW-RELEASE-008 pushed only that tag to `origin`, and
  OSW-RELEASE-009 verified the remote tag target.
- Tag creation is allowed only after release checklist P1 blockers are cleared
  by a dedicated release/tag gate.
- Tag creation should happen in a dedicated release/tag prompt.
- Do not push tags unless a maintainer explicitly instructs that exact action.
- OSW-AUTO-077 was the explicit maintainer-approved exception for pushing only
  `refs/tags/v0.1.2:refs/tags/v0.1.2`; historical and RC tags remained
  unpushed by that prompt.
- Prefer annotated tags for release candidates and final v0.1 tags.

## Release Branch And Tag Procedure Draft

Use this draft in a future release/tag prompt after release metadata approval:

1. Verify `develop` is clean and the release checklist has no P1 blockers.
2. Decide whether the release candidate is `0.1.3rc1` after historical
   `v0.1.0`, `v0.1.1`, and `v0.1.2` tags are preserved unchanged.
3. Update `CHANGELOG.md` or release notes.
4. Update package version metadata.
5. Verify `LICENSE`, README license text, and third-party notices.
6. Run final QA:
   - `python tools/qa/run_pre_merge_qa.py`
   - `pytest -q --import-mode=importlib`
   - `pytest tests/integration -q -m "not external_solver"`
   - `pytest tests/golden -q`
   - `pytest tests/validation -q`
   - `python tools/qa/check_scope_drift.py`
   - `python tools/qa/check_no_solver_artifacts_committed.py`
7. Build source distribution and wheel only if packaging metadata is ready.
8. Create an annotated local tag, for example:

   ```powershell
   git tag -a v0.1.3-rc1 -m "OpenSolver Workbench v0.1.3-rc1 internal release candidate"
   ```

9. Verify the tag locally with `git show v0.1.3-rc1`.
10. Do not push unless explicitly instructed by a maintainer.

## Local Rollback Plan For A Later Tag Prompt

If a later prompt creates a local tag and the release is rejected before any
push, delete only the local tag:

```powershell
git tag -d v0.1.3-rc1
```

If a tag was already pushed, stop and ask for maintainer direction. Do not delete
or rewrite remote tags from an autopilot prompt unless the maintainer explicitly
requests that exact operation.

## Release Artifact Policy

- Source distribution and wheel are acceptable release artifacts when package
  metadata, license, notices, and QA are ready.
- Do not bundle external solver binaries by default.
- Do not include generated solver runtime directories, logs, large generated
  reports, or temporary case outputs.
- Optional dependency install guidance remains documentation-only.
- If a future standalone desktop package is attempted, it must go through a
  separate packaging review and dependency redistribution review.

## OSW-AUTO-042 Outcome

The maintainer license decision is recorded as `GPL-3.0-or-later`, the
repository license text and metadata are aligned for `0.1.0rc1`, release notes
exist, and a third-party notices draft exists for source-distribution review.
No release tag is created in this prompt. Public tag creation and public
announcement remain blocked until the dedicated release/tag gate passes.

## OSW-AUTO-045 RC2 Plan

OSW-AUTO-045 updates package metadata to `0.1.0rc2` and may create a local
annotated `v0.1.0-rc2` tag only after merge and post-merge pre-tag QA pass.
Existing local `v0.1.0-rc1` remains historical local-only evidence and must not
be pushed as the current RC. Final `v0.1.0`, tag pushes, release artifacts, and
public announcements remain blocked until separate maintainer-controlled gates.

## OSW-AUTO-049 RC3 Plan

OSW-AUTO-049 updates package metadata to `0.1.0rc3` after OSW-AUTO-047 fixed
default pytest collection and OSW-AUTO-048 added local-only docs link checking.
Existing local `v0.1.0-rc1` and `v0.1.0-rc2` remain annotated historical
local-only evidence and must not be moved, recreated, retargeted, overwritten,
or pushed as the current RC. A local annotated `v0.1.0-rc3` tag may be created
only after merge, post-merge pre-tag QA, prior-RC verification, release
metadata checks, docs link checking, duplicate-basename checking, and default
`pytest -q` pass. Final `v0.1.0`, tag pushes, release artifacts, remote push
logic, and public announcements remain blocked until separate
maintainer-controlled gates.

## OSW-AUTO-053 Final Metadata Prep

OSW-AUTO-053 updates package metadata to final version `0.1.0` after
OSW-AUTO-052 local RC3 UAT passed with no P0/P1 blockers. Local annotated
`v0.1.0-rc1`, `v0.1.0-rc2`, and `v0.1.0-rc3` remain historical local evidence
and must not be moved, recreated, retargeted, overwritten, or pushed by this
final-prep step. At that step, final `v0.1.0` remained absent and was deferred
to OSW-AUTO-054; OSW-AUTO-054 later created it as local annotated evidence.
After OSW-AUTO-057 advanced `develop`, that tag remains historical local-only
evidence. Public tag pushes, release artifacts, bundled external solver
binaries, and public announcements remain blocked until separate
maintainer-controlled gates.

## OSW-AUTO-059 Patch Release Recovery Plan

OSW-AUTO-054 created local annotated `v0.1.0` before OSW-AUTO-056 discovered
source-install UAT blockers in a fresh isolated environment. OSW-AUTO-057 fixed
those blockers on `develop` at
`50e606b869e7a9a9c2e0275c32470c4d011a94a1`, and OSW-AUTO-058 verified a fresh
source-install retest with ruff, default pytest, importlib pytest,
fast/pre-merge QA, docs link checking, duplicate basename checking, and GUI
offscreen launch passing with no P0/P1 blockers.

The existing `v0.1.0` tag remains local-only historical evidence at
`da8728adf679314442755ed781c1dd57d1c6ed27`; it must not be moved, deleted,
retargeted, recreated, overwritten, or pushed as the current release. Because
current `develop` is ahead of `v0.1.0`, the selected recovery path is a patch
release:

- next release-candidate package version: `0.1.1rc1`
- next release-candidate tag: `v0.1.1-rc1`
- next final package version: `0.1.1`
- next final tag: `v0.1.1`

OSW-AUTO-059 records only this decision. It does not change package version,
create tags, push, build release artifacts, or publish announcements.

## OSW-AUTO-060 Patch v0.1.1 RC1 Candidate

OSW-AUTO-060 prepared patch release-candidate metadata as package version
`0.1.1rc1` and created local annotated tag `v0.1.1-rc1` at
`da1a2c9e2d27674dc4bb85a2800138170c4c4dec`. The historical
`v0.1.0` tag remains local-only evidence at
`da8728adf679314442755ed781c1dd57d1c6ed27` and must not be moved, deleted,
retargeted, recreated, overwritten, pushed, or published as current.

The `v0.1.1-rc1` tag was created only after merge to `develop`, post-merge QA,
fresh isolated source-install validation, and release metadata checks passed.
Final `v0.1.1`, public tag pushes, release artifacts, external solver binary
bundles, and public announcements remain blocked until separate
maintainer-controlled gates.

## OSW-AUTO-061A Patch RC1 Readiness Documentation Fix

OSW-AUTO-061 verified the local `v0.1.1-rc1` tag, package version
`0.1.1rc1`, release metadata, ruff, default/importlib pytest, fast QA,
pre-merge QA, and source-install evidence, then found stale checklist wording
that still described the completed patch RC1 local tag gate as pending.

OSW-AUTO-061A corrects that readiness wording only. It creates no tag, moves no
tag, changes no package version, and does not push. After this docs-only merge,
`develop` may be ahead of `v0.1.1-rc1`; final prep may proceed from docs-clean
`develop` only if the maintainer accepts the post-RC documentation delta. If
exact final-from-current-RC identity is required, a later dedicated
`v0.1.1-rc2` gate should create the next release-candidate tag for that
historical line.

## OSW-AUTO-062 Patch v0.1.1 Final Metadata Prep

The maintainer accepted the OSW-AUTO-061A docs-only post-RC delta for final
prep. OSW-AUTO-062 prepares final package metadata as `0.1.1` and keeps
historical local evidence unchanged:

- historical `v0.1.0` remains at `da8728adf679314442755ed781c1dd57d1c6ed27`
  and must not be moved, retargeted, pushed, or published as current;
- local `v0.1.1-rc1` remains at
  `da1a2c9e2d27674dc4bb85a2800138170c4c4dec` and must not be moved,
  retargeted, pushed, or published as current;
- final `v0.1.1` tag creation is deferred to
  OSW-AUTO-063_PATCH_V0_1_1_FINAL_LOCAL_TAG_GATE.

This prompt creates no final tag, no RC tag, no release artifact, no public
announcement, and no push.

## OSW-AUTO-069 Release Version Recovery After GUI Workflow Fix

OSW-AUTO-063 created local annotated final `v0.1.1` at
`7b232f5003fcc8eb207846570499ffb3442d3197`, and OSW-AUTO-064 parked it with no
remote publication. OSW-AUTO-067 then improved GUI-native workflow glue on
`develop` at `a12812dab77e1d968223a30859a8fa91e2ef0e1d`, so current `develop`
is ahead of the local `v0.1.1` tag.

OSW-AUTO-068 retested the GUI workflow and returned `PASS_WITH_LIMITATIONS`
with no P0/P1 blockers. The retest showed GUI import/project tree/properties,
Run/Generate prepare or diagnostic state, Table/Plot/Result state, and report
export now align much more strongly with the original development goal. Optional
external solver live runs, manual Computer Use depth, Cantera deprecation
warning cleanup, and packaging smoke remain P2 follow-ups.

The selected safe recovery path is:

- next release-candidate package version: `0.1.2rc1`
- next release-candidate tag: `v0.1.2-rc1`
- next final package version: `0.1.2`
- next final tag: `v0.1.2`

OSW-AUTO-069 records this decision only. It creates no tag, changes no package
version, and performs no push. The existing `v0.1.1` tag must remain historical
local-only final evidence and must not be published as current.

## OSW-AUTO-070 Patch v0.1.2 RC1 Candidate

OSW-AUTO-070 prepared the next patch release-candidate metadata as package
version `0.1.2rc1` after the GUI workflow recovery path selected in
OSW-AUTO-069. The local RC tag is `v0.1.2-rc1`; final `0.1.2` / `v0.1.2`
was completed later as local historical evidence.

The gate preserves historical local evidence unchanged:

- `v0.1.0-rc1`, `v0.1.0-rc2`, and `v0.1.0-rc3` remain historical RC evidence;
- `v0.1.0` remains historical local final evidence at
  `da8728adf679314442755ed781c1dd57d1c6ed27`;
- `v0.1.1-rc1` remains historical patch RC evidence at
  `da1a2c9e2d27674dc4bb85a2800138170c4c4dec`;
- `v0.1.1` remains historical local final evidence at
  `7b232f5003fcc8eb207846570499ffb3442d3197` and must not be published as
  current after OSW-AUTO-067 advanced `develop`.

Local annotated `v0.1.2-rc1` was created only after merge to `develop`,
post-merge QA, fresh isolated source-install validation, compact GUI workflow
validation, release metadata checks, and final `v0.1.2` absence verification
passed. This gate created no final tag, pushed no branch or tag, built no
release artifacts, and made no public announcement.

## OSW-AUTO-072 Patch v0.1.2 Final Metadata

OSW-AUTO-072 prepared final package metadata as version `0.1.2` after
OSW-AUTO-071 triaged local `v0.1.2-rc1` feedback as `NO_FEEDBACK_REPORTED` with
no P0/P1 blockers. A later local final tag gate created annotated `v0.1.2` at
`c39f21372ef837f096aa0d430cced82adc6f3485` with no push.

The final-prep gate preserves historical local evidence unchanged:

- `v0.1.0-rc1`, `v0.1.0-rc2`, and `v0.1.0-rc3` remain historical RC evidence;
- `v0.1.0` remains historical local final evidence at
  `da8728adf679314442755ed781c1dd57d1c6ed27`;
- `v0.1.1-rc1` remains historical patch RC evidence at
  `da1a2c9e2d27674dc4bb85a2800138170c4c4dec`;
- `v0.1.1` remains historical local final evidence at
  `7b232f5003fcc8eb207846570499ffb3442d3197` and must not be published as
  current after OSW-AUTO-067 advanced `develop`;
- `v0.1.2-rc1` remains local RC evidence at
  `28b30c1f79d4c62d160629e96fc1fcefa2382ebe`;
- `v0.1.2` remains published final source-release evidence at
  `c39f21372ef837f096aa0d430cced82adc6f3485`.

## OSW-AUTO-077 Patch v0.1.2 GitHub Source Publish

OSW-AUTO-073 created local annotated `v0.1.2` at
`c39f21372ef837f096aa0d430cced82adc6f3485`. OSW-AUTO-077 then published the
source release from a clean publish clone after OSW-AUTO-075 source smoke and
OSW-AUTO-076E remote readiness checks passed.

The publish gate pushed only:

- `refs/heads/develop:refs/heads/develop`
- `refs/tags/v0.1.2:refs/tags/v0.1.2`

Remote `develop` and remote `v0.1.2^{}` both resolve to
`c39f21372ef837f096aa0d430cced82adc6f3485`; the remote annotated tag object
verified by OSW-AUTO-077 is `353a87897c842ee01aaae18abc4d69f330406e09`.
Historical `v0.1.0`, `v0.1.1`, and `v0.1.2-rc1` tags were not pushed by that
prompt. Release artifacts, GitHub Release notes, binary installers, external
solver binary bundles, and public announcements remain separate
maintainer-controlled gates.

## OSW-RELEASE-002 Release Line Reconciliation

OSW-RELEASE-002 reconciled the current checkout after the internal freeze and
handoff commit `f42131845bee49a89ef40a8d21c0c146846ada25`. At that point, the
source metadata was still `0.1.2`, but published `v0.1.2` already pointed to
`c39f21372ef837f096aa0d430cced82adc6f3485`; therefore `v0.1.2` must not be
moved or reused for the current `develop` line.

At that point, if maintainers needed a release candidate after `f421318`, the
recommended historical path was a new patch candidate:

- next release-candidate package version: `0.1.3rc1`
- next release-candidate tag: `v0.1.3-rc1`

OSW-RELEASE-002 creates no tag, performs no push, and changes no product
behavior.

## OSW-RELEASE-003 / 005 / 008 v0.1.3rc1 Tag-Only Path

OSW-RELEASE-003 aligns the current source metadata to `0.1.3rc1` and records
`v0.1.3-rc1` as the patch release-candidate tag name. OSW-RELEASE-005 creates
the annotated local tag, OSW-RELEASE-008 pushes only that tag to `origin`, and
OSW-RELEASE-009 verifies that the remote tag peels to
`a6e8d3a8211e02359841d10e1947e16ab847b132`.

This tag-only path performs no branch push, all-tags push, force push, GitHub
Release creation, package artifact build, binary installer publication, public
announcement, or product behavior change. The existing `v0.1.2` source-release
tag and then-current `v0.1.3-rc1` candidate tag must not be moved, reused,
deleted, retargeted, recreated, or force-updated.
