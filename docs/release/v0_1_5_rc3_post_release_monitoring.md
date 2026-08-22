# v0.1.5-rc3 post-release monitoring

## Status

`RC3_PUBLISHED_VERIFIED_POST_PUBLICATION_DOCUMENTATION_CLOSURE`

`v0.1.5-rc3` is live as a public prerelease at:

https://github.com/CAPTW/OpenSourceWorkBench/releases/tag/v0.1.5-rc3

Published timestamp: `2026-08-22T06:51:24Z`.

```text
RC3_RELEASE_SOURCE = 4b1effccf3bbc4fd18073c0ab39f90cfb6822232
CURRENT_DEVELOP_AFTER_DOCS_CLOSURE = this docs-only post-publication commit on develop
```

Later docs-only `develop` commits do not move the RC3 tag or release source.
Package version remains `0.1.5rc3`. RC3 is not final `0.1.5`.

## Current release state

- Release: `v0.1.5-rc3`
- Release ID: `374854738`
- State: public prerelease, not draft
- Package version: `0.1.5rc3`
- Tag object: `841db318dade807e5294718d4e50813934752d0a`
- Peeled target / release source: `4b1effccf3bbc4fd18073c0ab39f90cfb6822232`
- Tag message: `OpenSolver Workbench v0.1.5-rc3`
- Signing: unsigned
- Expected assets present (exact four):
  - `open_solver_workbench-0.1.5rc3-py3-none-any.whl` (`524764240`, `1219269` bytes, SHA-256 `40023dad707adeb16dd2bbbc00477bda31ae39eae83e44983f84b79ee7f36c5e`)
  - `open_solver_workbench-0.1.5rc3.tar.gz` (`524764242`, `1036147` bytes, SHA-256 `0f5ab779d7abb2523ceb7a85faff88bb9b7955c4bd340aed29b252a49a7ba571`)
  - `SHA256SUMS.txt` (`524764241`, `312` bytes, SHA-256 `25426ca9fcf2fb220edca5678e94c00fb1ed132498eba8a915aae0e1b3669e39`)
  - `release_asset_manifest.json` (`524764243`, `3722` bytes, SHA-256 `f4ddf0705d757d3497a450c04518c817b46158708947d94d1922fcff9327cb47`)

## Publication evidence

- Draft and published remote-download hashes matched the qualified local bundle.
- Downloaded base installed-package smoke passed.
- Downloaded native installed-package smoke passed.
- Green RC3 source OSW CI: `32555950013` on `4b1effccf3bbc4fd18073c0ab39f90cfb6822232`.
- Green RC3 source Release asset smoke: `32555949955` on `4b1effccf3bbc4fd18073c0ab39f90cfb6822232`.
- No automatic GitHub workflow is triggered by RC3 tag or release actions under current workflow definitions.
- No package-index publication is configured.
- No deployment occurred under the publication or this monitoring gate.

## Immutable historical identities

- Annotated `v0.1.5-rc1` remains at peeled commit `85c8144f7ff19159ab02c40adb6483ce6b13c017`.
- Annotated `v0.1.5-rc2` remains at peeled commit `3eced55adf49e70690af80aeb1eb9a8b053555fd`.
- GitHub prerelease `374775403` for `v0.1.5-rc2` remains published with its exact four assets.
- Historical failed workflows `32545992919` and `32548389175` remain historical failures.

## Recommended monitoring checks

- Release state remains prerelease and not draft.
- Release ID remains `374854738`.
- The four expected assets remain present, duplicate-free, and identity-bound.
- Checksums and `release_asset_manifest.json` remain consistent with the published assets.
- The tag continues to peel to `4b1effccf3bbc4fd18073c0ab39f90cfb6822232`.
- Later `develop` documentation commits are not described as RC3 binary or tag-source artifacts.
- RC1 and RC2 identities remain unchanged.
- Public notes continue to avoid planned-tag or publication-pending wording for RC3.

## Known risks

- No MSI or code signing is provided.
- External solvers are not bundled.
- Native report-asset filesystem resolution remains `DEFERRED_RETAINED`.
- The release is a prerelease and not a certification or production CAE claim.
- Final `0.1.5`, another RC, or hold remains an owner decision outside this page.

## Non-claims

- No bundled solver claim.
- No industrial-certification claim.
- No solver-numerical-certification claim.
- No all-platform or all-topology claim.
- No production-readiness claim.
- No package-index publication claim.
- No deployment claim.
- No native-locality proof.
- No claim that later docs-only `develop` commits retarget RC3.
