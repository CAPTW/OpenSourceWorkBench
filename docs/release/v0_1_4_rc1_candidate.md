# v0.1.4-rc1 candidate metadata alignment

Date: 2026-06-06

Repo HEAD before alignment: `b6f6ee0c9a7ead52d8947d987461dff798fea8b2`

## Status

Metadata is aligned for the `v0.1.4-rc1` candidate.

This page records metadata and documentation alignment only:

- no `v0.1.4-rc1` tag exists yet;
- no `v0.1.4-rc1` release assets exist yet;
- no GitHub Release for `v0.1.4-rc1` exists yet;
- no release asset build, upload, overwrite, or publication was performed.

## Baseline Public Release

- Current public release: `v0.1.3-rc1`
- Current public release tag target:
  `a6e8d3a8211e02359841d10e1947e16ab847b132`
- Public release state: published prerelease, not draft
- Public release assets: wheel, sdist, Windows portable ZIP, `SHA256SUMS.txt`,
  and `release_asset_manifest.json`

The existing `v0.1.3-rc1` tag and public GitHub Release remain the current
published prerelease boundary.

## Candidate

- Version metadata: `0.1.4rc1`
- Intended tag: `v0.1.4-rc1`
- Tag status: not created
- Asset status: not built
- GitHub Release status: not created

The candidate tag must be created only by a later explicit tag gate after final
revalidation passes.

## Included Work Since v0.1.3-rc1

The candidate metadata covers the completed work on `develop` after the public
`v0.1.3-rc1` prerelease:

- release asset smoke automation and read-only CI workflow;
- Windows portable ZIP UX documentation and checks;
- onboarding examples and tutorials;
- code signing / installer strategy documentation;
- Plugin Manager UX and install receipts;
- ResultViewer / FieldViewer workflow improvements;
- VFEA experimental scope definition;
- QA, release-trust, docs, and test hardening.

## Remaining Open Issues

| Issue | Title | Status |
| --- | --- | --- |
| `#6` | Run live Gmsh validation | live optional validation |
| `#7` | Run live GNU Octave validation | live optional validation |
| `#8` | Run live CalculiX ccx validation | live optional validation |
| `#9` | Run live OpenFOAM validation | live optional validation |
| `#10` | Run live CoolProp and Cantera validation | live optional validation |
| `#11` | Run live PyVista and meshio validation | live optional validation |

These remain environment-specific and are not claimed as completed by metadata
alignment.

## Not Included / Not Claimed

This candidate metadata does not claim:

- stable production status;
- live optional solver validation completion;
- VFEA implementation;
- MSI installer, MSIX package, Microsoft Store distribution, or code signing;
- bundled external solvers;
- industrial certification;
- native commercial CAD import.

## Required Next Gates

1. Final revalidation:
   - rerun focused and broad QA against `0.1.4rc1`;
   - verify release, docs, scope, architecture, and artifact guardrails.
2. Local tag creation:
   - create an annotated `v0.1.4-rc1` tag only after revalidation passes;
   - verify tag object type and peeled target.
3. Asset build from tag:
   - build wheel, sdist, and Windows portable ZIP only from the verified tag if
     maintainers choose asset publication.
4. Asset download smoke:
   - verify checksums, manifest, archive safety, and install/portable smoke.
5. GitHub Release draft or publish:
   - create or publish a GitHub Release only in a dedicated release gate.

## Risks

- `v0.1.4-rc1` remains a prerelease candidate.
- The Windows portable ZIP remains unsigned unless a later signing gate changes
  that.
- Optional dependency and live solver evidence remains environment-specific.
- External solvers are not bundled.
- Public docs on `develop` may be newer than the `v0.1.3-rc1` tag until the
  `v0.1.4-rc1` tag is created.
