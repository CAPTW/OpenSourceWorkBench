# v0.1.3rc2 maintenance revalidation

This page records the maintenance baseline after the public `v0.1.3-rc1`
prerelease, release asset smoke automation, Windows portable ZIP UX review, and
release asset smoke CI integration.

OSW remains educational/research software. This revalidation is not an
industrial certification claim, a stable production claim, or a compatibility
claim for MATLAB, ANSYS, Simulink, native commercial CAD, or full external
solver coverage.

## Baseline

| Item | State |
| --- | --- |
| Base public release | `v0.1.3-rc1` |
| Current development version | `0.1.3rc2.dev0` |
| Current develop HEAD at revalidation start | `3f1942c1593b0ea8caaa6d9cee9551891de11231` |
| Release tag target | `a6e8d3a8211e02359841d10e1947e16ab847b132` |
| Release state | Public prerelease, not draft |
| Release assets | Wheel, sdist, Windows portable ZIP, `SHA256SUMS.txt`, and `release_asset_manifest.json` |

Develop is intentionally newer than the tagged `v0.1.3-rc1` source because the
maintenance cycle added public docs polish, release asset smoke tooling,
portable ZIP UX guidance, and CI/manual smoke wiring after the release tag.

## Maintenance Items Completed

- Duplicate-file hygiene.
- Post-public roadmap and milestones.
- GitHub labels, issues, and milestones.
- Live optional validation evidence.
- Next development cycle opened as `0.1.3rc2.dev0`.
- Release asset smoke automation.
- Windows portable ZIP UX review.
- Release asset smoke CI/manual workflow.

## Release Integrity

- `v0.1.3-rc1` remains an annotated release tag.
- The tag target remains `a6e8d3a8211e02359841d10e1947e16ab847b132`.
- The public GitHub Release remains a prerelease.
- The expected release assets remain present:
  - `open_solver_workbench-0.1.3rc1-py3-none-any.whl`
  - `open_solver_workbench-0.1.3rc1.tar.gz`
  - `OpenSolverWorkbench-v0.1.3rc1-windows-x64-portable.zip`
  - `SHA256SUMS.txt`
  - `release_asset_manifest.json`

## CI And Workflow

The `Release asset smoke` workflow provides two bounded paths:

- Offline fixture smoke runs on pull requests and `develop` pushes.
- Live GitHub Release asset download smoke is available only through manual
  `workflow_dispatch`.

Workflow safety boundaries:

- `contents: read` only.
- No release asset upload.
- No GitHub Release edit or publish.
- No branch or tag push.
- No `--clobber` asset overwrite path.
- `GH_TOKEN` is scoped to the manual live download job only.

`ALLOW_WORKFLOW_DISPATCH=false` was used for this revalidation gate, so the
manual live workflow was not triggered by this gate.

## Known Warnings

- The release remains a prerelease.
- The Windows portable ZIP is unsigned.
- There is no MSI installer.
- There is no code signing.
- External solvers are not bundled.
- Optional solver and science dependencies remain environment-specific.
- Published portable ZIP UX smoke can report warnings for older
  `README_RUN_FIRST.txt` wording.
- Public docs on `develop` are newer than the tagged release source.

## Next Choices

- Review Issue `#1` for remaining duplicate-file hygiene records.
- Use Issue `#5` as the maintainer review point for this revalidation baseline.
- Manually trigger the `Release asset smoke` `workflow_dispatch` check from the
  GitHub Actions UI if live CI evidence is desired.
- Select the next `v0.1.3rc2` maintenance issue before moving to broader
  `v0.1.4` feature selection.

## Scope Guardrails

- OSW is an educational/research Engineering Solver & Script Workbench.
- OSW is not industrial-certified.
- OSW is not a MATLAB, ANSYS, or Simulink clone.
- OSW does not support native commercial CAD direct import.
- Optional external solvers and science stacks are user-provided unless a later
  release explicitly documents otherwise.
