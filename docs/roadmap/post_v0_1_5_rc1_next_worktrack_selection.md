# Post-v0.1.5-rc1 next worktrack selection

## Status

`completed`

This planning-only gate selects the next worktrack after the completed
`v0.1.5-rc1` public prerelease flow and the public release body note update.
It does not perform the selected work.

## Current public release

- Current public release: `v0.1.5-rc1`
- URL: https://github.com/CAPTW/OpenSourceWorkBench/releases/tag/v0.1.5-rc1
- State: public prerelease, not draft
- Assets present: wheel, sdist, Windows portable ZIP, `SHA256SUMS.txt`, and
  `release_asset_manifest.json`
- Post-public audit: passed
- Release body note: corrected after OSW-RELEASE-041 to remove stale
  audit-pending wording

## Current repository

- Develop HEAD: `d141c9f4d53d8d1477a3b0ac5f7f6b28137dd6e1`
- Release tag target: `85c8144f7ff19159ab02c40adb6483ce6b13c017`
- CLI version: `osw 0.1.5rc1`
- Installed package metadata: `0.1.5rc1`
- Develop is newer than the release tag because post-release planning,
  release-body follow-up, GUI aggregate timeout/release-monitoring hardening,
  and prepared-machine optional validation discovery were follow-up work after
  the public `v0.1.5-rc1` release.

## Open validation

- `#6` live Gmsh validation remains open.
- `#7` live GNU Octave validation remains open.
- `#8` live CalculiX `ccx` validation remains open; OSW-VALID-004 was
  `skipped-missing` because `ccx` was absent.
- `#9` live OpenFOAM validation remains open.
- `#10` live CoolProp / Cantera validation remains open.
- `#11` live PyVista / meshio validation remains open.

## Known risks

- Live validation remains environment-dependent.
- The Windows portable ZIP is unsigned.
- No MSI or code signing is provided.
- External solvers are not bundled.
- GUI aggregate test commands may time out in this environment even when
  deterministic per-file fallback has passed in prior gates.
- Release monitoring should continue to watch public release notes, assets,
  checksums, and issue state after the public `v0.1.5-rc1` flow.

## Decision

Selected worktrack: `maintenance hardening for GUI aggregate timeout and release-monitoring notes`

## Rationale

Prepared-machine live optional validation is still important, but this gate has
no evidence that a prepared solver/science environment is available. Issues
`#6` through `#11` remain open, and issue `#8` is still `skipped-missing`
because `ccx` was absent.

The release flow is now complete and the public release body note has been
corrected. The next practical work is to harden recurring maintenance signals:
document and stabilize the GUI aggregate timeout/per-file fallback pattern, and
add release-monitoring notes so public assets, release body wording, and open
validation status remain easy to audit.

## Non-actions

- No release edit was performed in this planning gate.
- No asset mutation was performed.
- No issue mutation was performed.
- No solver execution was performed.
- No runtime source, GUI source, CLI source, or ProjectSchema mutation was
  performed.
- No version bump or metadata alignment was performed.
- No dependency installation or upgrade was performed.

## Next recommended gate

`OSW-MAINT-018_GUI_AGGREGATE_TIMEOUT_AND_RELEASE_MONITORING_HARDENING`

The next gate should remain maintenance-scoped: document the GUI aggregate
timeout fallback policy, add release-monitoring notes for public prerelease
checks, and avoid release mutation, issue mutation, solver execution, runtime
source changes, or dependency installation unless a later prompt explicitly
allows them.

## Maintenance follow-up

OSW-MAINT-018 implements the selected maintenance hardening path with docs,
focused tests, and a pytest-only GUI per-file fallback helper. The selected
policy keeps aggregate GUI failures blocking and allows aggregate GUI timeouts
as warning-only only when the complete deterministic fallback passes every GUI
test file.

The maintenance follow-up also adds `v0.1.5-rc1` release-monitoring notes for
public prerelease state, duplicate-free asset checks, retained public download
smoke evidence, open issues `#6` through `#11`, unsigned portable ZIP status,
no MSI/code signing, no bundled external solvers, and no certification claim.
It does not edit the release, mutate assets or issues, execute solvers, bump
versions, install dependencies, or mutate runtime source.

## Next experimental-line follow-up

OSW-VALID-005 later reran prepared-machine discovery and classified issues
`#6` through `#11` as `skipped-missing` because the target optional solver and
science stacks were absent on this machine. The follow-up
[next experimental line selection](next_experimental_line_selection.md) selects
`Plugin ecosystem / optional solver manifest UX` as the next experimental line.

That selection is planning-only. It does not implement source features, edit
the release, mutate issues, execute solvers, install dependencies, bump
versions, claim bundled solvers, claim certification, or treat skipped-missing
validation evidence as issue-closure evidence.
