# v0.1.3rc2 maintenance issue closure triage

Date: 2026-06-05

Repo HEAD reviewed: `431dbb80939dc516ecd7c360b44312925818073b`

Public release: `v0.1.3-rc1`

Active development version: `0.1.3rc2.dev0`

This triage reviews only completed v0.1.3rc2 maintenance issues. It does not
edit the GitHub Release, upload assets, create tags, retarget tags, publish a
stable release, or change product behavior.

## Candidate Issues

- #1 Clean remaining local duplicate-file hygiene records
- #2 Automate release asset download smoke
- #4 Review Windows portable ZIP user experience
- #5 Prepare v0.1.3rc2 maintenance revalidation gate

## Evidence Table

| Issue | Title | Evidence checked | Decision | Reason |
| --- | --- | --- | --- | --- |
| #1 | Clean remaining local duplicate-file hygiene records | `docs/maintenance/duplicate_file_quarantine_review.md`, OSW-MAINT-007 report, duplicate-path scan, release gate, archive manifest | Close | OSW-MAINT-002 quarantined 19 duplicate files; OSW-MAINT-007 reviewed the archive; no files were restored or permanently deleted; no high-risk secrets were found; duplicate desktop-file patterns are absent from source/test/docs/examples/tools/workflow paths. |
| #2 | Automate release asset download smoke | `tools/release/check_release_assets.py`, `tools/qa/check_release_asset_smoke.py`, `tests/unit/test_release_asset_smoke.py`, `release-asset-smoke.yml`, OSW-MAINT-003/004B/006A/006R reports, workflow runs `26957576562` and `26979859278` | Close | Release asset smoke automation now covers checksum and manifest verification, offline fixtures, GitHub download mode, CI/manual workflow wiring, CI fixture stabilization, and successful push and workflow_dispatch evidence. |
| #4 | Review Windows portable ZIP user experience | `docs/release/windows_portable_zip.md`, `tools/release/templates/README_RUN_FIRST.txt`, portable UX checks in `tools/release/check_release_assets.py`, tests in `tests/unit/test_release_asset_smoke.py`, OSW-MAINT-004 report | Close | Portable ZIP docs and future build template now document unsigned/no MSI/no code-signing/no bundled solver caveats, checksum guidance, first-run expectations, and portable UX smoke warnings. |
| #5 | Prepare v0.1.3rc2 maintenance revalidation gate | `docs/maintenance/v0_1_3rc2_revalidation.md`, OSW-MAINT-005 report, `release-asset-smoke.yml`, OSW-MAINT-006R report, workflow run `26979859278` | Close | The maintenance revalidation baseline is documented, release and workflow safety boundaries are recorded, and the workflow_dispatch retry passed after the fixture fix. |

## Closure Policy

- Close only issues with local and GitHub evidence.
- Use `--reason completed`.
- Leave unrelated issues open.
- Do not mutate the GitHub Release, release assets, tags, or branch history as
  part of issue closure.

## Known Warnings

- `v0.1.3-rc1` remains a prerelease.
- The Windows portable ZIP is unsigned.
- No MSI installer is provided.
- No code signing is claimed.
- External solvers are not bundled.
- Optional dependency validation remains environment-specific.
- Public docs on `develop` are newer than the tagged `v0.1.3-rc1` source.

## Next Maintenance Choices

- Run optional full-smoke workflow evidence if maintainers want deeper wheel,
  sdist, and portable executable validation.
- Continue live optional solver validation on machines that intentionally have
  those tools installed.
- Select later `v0.1.4` feature planning only after maintenance choices are
  closed or explicitly deferred.
