# v0.1.5-rc1 post-release monitoring

## Status

`active monitoring; optional validation issue state reconciled`

`v0.1.5-rc1` is live as a public prerelease at:

https://github.com/CAPTW/OpenSourceWorkBench/releases/tag/v0.1.5-rc1

The post-public audit passed, and the public release body note was corrected to
state that the post-public audit and fresh public asset download smoke completed.

## Current release state

- Release: `v0.1.5-rc1`
- State: public prerelease, not draft
- Package version: `0.1.5rc1`
- Tag object: `88d683c2e08265c86ee419d0c70c55d93f023893`
- Peeled target: `85c8144f7ff19159ab02c40adb6483ce6b13c017`
- Expected assets present:
  - `open_solver_workbench-0.1.5rc1-py3-none-any.whl`
  - `open_solver_workbench-0.1.5rc1.tar.gz`
  - `OpenSolverWorkbench-v0.1.5rc1-windows-x64-portable.zip`
  - `SHA256SUMS.txt`
  - `release_asset_manifest.json`

## Recommended monitoring checks

- Release state remains prerelease and not draft.
- The five expected assets remain present and duplicate-free.
- Public download smoke evidence remains retained in release reports.
- Checksums and `release_asset_manifest.json` remain consistent with the
  published assets.
- Issues `#6`, `#7`, `#8`, `#9`, `#10`, and `#11` remain closed after the
  later bounded optional validation evidence and closure gates. Treat those
  closures as scoped issue-state evidence only, not certification,
  production-readiness, release-readiness, broad solver/science correctness, bundled-solver
  support, or native-Windows validation where evidence was WSL-scoped.
- Historical `skipped-missing` checks remain historical setup evidence only and
  do not replace the later issue-specific validation evidence.
- Public notes continue to avoid stale audit-pending wording.

## Known risks

- The Windows portable ZIP is unsigned.
- No MSI or code signing is provided.
- External solvers are not bundled.
- Live optional validation remains environment-dependent.
- The release is a prerelease and not a certification or production CAE claim.

## Non-claims

- No bundled solver claim.
- No certification claim.
- No signed ZIP or MSI/code-signing claim.
- No live CalculiX validation pass claim.
- No issue `#8` closure claim.
