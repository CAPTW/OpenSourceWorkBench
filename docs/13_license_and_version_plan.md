# License And Version Plan

Status: release-planning packet, not a final license decision

This document resolves the v0.1 license and tag planning blockers as far as a
documentation prompt can. It does not finalize the project license, provide
legal advice, create a Git tag, announce a public release, or approve
redistribution of third-party solver binaries.

## Current License State Inventory

| Area | Current state | Release impact |
| --- | --- | --- |
| `LICENSE` | Present, but it is a placeholder. It recommends GPL-3.0-or-later unless maintainers decide otherwise and says it is not the final license grant. | Public release remains blocked until maintainers replace it with the full selected license text. |
| `pyproject.toml` license metadata | Present, but provisional: `GPL-3.0-or-later recommended; final license pending project decision`. | Metadata must be aligned with the final license before a public release tag. |
| README license statement | No dedicated license section yet. README links known limitations and release readiness docs, but not this plan before OSW-AUTO-041. | Add a link to this plan; add a final license section only after maintainer approval. |
| `docs/10_release_checklist.md` | License remains a P1 release blocker. Version/tag planning was also blocked before this packet. | Keep final license as P1. Mark version/tag plan ready after this document lands. |
| `docs/09_risk_register.md` | Tracks pending license decision, broad pytest collection, and missing docs link checker risks. | Add explicit version/tag and third-party notice review risks. |
| `docs/07_decision_log.md` | No license-specific ADR exists before this step. | Add a process ADR for license/tag planning without selecting the license. |
| Plugin manifest expectations | `docs/03_plugin_contract.md` and `src/osw/plugins/manifest.py` require a manifest `license` field. Built-in solver/property plugin manifests currently use `GPL-3.0-or-later`. | Plugin metadata must stay explicit. Third-party plugin packages remain responsible for their own license terms. |
| Optional dependency assumptions | Installation docs treat CalculiX, OpenFOAM, Gmsh, GNU Octave, Cantera, and CoolProp as optional external tools or optional Python dependencies. | v0.1 release artifacts must not bundle external solver binaries unless license compatibility and redistribution obligations are explicitly reviewed. |
| Git tag state | `git tag --list "v0.1*"` returned no local v0.1 tags. | No release tag exists. Tag creation is deferred to a dedicated release/tag prompt. |

## Maintainer Decision Required

Final public release license selection is a maintainer decision. The repository
currently contains a recommended direction, not an approved final license grant.

Before a public v0.1 release or tag, maintainers must choose the license,
replace the placeholder `LICENSE`, align package metadata, update README release
text, review third-party notices, and rerun the release checklist.

This document is planning guidance for maintainers. It is not legal advice.

## Recommended Default For v0.1

The recommended default for v0.1 is a GPL-compatible open-source path, with
`GPL-3.0-or-later` as the practical default candidate, because OSW integrates
with or may integrate with GPL-family solver and workflow ecosystems and the
built-in plugin manifests already use that identifier.

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
| Option 2: GPL-3.0-or-later | License OSW source under GPL version 3 or any later GPL version. | Recommended default candidate for v0.1. | Aligns with current placeholder text and built-in plugin manifest metadata, pending maintainer approval. |
| Option 3: split/dual model | Use different licenses for different parts, or offer a dual-license model. | Future consideration, not the v0.1 default. | Requires a sharper contribution and ownership policy before it is safe to adopt. |

Do not update `LICENSE` or `pyproject.toml` to a final license value until the
maintainer decision is recorded.

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

- [ ] Final license selected by maintainers.
- [ ] `LICENSE` file replaced with the full chosen license text.
- [ ] `pyproject.toml` license metadata aligned with the selected license.
- [ ] README license section aligned with the selected license.
- [ ] `docs/10_release_checklist.md` updated from P1 blocker to release-ready
      status for license.
- [ ] Third-party notices and optional dependency redistribution assumptions
      reviewed.
- [ ] Built-in plugin manifest license fields reviewed for consistency.
- [ ] Release notes or `CHANGELOG.md` updated with the selected release version.

## Version Scheme

Use PEP 440 compatible Python/package versions.

Recommended package versions:

| Release stage | Package version | Notes |
| --- | --- | --- |
| Current development placeholder | `0.1.0a0` | Current package metadata. |
| Release candidate | `0.1.0rc1` | Recommended package version if maintainers want a v0.1 candidate. |
| Final v0.1 | `0.1.0` | Recommended package version for final v0.1 release. |

Recommended Git tag names:

| Release stage | Git tag |
| --- | --- |
| Release candidate | `v0.1.0-rc1` |
| Final v0.1 | `v0.1.0` |

The package version and Git tag do not have to use identical syntax. Package
metadata should follow PEP 440; Git tags may use the common `v` prefix and a
hyphenated release-candidate suffix.

## Tag Policy

- No tag is created in OSW-AUTO-041.
- Tag creation is allowed only after release checklist P1 blockers are cleared.
- Tag creation should happen in a dedicated release/tag prompt.
- Do not push tags unless a maintainer explicitly instructs that exact action.
- Prefer annotated tags for release candidates and final v0.1 tags.

## Release Branch And Tag Procedure Draft

Use this draft in a future release/tag prompt after license approval:

1. Verify `develop` is clean and the release checklist has no P1 blockers.
2. Decide whether the release is `0.1.0rc1` or `0.1.0`.
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
   git tag -a v0.1.0-rc1 -m "OpenSolver Workbench v0.1.0 release candidate 1"
   ```

9. Verify the tag locally with `git show v0.1.0-rc1`.
10. Do not push unless explicitly instructed by a maintainer.

## Local Rollback Plan For A Later Tag Prompt

If a later prompt creates a local tag and the release is rejected before any
push, delete only the local tag:

```powershell
git tag -d v0.1.0-rc1
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

## OSW-AUTO-041 Outcome

This plan clears the version/tag planning blocker by documenting a coherent
candidate/final version scheme, tag policy, release procedure, rollback plan,
and artifact policy. It does not clear the final license blocker. Public tag
creation and public announcement remain blocked until maintainers finalize the
license and align metadata.
