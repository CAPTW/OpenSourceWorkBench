# OpenSolver Workbench v0.1.5

## 1. Final 0.1.5 identity and overview

This GitHub release publishes OpenSolver Workbench package
`open-solver-workbench` version `0.1.5` as annotated tag `v0.1.5`. The
source is the `develop` final metadata commit that follows published RC3
source `4b1effccf3bbc4fd18073c0ab39f90cfb6822232` and the later
post-publication docs-closure commit
`e3beb87af3e2ac134f848beb599dae12167a9bf0`. Final means a stable semantic
version for the documented educational and research preview scope. It is
not unrestricted production readiness, industrial certification, or solver
numerical certification.

## 2. Why final follows RC3

Final `0.1.5` follows published and verified RC3 and the later green
docs-closure commit. RC3 provided a green tagged-source candidate on the
existing `0.1.5` line that contains both post-RC2 QA repairs. The
docs-closure commit recorded that published RC3 identity without changing
package version `0.1.5rc3` or moving the RC3 tag or release source. Final
metadata then promotes current package identity to `0.1.5` on that same
line.

## 3. RC1, RC2, and RC3 continuity

Annotated `v0.1.5-rc1` remains at peeled commit
`85c8144f7ff19159ab02c40adb6483ce6b13c017`. Published annotated
`v0.1.5-rc2` remains at peeled commit
`3eced55adf49e70690af80aeb1eb9a8b053555fd` as GitHub prerelease
`374775403`. Published annotated `v0.1.5-rc3` remains at peeled commit
`4b1effccf3bbc4fd18073c0ab39f90cfb6822232` as GitHub prerelease
`374854738`. RC1, RC2, and RC3 tag objects, release bodies, and published
assets remain immutable historical records. RC2 historical tagged-source CI
remains failed and visible. This final release does not rewrite that
history.

## 4. 3D Workspace MVP capability summary

Final `0.1.5` carries the integrated 3D workspace preview: mesh load, scene
interaction, NamedSelections, solver-setup overlays, mesh diagnostics,
interactive results, persistence, and report capture. It is an educational
and research preview, not a production CAE product.

## 5. Post-RC2 QA repair continuity

The RC3 line retained both post-RC2 QA repairs:

- `a2a0b4b90a998420ca09cef7bf94a1f5d8b28c7b` — `fix(qa): normalize Windows paths in golden tests`
- `c30ef8c70554461be297f833f2934d08baec0870` — `fix(qa): recognize certification denial language`

Those repairs are QA and test-tooling only. They do not change product
runtime behavior beyond the package version identity.

## 6. RC3 green-source and publication evidence

Required GitHub workflows passed on published RC3 source
`4b1effccf3bbc4fd18073c0ab39f90cfb6822232`:

- OSW CI run `32555950013`
- Release asset smoke run `32555949955`

RC3 GitHub prerelease `374854738` is public with exactly four verified
assets. Draft and published remote-download hashes matched. Downloaded
base and native installed-package smokes passed. Historical failed runs
`32545992919` and `32548389175` remain failed and visible.

## 7. Post-RC3 docs closure

Docs-only `develop` commit `e3beb87af3e2ac134f848beb599dae12167a9bf0`
recorded the published RC3 identity, monitoring closure, and current
public-prerelease facts. It did not change package version `0.1.5rc3`,
product runtime modules, workflows, or the RC3 tag or release source.
Required GitHub workflows on that docs-closure commit also succeeded:

- OSW CI run `32560749949`
- Release asset smoke run `32560749970`

## 8. Final package and build qualification

Final `0.1.5` wheel and sdist artifacts are newly built from the final
metadata source. They are not renamed, relabeled, hard-linked, or reused
RC3 artifacts. Package metadata, archive membership, and installed-package
smokes use version `0.1.5`. Base and native installed-package smokes import
`osw` from the install target rather than a source checkout.

## 9. Exact public asset inventory

The public GitHub Release asset set is exactly four files:

1. `open_solver_workbench-0.1.5-py3-none-any.whl`
2. `open_solver_workbench-0.1.5.tar.gz`
3. `SHA256SUMS.txt`
4. `release_asset_manifest.json`

Release notes are the GitHub release body only and are not a fifth public
asset.

## 10. Upgrade and migration notes

Users moving from published `0.1.5rc3` to final `0.1.5` keep the same
documented educational and research preview scope. Install the new final
wheel or sdist. Do not rename RC3 artifacts as final artifacts. RC1, RC2,
and RC3 public identities remain available as historical prereleases.

## 11. Supported topology

Supported preview topology remains triangle, quad, and polygon surface
rendering plus linear tetra.

## 12. Unsupported topology

Unsupported topology remains tetra10, hexahedron, hexahedron20, wedge, and
pyramid.

## 13. CalculiX handoff limitations

CalculiX remains the bounded educational subset. Export and prepare-only
handoff do not execute a solver, do not bundle solver binaries, and do not
claim numerical certification.

## 14. Diagnostics advisory boundary

Scaled Jacobian and related mesh-quality diagnostics remain advisory
preview metrics. They do not edit or repair meshes and do not certify mesh
adequacy.

## 15. Result fingerprint boundary

Exact mesh-fingerprint binding remains required for result attachment.
Nearest-map or interpolated transfers are not provided.

## 16. Screenshot cross-GPU boundary

Screenshots are explicit current-session captures. Cross-GPU or
cross-platform pixel identity is not claimed.

## 17. PDF optional and deferred behavior

PDF report output remains optional and deferred. HTML reports may consume
persisted stored images. Missing PDF support is an explicit deferred path,
not a silent success.

## 18. Native-locality boundary

Native report-asset filesystem resolution remains `DEFERRED_RETAINED`.
Production native resolution is unsupported.

## 19. Claim boundary

No package-index publication is configured. No deployment is claimed. No
unrestricted production-readiness claim is made. No industrial
certification claim is made. No solver-numerical-certification claim is
made. No all-platform or all-topology claim is made. Final `0.1.5` is a
stable semantic version for the documented educational and research
preview scope.
