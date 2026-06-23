# Post-v0.1.5-rc1 next scope decision

## Status

`completed`

This planning-only review records the next work path after the public
`v0.1.5-rc1` prerelease flow. It does not edit the release, mutate issues, run
solvers, bump versions, or change runtime source.

## Current public release

- Current public release: `v0.1.5-rc1`
- URL: https://github.com/CAPTW/OpenSourceWorkBench/releases/tag/v0.1.5-rc1
- State: public prerelease, not draft
- Tag object: `88d683c2e08265c86ee419d0c70c55d93f023893`
- Tag target: `85c8144f7ff19159ab02c40adb6483ce6b13c017`
- Package and CLI version: `0.1.5rc1`
- Expected assets: wheel, sdist, Windows portable ZIP, `SHA256SUMS.txt`, and
  `release_asset_manifest.json`

## Release audit summary

The `v0.1.5-rc1` release is a public prerelease with the expected five assets
present. The post-public download audit passed: the public assets were
downloaded, checksums and manifest were verified, and wheel, sdist, and Windows
portable ZIP smoke checks completed.

The audit preserved the release and repository boundaries: no asset upload,
asset deletion, release edit, tag push, branch push, issue mutation, source
mutation, dependency upgrade, or solver execution was performed.

## Known non-blocking warnings

- OSW-RELEASE-041 corrected the release body note that previously said
  post-public audit pending.
- The GUI aggregate timeout required per-file fallback during the release QA
  line; that fallback evidence remains acceptable for the prerelease flow.
- The Windows portable ZIP remains unsigned.
- No MSI or code signing is provided.
- External solvers are not bundled.
- Live optional validation remains environment-dependent.

## Open validation

Live optional validation remains open:

- `#6` Gmsh live validation remains open.
- `#7` GNU Octave live validation remains open.
- `#8` CalculiX `ccx` live validation remains open; OSW-VALID-004 was
  `skipped-missing` because `ccx` was absent.
- `#9` OpenFOAM live validation remains open.
- `#10` CoolProp / Cantera live validation remains open.
- `#11` PyVista / meshio live validation remains open.

## Decision

Selected decision: `OSW-RELEASE narrow public release body note update, only to replace stale "post-public audit pending" wording`

## Rationale

The release has already been published and the public download audit passed, but
the release body may still contain stale draft-era wording that says the
post-public audit is pending. That is public-facing release text, so correcting
that narrow note is the highest-priority next step before starting a new
experimental line or broader validation campaign.

Prepared-machine live optional validation remains important, but it depends on
external solver/tool availability. A new experimental line should wait until
the public release notes accurately describe the completed post-public audit.

## Non-actions

- No release edit was performed in this planning gate.
- No issue mutation was performed.
- No solver execution was performed.
- No version bump or metadata alignment was performed.
- No branch, tag, or asset mutation was performed.
- No runtime source, GUI source, CLI source, or ProjectSchema mutation was
  performed.

## Next recommended gate

`OSW-RELEASE-041_V0_1_5RC1_PUBLIC_RELEASE_BODY_NOTE_UPDATE`

The next gate should narrowly update the public `v0.1.5-rc1` release body to
replace stale "post-public audit pending" wording with public-safe wording that
states the post-public audit passed, without changing assets, tags, issues,
source, or release publication state.

Follow-up:
OSW-RELEASE-041 completed that narrow release-body note update. The next
[post-v0.1.5-rc1 worktrack selection](post_v0_1_5_rc1_next_worktrack_selection.md)
selects maintenance hardening for GUI aggregate timeout behavior and
release-monitoring notes, without starting validation or experimental work in
the planning gate.
