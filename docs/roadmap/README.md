# Post-Public-Release Roadmap

This roadmap starts after the public `v0.1.3-rc1` prerelease and its attached
assets. It separates maintenance, next-feature planning, and optional live
validation so future work remains reviewable and does not blur release claims.

OpenSolver Workbench is educational/research software. It is not a stable
production or industrial-certified solver platform. It is not a MATLAB,
Simulink, ANSYS, or commercial CAD clone. External solvers and optional
scientific packages are not bundled unless a later release explicitly documents
that choice. Users must validate engineering results independently.

## Current State

| Item | Value |
| --- | --- |
| Current public release | `v0.1.3-rc1` |
| Release tag target | `a6e8d3a8211e02359841d10e1947e16ab847b132` |
| Current develop HEAD | `de1585edad0f94c6d9fb2f376bf4393f56a6fc40` |
| Release state | Public prerelease with wheel, sdist, Windows portable ZIP, checksums, and manifest |
| Public docs state | README, screenshots, quickstart, examples, and limitations published on `develop` |

## Roadmap Tracks

| Track | Purpose | Document |
| --- | --- | --- |
| `v0.1.3rc2` maintenance | Stabilize the public prerelease, improve release polish, and collect revalidation evidence without broad feature expansion. | [v0.1.3rc2 maintenance](v0_1_3rc2.md) |
| `v0.1.4` feature line | Plan the next feature development cycle after maintenance tasks are triaged. | [v0.1.4 feature line](v0_1_4.md) |
| Live optional validation | Collect evidence from machines with optional solver and science dependencies installed. | [Live optional validation](live_optional_validation.md) |
| Current pointer | Short handoff page for the currently recommended next steps. | [Current roadmap](current.md) |

## Next GitHub Planning Gate

Recommended next gate: `OSW-GH-001_ISSUES_AND_MILESTONES_TRIAGE`.

That gate should create or update GitHub milestones and issues without changing
source behavior:

- `v0.1.3rc2` maintenance and revalidation.
- `v0.1.4` next-feature planning.
- Live optional validation evidence.
- Packaging and signing investigation.
- Release checklist and asset smoke automation.

Do not create a new release tag or edit the existing GitHub Release from this
roadmap alone.
