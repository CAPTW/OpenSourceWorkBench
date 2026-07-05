# Post-Public-Release Roadmap

This roadmap started after the public `v0.1.3-rc1` prerelease and now tracks
the later `v0.1.5-rc1` public prerelease line. It separates maintenance,
next-feature planning, and optional validation so future work remains
reviewable and does not blur release claims.

OpenSolver Workbench is educational/research software. It is not a stable
production or industrial-certified solver platform. It is not a MATLAB,
Simulink, ANSYS, or commercial CAD clone. External solvers and optional
scientific packages are not bundled unless a later release explicitly documents
that choice. Users must validate engineering results independently.

## Current State

| Item | Value |
| --- | --- |
| Current public release | `v0.1.5-rc1` |
| Release tag target | `85c8144f7ff19159ab02c40adb6483ce6b13c017` |
| Optional validation closure snapshot baseline | `de93800edfdd13008eee962f045fd3cdb866ab4c` |
| Release state | Public prerelease with wheel, sdist, Windows portable ZIP, checksums, and manifest |
| Optional validation state | Issues #6 through #11 are closed after separate bounded validation evidence and closure gates; #18/#19 remain closed as WSL-scoped OpenFOAM v12 template compatibility evidence. |
| Public docs state | README, screenshots, quickstart, examples, limitations, validation matrix, and current-status docs on `develop` may be newer than the release tag |

## Roadmap Tracks

| Track | Purpose | Document |
| --- | --- | --- |
| `v0.1.3rc2` maintenance | Stabilize the public prerelease, improve release polish, and collect revalidation evidence without broad feature expansion. | [v0.1.3rc2 maintenance](v0_1_3rc2.md) |
| `v0.1.4` feature line | Plan the next feature development cycle after maintenance tasks are triaged. | [v0.1.4 feature line](v0_1_4.md) |
| Live optional validation | Historical and future evidence from machines with optional solver and science dependencies installed. Current issues #6 through #11 are closed with bounded caveats. | [Live optional validation](live_optional_validation.md) |
| Current pointer | Short handoff page for the currently recommended next steps. | [Current roadmap](current.md) |

## Next GitHub Planning Gate

Recommended next gate: `OSW-REPO_SNAPSHOT_PROJECT_SOURCE_AFTER_OPTIONAL_VALIDATION_DOCS_RECONCILIATION`.

That gate should create one compact source-ready repo snapshot after the docs
commit. It should not mutate source behavior, GitHub issues, releases, tags, or
assets.

Do not create a new release tag or edit the existing GitHub Release from this
roadmap alone.
