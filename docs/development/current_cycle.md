# Current Development Cycle

Current package metadata: `0.1.5rc1`

Current public prerelease: `v0.1.5-rc1`

Branch: `develop`

Release relationship: `develop` may be ahead of the `v0.1.5-rc1` tag

Live validation milestone: `live-optional-validation`

## Cycle Purpose

This cycle keeps post-`v0.1.5-rc1` repository status honest after the
OpenFOAM v12 template compatibility closure line and the later optional
validation issue closure line for #6 through #11. It reconciles docs and
Project Source handoffs before any new implementation gate starts.

## Primary Goals

- Keep release/status docs aligned with package metadata `0.1.5rc1` and public
  prerelease `v0.1.5-rc1`.
- Record that OpenFOAM issues #18 and #19 are closed after WSL-scoped OpenFOAM
  v12 template compatibility evidence.
- Record that optional validation issues #6 through #11 are closed after
  separate bounded evidence and closure gates, while preserving that #18/#19 do
  not independently close #9 and that all six optional validation tracks remain
  conceptually separate.
- Keep skipped-missing optional dependencies distinct from validation pass.
- Prepare bounded follow-up gates without expanding v0.1 scope.

## Non-Goals

- No stable production claim.
- No tag creation without a dedicated release gate.
- No claim that OpenFOAM #18/#19 WSL evidence validates native Windows behavior.
- No claim that closing #18/#19 resolves optional live validation issue #9.
- No claim that closing #6 through #11 is certification, production-readiness
  evidence, release-readiness evidence, bundled-solver support, native-Windows
  validation where evidence was WSL-scoped, or broad solver/science correctness.
- No claim that skipped-missing optional dependencies are passing validation.
- No MATLAB, ANSYS, or Simulink clone.
- No native commercial CAD direct import.
- No industrial certification claim.

## Active References

- [v0.1.3rc2 maintenance](../roadmap/v0_1_3rc2.md)
- [v0.1.4 feature line](../roadmap/v0_1_4.md)
- [Live optional validation](../roadmap/live_optional_validation.md)
- [Post-v0.1.5-rc1 next worktrack selection](../roadmap/post_v0_1_5_rc1_next_worktrack_selection.md)
- [Next experimental line selection](../roadmap/next_experimental_line_selection.md)
- [Release checklist](../10_release_checklist.md)
- [Live optional solver validation evidence](../validation/live_optional_solver_validation.md)

GitHub issues #18 and #19 are closed after WSL-scoped OpenFOAM v12 template
compatibility evidence. GitHub issues #6 through #11 are closed after separate
bounded optional validation evidence and closure gates; issue #9 was not closed
by #18/#19 compatibility closure alone. Local validation artifacts are not
release assets, and closure evidence does not create a new release.
