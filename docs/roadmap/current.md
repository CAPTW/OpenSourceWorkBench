# Current Roadmap Pointer

Current public prerelease: `v0.1.5-rc1`.

Current package metadata: `0.1.5rc1`.

Current development cycle: [post-v0.1.5-rc1 development cycle](../development/current_cycle.md).

`develop` may be ahead of the `v0.1.5-rc1` release tag. The public prerelease is
not a production release, certification milestone, native-Windows validation
claim, or bundled-solver distribution.

Current recommended sequence:

1. Keep repository docs and ChatGPT Project Sources aligned with the current
   `v0.1.5-rc1` / `0.1.5rc1` status.
2. Treat OpenFOAM issues #18 and #19 as closed only for WSL-scoped OpenFOAM v12
   template compatibility evidence: `physicalProperties`, `pFinal`, `blockMesh`
   exit 0, and `icoFoam` exit 0 for the Foundation cavity. Duct status remains
   generation/layout-verified only.
3. Keep optional validation issues #6 through #11 open and separate. Missing
   optional dependencies are skipped-missing, not pass.
4. Plan GUI runner-boundary hardening as a later P1 gate; do not use docs status
   cleanup as permission for GUI direct solver execution.

## Track Links

- [v0.1.3rc2 maintenance](v0_1_3rc2.md)
- [v0.1.4 feature line](v0_1_4.md)
- [Live optional validation](live_optional_validation.md)
- [Post-v0.1.5-rc1 next worktrack selection](post_v0_1_5_rc1_next_worktrack_selection.md)
- [Next experimental line selection](next_experimental_line_selection.md)
- [Current development cycle](../development/current_cycle.md)

## Scope Reminder

OSW is an educational/research Engineering Solver & Script Workbench. It is not
a MATLAB, Simulink, ANSYS, or commercial CAD clone. It is not an
industrial-certified solver platform. External solver and optional science
dependencies are local user-provided tools unless a later release explicitly
documents otherwise.
