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

The native-deferral documentation review, commit `adad148becf87ead12f4e3a16f59530d048b21a6`, and post-commit verification are complete. `SELECT_FULL_EXISTING_HISTORY_FAST_FORWARD_PATH` remains the selected ancestry direction. A subsequent full-range publication-readiness gate stopped at `BLOCKED_DOCUMENTATION_SEMANTIC_MISMATCH`. This additive documentation amendment corrects the known wording defects only; it does not validate runtime behavior or publish history. Publication remains blocked until the amended tip receives a fresh full-range validation and publication-readiness result.

The narrower
`OSW-3D-WORKSPACE-ACTIVE-SCENE-OWNERSHIP-ADAPTER-AND-TEARDOWN-FOUNDATION`
is implemented and validated only on its retained isolated local feature
branch. The chained `OSW-3D-WORKSPACE-SCENE-INTERACTION-CORE` exact base adds
one optional central PyVistaQt session and bounded camera/representation/clip
interaction, also without integration or publication. The current isolated
`OSW-3D-WORKSPACE-ENTITY-PICKING-AND-NAMED-SELECTION` branch adds exact mesh
fingerprints, durable node/cell locators, fail-closed five-state resolution,
Project schema 0.3 selection persistence, generation-guarded picking, and
NamedSelection CRUD. Fake-session/offscreen evidence is not prepared live
PyVistaQt evidence. Face/Edge, setup/result overlays, full scene persistence,
solver execution, integration, publication, and Golden repair remain separate.

The chained local `OSW-3D-WORKSPACE-SOLVER-SETUP-OVERLAYS` branch adds typed
material, translational fixed-support, and global per-node force records;
fail-closed setup status; semantic overlays; a bounded
CRUD/filter/visibility panel; and a pure deterministic CalculiX prepare-only
handoff. It remains isolated, not integrated into `develop`, not pushed, and
not remotely validated. PyVistaQt live rendering, GPU/OpenGL portability,
pressure/thermal and face/edge targeting, mesh diagnostics, results/probes,
solver execution, full scene persistence, Golden repair, and publication
remain separate.

The next chained local `OSW-3D-WORKSPACE-MESH-DIAGNOSTICS` branch adds one
preview-grade explicit-topology edge-aspect-ratio analysis bound to the exact
mesh fingerprint and existing stable cell ordinals. It provides a transient
thresholded table plus one semantic bad-cell highlight/isolate actor, while
retaining table-only diagnostics when the renderer is unavailable. The
analysis cache, threshold, table, actor, and isolation state are not persisted
and do not mark the Project dirty. The feature does not edit or repair meshes,
create NamedSelections, mutate solver setup/results, write files, or execute a
solver. It remains isolated, not integrated into `develop`, not pushed, and
not remotely validated. Live PyVistaQt/GPU evidence, unsupported or high-order
topology support, mesh repair, full scene persistence, Golden/Gmsh
maintenance, native locality, and publication remain separate. Interactive
Results/probes were separate from that Mesh Diagnostics gate and are addressed
only by the following chained local gate.

The chained local
`OSW-3D-WORKSPACE-INTERACTIVE-RESULTS-AND-STABILIZATION-B` branch adds
fingerprint-backed v2 ResultDataset bindings, fail-closed readable v1
compatibility, finite point/cell scalar ranges, deterministic bounded
three-component vector glyphs, exact point/cell probes, and a bounded selected
result table. Four session-private semantic result resources replace
deterministically and are cleared or marked stale on mesh change. Renderer
fallback retains pure binding/range/probe/table state but makes no render
success claim. Only explicit binding confirmation/rebinding marks the Project
dirty; transient visualization state is not persisted. No result artifact is
parsed, no solver executes, no mesh is deformed or edited, and no file is
written. The feature remains isolated, not integrated into `develop`, not
pushed, and not remotely validated. Live PyVistaQt/GPU evidence, result-report
integration, full active-scene persistence, deformation/timestep/tensor/
streamline work, Golden/Gmsh maintenance, native locality, and publication
remain separate.

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
