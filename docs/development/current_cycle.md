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

## Publication And 3D Baseline Status

The native-deferral documentation review, commit `adad148becf87ead12f4e3a16f59530d048b21a6`, and post-commit verification are complete. `SELECT_FULL_EXISTING_HISTORY_FAST_FORWARD_PATH` remains the selected ancestry direction. A subsequent full-range publication-readiness gate stopped at `BLOCKED_DOCUMENTATION_SEMANTIC_MISMATCH`. This additive documentation amendment corrects the known wording defects only; it does not validate runtime behavior or publish history. Publication remains blocked until the amended tip receives a fresh full-range validation and publication-readiness result. The 3D MVP delivery plan is selected, but `OSW-3D-WORKSPACE-SCENE-INTERACTION-CORE` has not started and cannot start until its clean published-baseline entry conditions pass.

**Native report-asset filesystem resolution is `DEFERRED_RETAINED`.** Production native resolution is unsupported, the strict zero-provider-contact-before-attestation invariant remains unchanged, and no implementation is scheduled. Accepted schema, lexical, privacy, stale-binding, relink, and unresolved-placeholder contracts and their evidence remain retained. The status is not an implementation failure or a native-support claim; reopening requires a qualifying trigger and a separately authorized policy/architecture gate. Branches, worktrees, and evidence remain retained until a separate cleanup decision. Legacy compatibility paths remain outside the typed-resolver policy and are not certified provider-silent.

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
- Keep the report-asset native-deferral documentation aligned while leaving the
  native implementation and native-test allowlists empty.
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
- No report-asset native resolver/service/adapter implementation, native test,
  policy reopening, legacy-path security review, or retained-evidence cleanup.
- No industrial certification claim.

## Active References

- [v0.1.3rc2 maintenance](../roadmap/v0_1_3rc2.md)
- [v0.1.4 feature line](../roadmap/v0_1_4.md)
- [Live optional validation](../roadmap/live_optional_validation.md)
- [Post-v0.1.5-rc1 next worktrack selection](../roadmap/post_v0_1_5_rc1_next_worktrack_selection.md)
- [Next experimental line selection](../roadmap/next_experimental_line_selection.md)
- [Report asset runtime path native deferral](../experimental/report_asset_runtime_path_native_deferral.md)
- [Release checklist](../10_release_checklist.md)
- [Live optional solver validation evidence](../validation/live_optional_solver_validation.md)

GitHub issues #18 and #19 are closed after WSL-scoped OpenFOAM v12 template
compatibility evidence. GitHub issues #6 through #11 are closed after separate
bounded optional validation evidence and closure gates; issue #9 was not closed
by #18/#19 compatibility closure alone. Local validation artifacts are not
release assets, and closure evidence does not create a new release.
