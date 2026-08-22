# Current Roadmap Pointer

Current public prerelease: `v0.1.5-rc3`.

Current package metadata: `0.1.5rc3`.

Published annotated tag: `v0.1.5-rc3` at
`4b1effccf3bbc4fd18073c0ab39f90cfb6822232`.

Current development cycle: [post-v0.1.5-rc1 development cycle](../development/current_cycle.md).

Published RC3 is the current public prerelease. Later docs-only `develop`
commits do not move that tag or release source. The public prerelease is not
a production release, certification milestone, native-Windows validation
claim, or bundled-solver distribution.

Current recommended sequence:

1. Keep repository docs and ChatGPT Project Sources aligned with current
   package metadata `0.1.5rc3`, the published prerelease `v0.1.5-rc3` at
   release source `4b1effccf3bbc4fd18073c0ab39f90cfb6822232`, the immutable
   historical prerelease `v0.1.5-rc2`, and the immutable historical prerelease
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
6. Treat `BLOCKED_DOCUMENTATION_SEMANTIC_MISMATCH` as historical wording-repair evidence. Published `v0.1.5-rc3` is already public and verified; this does not select final `0.1.5`, RC4, package-index publication, or deployment.
7. Treat the 3D Workspace MVP line as already integrated on the published RC3 source. Later feature or release-line work requires a separate owner decision and must not retarget RC3.

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
