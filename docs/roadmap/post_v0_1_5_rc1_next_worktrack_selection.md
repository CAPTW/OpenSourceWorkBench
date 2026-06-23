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

- Develop HEAD: `665aa100b71d1abd9cae25992e8fdf1ab94320b1`
- Release tag target: `85c8144f7ff19159ab02c40adb6483ce6b13c017`
- CLI version: `osw 0.1.5rc1`
- Installed package metadata: `0.1.5rc1`
- Develop is newer than the release tag because OSW-PLAN-009 and
  OSW-RELEASE-041 were post-release planning and release-body follow-up work.

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
