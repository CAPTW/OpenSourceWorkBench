# Current Roadmap Pointer

Current public prerelease: `v0.1.5-rc2`.

Current package metadata: `0.1.5rc3`.

Planned next annotated tag: `v0.1.5-rc3` (not created).

Current development cycle: [post-v0.1.5-rc1 development cycle](../development/current_cycle.md).

`develop` is ahead of the immutable published `v0.1.5-rc2` release tag. The
public prerelease is not a production release, certification milestone,
native-Windows validation claim, or bundled-solver distribution.

Current recommended sequence:

1. Keep repository docs and ChatGPT Project Sources aligned with current
   package metadata `0.1.5rc3`, planned tag `v0.1.5-rc3`, the immutable
   published prerelease `v0.1.5-rc2`, and the immutable historical prerelease
   `v0.1.5-rc1`.
2. Treat OpenFOAM issues #18 and #19 as closed only for WSL-scoped OpenFOAM v12
   template compatibility evidence: `physicalProperties`, `pFinal`, `blockMesh`
   exit 0, and `icoFoam` exit 0 for the Foundation cavity. Duct status remains
   generation/layout-verified only.
3. Treat optional validation issues #6 through #11 as closed after separate
   bounded evidence and closure gates. Keep the per-issue caveats visible:
   WSL-scoped evidence stays WSL-scoped, native Windows remains unvalidated
   where applicable, local validation artifacts are not release assets, and
   bounded validation is not certification, production-readiness, broad
   solver/science correctness, or release-readiness.
4. Plan GUI runner-boundary hardening as a later P1 gate; do not use docs status
   cleanup as permission for GUI direct solver execution.
5. Treat the native-deferral documentation review, commit `adad148becf87ead12f4e3a16f59530d048b21a6`, and post-commit verification as complete. Keep `SELECT_FULL_EXISTING_HISTORY_FAST_FORWARD_PATH` as the selected ancestry direction.
6. Keep publication blocked after `BLOCKED_DOCUMENTATION_SEMANTIC_MISMATCH`. This additive documentation amendment corrects wording only; the amended tip still requires fresh full-range validation and publication-readiness review before any push or publication.
7. Keep `SELECT_3D_WORKSPACE_MVP_DELIVERY_PLAN` selected but queued. `OSW-3D-WORKSPACE-SCENE-INTERACTION-CORE` has not started and cannot start until the clean published-baseline entry conditions pass.

**Native report-asset filesystem resolution is `DEFERRED_RETAINED`.** Production native resolution is unsupported, the strict zero-provider-contact-before-attestation invariant remains unchanged, and no implementation is scheduled. Accepted schema, lexical, privacy, stale-binding, relink, and unresolved-placeholder contracts and their evidence remain retained. The status is not an implementation failure or a native-support claim; reopening requires a qualifying trigger and a separately authorized policy/architecture gate. Branches, worktrees, and evidence remain retained until a separate cleanup decision. Legacy compatibility paths remain outside the typed-resolver policy and are not certified provider-silent.

## Track Links

- [v0.1.3rc2 maintenance](v0_1_3rc2.md)
- [v0.1.4 feature line](v0_1_4.md)
- [Live optional validation](live_optional_validation.md)
- [Post-v0.1.5-rc1 next worktrack selection](post_v0_1_5_rc1_next_worktrack_selection.md)
- [Next experimental line selection](next_experimental_line_selection.md)
- [Report asset runtime path native deferral](../experimental/report_asset_runtime_path_native_deferral.md)
- [Current development cycle](../development/current_cycle.md)

## Scope Reminder

OSW is an educational/research Engineering Solver & Script Workbench. It is not
a MATLAB, Simulink, ANSYS, or commercial CAD clone. It is not an
industrial-certified solver platform. External solver and optional science
dependencies are local user-provided tools unless a later release explicitly
documents otherwise.
