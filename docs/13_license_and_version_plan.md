# License And Version Plan

Status: maintainer license decision recorded; release tag not created

This document records the v0.1 maintainer license decision, package version
scheme, tag plan, and release artifact policy. It does not provide legal
advice, create a Git tag, announce a public release, or approve redistribution
of third-party solver binaries.

## Current License State Inventory

| Area | Current state | Release impact |
| --- | --- | --- |
| `LICENSE` | Present and replaced with the canonical GNU GPL version 3 text from a trusted local source: `D:\Program Files\Git\mingw64\share\licenses\xz\COPYING.GPLv3` (SHA-256 `3972DC9744F6499F0F9B2DBF76696F2AE7AD8AF9B23DDE66D6AF86C9DFB36986`). | Source license text is present. The "or later" grant is recorded in project metadata and release docs. |
| `pyproject.toml` license metadata | Aligned to `GPL-3.0-or-later`; package version is `0.1.0`. | Final metadata is ready for the final local tag gate. |
| README license statement | Dedicated License and Release Candidate Status sections link this plan, known limitations, and third-party notices. | README is aligned with the maintainer decision. |
| `docs/10_release_checklist.md` | License, pyproject metadata, README license section, release notes, and third-party notices are marked PASS when this step's checks pass. | Public tag and announcement remain blocked until the dedicated tag/release gate. |
| `docs/09_risk_register.md` | Tracks license metadata drift, third-party notice review, external solver redistribution, and tag-control risks. | License decision risk is lowered; redistribution and tag risks remain monitored. |
| `docs/07_decision_log.md` | Records the maintainer GPL-3.0-or-later decision and rc package/tag naming policy. | Future release prompts have an auditable decision record. |
| Plugin manifest expectations | `docs/03_plugin_contract.md` and `src/osw/plugins/manifest.py` require a manifest `license` field. Built-in solver/property plugin manifests currently use `GPL-3.0-or-later`. | Plugin metadata must stay explicit. Third-party plugin packages remain responsible for their own license terms. |
| Optional dependency assumptions | Installation docs treat CalculiX, OpenFOAM, Gmsh, GNU Octave, Cantera, and CoolProp as optional external tools or optional Python dependencies. | v0.1 release artifacts must not bundle external solver binaries unless license compatibility and redistribution obligations are explicitly reviewed. |
| Git tag state | Local `v0.1.0-rc1` exists as OSW-AUTO-043 historical evidence and points to `29c5c8bec8df30c7f7be72fc9be5e5409794968e`. Local `v0.1.0-rc2` exists as OSW-AUTO-045/046 historical evidence and points to `684dc6138d4257564bbcdd176a9d5ed311a7316d`. Local `v0.1.0-rc3` exists as OSW-AUTO-049 historical evidence and points to `dc7df75c53f0a4acb0a1ccf33d97c01ffdde4b16`. Final `v0.1.0` remains absent until OSW-AUTO-054. | rc1, rc2, and rc3 must not be moved, recreated, retargeted, overwritten, or pushed by final-prep. The final tag must be created only by the dedicated final local tag gate. |

## Maintainer Decision Recorded

The maintainer selected `GPL-3.0-or-later` for the OpenSolver Workbench v0.1
repository source license on 2026-05-14. The `LICENSE` file contains the
canonical GNU GPL version 3 license text, while the "or later" grant is recorded
through `pyproject.toml`, README wording, this plan, the decision log, and the
release checklist.

Before a public v0.1 release or tag, maintainers must still review third-party
notices, confirm that no external solver binaries are bundled by default, rerun
release QA, and use a dedicated release/tag prompt.

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
- [ ] Dedicated release/tag gate completed.

## Version Scheme

Use PEP 440 compatible Python/package versions.

Recommended package versions:

| Release stage | Package version | Notes |
| --- | --- | --- |
| Previous development placeholder | `0.1.0a0` | Superseded by the release-candidate metadata update. |
| Historical release candidate | `0.1.0rc1` | Local-only rc1 evidence from OSW-AUTO-043. It is not current after OSW-AUTO-044A. |
| Historical release candidate | `0.1.0rc2` | Local-only rc2 evidence from OSW-AUTO-045/046. It is not current after OSW-AUTO-047/048. |
| Historical release candidate | `0.1.0rc3` | Local-only rc3 evidence from OSW-AUTO-049/052. It is not current after final metadata prep advances `develop`. |
| Current final metadata | `0.1.0` | Package version prepared for the final v0.1 local tag gate. |

Recommended Git tag names:

| Release stage | Git tag |
| --- | --- |
| Historical release candidate | `v0.1.0-rc1` |
| Historical release candidate | `v0.1.0-rc2` |
| Historical release candidate | `v0.1.0-rc3` |
| Pending final v0.1 | `v0.1.0` |

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
- Final `v0.1.0` may be created only by the OSW-AUTO-054 final local tag gate
  after final metadata QA passes.
- Tag creation is allowed only after release checklist P1 blockers are cleared
  by a dedicated release/tag gate.
- Tag creation should happen in a dedicated release/tag prompt.
- Do not push tags unless a maintainer explicitly instructs that exact action.
- Prefer annotated tags for release candidates and final v0.1 tags.

## Release Branch And Tag Procedure Draft

Use this draft in a future release/tag prompt after release metadata approval:

1. Verify `develop` is clean and the release checklist has no P1 blockers.
2. Decide whether the release is `0.1.0`.
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
   git tag -a v0.1.0 -m "OpenSolver Workbench v0.1.0"
   ```

9. Verify the tag locally with `git show v0.1.0`.
10. Do not push unless explicitly instructed by a maintainer.

## Local Rollback Plan For A Later Tag Prompt

If a later prompt creates a local tag and the release is rejected before any
push, delete only the local tag:

```powershell
git tag -d v0.1.0
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
final-prep step. Final `v0.1.0` remains absent and may be created only by the
OSW-AUTO-054 final local tag gate after release metadata, docs-link,
duplicate-basename, default pytest, and pre-merge QA checks pass. Public tag
pushes, release artifacts, bundled external solver binaries, and public
announcements remain blocked until separate maintainer-controlled gates.
