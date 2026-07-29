# OSW Architecture

The repository uses a `src/osw` package layout. Core domain contracts live under
`osw.core`, while GUI, geometry, mesh, solver, script, and post-processing
packages remain separated by responsibility.

The GUI must coordinate workflows but not directly execute external solver
subprocesses. Solver adapters should prepare validated cases and hand execution
to an explicit backend/service boundary in later milestones.

Heavy integrations such as PySide6, Gmsh, PyVista, Cantera, CoolProp, and SciPy
are optional extras so bootstrap tests can run in a light Python environment.

## Project Schema Integration

The completed PySide6 GUI baseline binds to `osw.core` through ProjectSchema
objects. Core schema, unit, material, validation, and project IO modules remain
PySide6-free; GUI widgets consume them through explicit `set_project()` methods
without replacing the visual shell or adding solver execution behavior.

## Plugin Contract Integration

Plugin manifests and discovery live under `osw.plugins` and remain GUI-free.
Local discovery reads manifest data only, entry point loading is explicit, and
health checks inspect Python package availability and executable presence without
running solver binaries. See `docs/03_plugin_contract.md` for the manifest
schema and security rules.

## Runner Diagnostics Integration

External command execution is centralized behind `ExternalCommandRunner` and
`RunManager`. These services live outside the GUI, accept argument lists instead
of shell strings, capture stdout/stderr, enforce timeouts, and classify runtime
artifacts under controlled run directories. Solver and script adapters may use
this backend boundary in later steps; GUI widgets must not launch subprocesses
directly.

## Mesh Import Bridge

Standard/exported mesh import lives under `osw.mesh` and remains independent of
GUI and solver adapters. The meshio bridge imports meshio lazily, extracts
`MeshInfo` metadata, can attach summaries to ProjectSchema `MeshRef` records,
and reports unsupported, corrupt, or dependency-missing imports through
structured diagnostics. It does not run Gmsh, solvers, shell commands, or native
commercial CAD readers. See `docs/16_mesh_import_bridge.md`.

## M-Script Import Preview

MATLAB/Octave `.m` preview lives under `osw.scripts.mscript` and is text-only.
It classifies scripts/functions/classdefs, extracts help text, function
signatures, plot hints, and structured safety findings, then can attach the
summary to ProjectSchema `ScriptRef` records. It does not require MATLAB,
Octave, Oct2Py, PySide6, or script execution. See
`docs/17_mscript_import_preview.md`.

## GNU Octave Runner

GNU Octave execution lives under `osw.scripts.mscript.octave_runner` and is an
explicit backend request, not an import or preview side effect. The runner
resolves `octave`/`octave-cli` through `ExecutablePathRegistry`, gates execution
with the M-Script safety scan, uses an isolated workspace by default, and hands
process execution to `ExternalCommandRunner` for timeout handling,
stdout/stderr capture, and artifact collection. GUI widgets may call the runner
API, but must not launch subprocesses directly. See `docs/18_octave_runner.md`.

## FigureDataset and Figure Artifacts

Figure artifact normalization lives under `osw.scripts.mscript.figure_capture`
and `osw.scripts.mscript.figure_dataset`. It consumes existing artifacts from
`OctaveRunResult` workspaces or explicit artifact paths and creates serializable
`FigureDataset` records for PNG, SVG, PDF, CSV, and workspace-summary metadata.
The model is optional-dependency friendly: importing it does not require Octave,
MATLAB, PySide6, matplotlib, Pillow, pandas, or `.mat` readers.

Post-processing and GUI surfaces consume `FigureDataset` data without executing
scripts. HTML reports can embed available image references and warn on missing
artifacts, while the GUI Plot Viewer lists figures, metadata, and workspace
variables. See `docs/19_figure_capture_dataset.md`.

## MAT Data Reader

MATLAB `.mat` data import lives under `osw.scripts.mscript.mat_reader` and is a
data-preview boundary. It detects MAT versions, imports SciPy and HDF5 helpers
lazily, summarizes variables, exports simple real numeric 1D/2D arrays to CSV,
and converts variable summaries into `WorkspaceVariableSummary` records for
FigureDataset/report surfaces. It does not run `.m` files, MATLAB, Octave, or
external commands. See `docs/20_mat_reader.md`.

## BoundaryCurve Bridge

Reusable boundary curves live in `osw.core.boundary_curve` and remain
solver-agnostic. The bridge can normalize explicit numeric x/y arrays, CSV
columns, already-loaded MAT variable values, workspace summaries, and
FigureDataset workspace metadata into serializable `BoundaryCurve` records with
axis units, interpolation policy, source traceability, and validation
diagnostics. ProjectSchema stores these curves separately from solver adapters;
boundary conditions may reference a curve id, but no CalculiX, OpenFOAM, SU2, or
other solver boundary file generation is implemented in this layer. See
`docs/21_boundary_curve_bridge.md`.

## Report Generator Binding

Report generation lives under `osw.post` and consumes existing project,
diagnostic, mesh, script, MAT, FigureDataset, BoundaryCurve, plugin-health, and
runner summaries. It builds deterministic `ReportSummary` data and exports
standalone HTML without importing GUI modules or executing solvers/scripts. The
GUI report preview reads this summary data through a safe binding, and CLI
`report-export`/`report-summary` commands operate on ProjectSchema files only.
See `docs/22_report_generator_binding.md`.

## Report Asset Runtime Path Boundary

**`DEFERRED_RETAINED`: native report-asset availability resolution is unsupported and unscheduled.** `osw.core` may preserve typed intent, apply pure lexical rules, build lexical candidates from an explicitly supplied context, and emit path-private projections; it must not turn those results into filesystem facts. `effective_path` remains unavailable and canonical containment remains unknown without a separately authorized native service. The strict zero-provider-contact-before-attestation invariant, empty native implementation allowlist, and empty native-test allowlist remain in force. Unsupported does not mean missing, unreadable, unsafe, or nonexistent. Existing relink and legacy compatibility paths remain outside this typed-resolver native policy and are not certified provider-silent.

**Legacy compatibility paths are outside the typed-resolver `DEFERRED_RETAINED` native policy and are not certified provider-silent.** Their existing path checks or relink behavior may access the filesystem; lexical handling in the typed contract does not convert that behavior into proved filesystem facts. The absence of a new typed native resolver neither validates nor expands legacy behavior, and “unsupported” does not mean a legacy target is missing, unreadable, unsafe, or nonexistent. This closure neither removes nor expands legacy behavior. Any legacy-path security review requires its own authorized gate; explicit relink and unresolved-placeholder behavior remain available within their existing boundaries.

See [Report Asset Runtime Path Native
Deferral](experimental/report_asset_runtime_path_native_deferral.md) for the
canonical claim boundary, retention policy, and reopening criteria.

## Gmsh Adapter

Gmsh primitive meshing lives under `osw.mesh.gmsh_*`. It can generate
deterministic `.geo` scripts without Gmsh installed, and it resolves the local
`gmsh` executable through `ExecutablePathRegistry` without running it. Mesh
generation is explicit through `GmshMeshRequest` and `ExternalCommandRunner`;
GUI code may open the Gmsh dialog and call the adapter API, but it does not call
subprocess directly. Generated `.msh` artifacts can be converted through the
existing optional meshio bridge and attached as ProjectSchema `MeshRef`
metadata. See `docs/23_gmsh_adapter.md`.

## CalculiX Input Deck

CalculiX deck preparation lives under `osw.solvers.calculix`. The bounded v0.1
adapter maps full `MeshModel` topology, isotropic elastic material data, node
sets, fixed supports, and simple loads into deterministic linear static `.inp`
text. It does not run `ccx`, parse results, implement nonlinear/contact
features, or call external commands from the GUI. See
`docs/24_calculix_input_deck.md`.

## OpenFOAM Template Binding

OpenFOAM support lives under `osw.solvers.openfoam` as a bounded template
adapter. It generates deterministic cavity and duct case directories without
requiring OpenFOAM installed, resolves `blockMesh`, `icoFoam`, and `simpleFoam`
through `ExecutablePathRegistry` without executing them, and runs only explicit
`OpenFOAMRunRequest` operations through `ExternalCommandRunner`. Residual log
summaries can be bridged into `ResultDataset` and reports, but OSW v0.1 does
not provide a full OpenFOAM case editor, multiphase/reacting flow support, or
field visualization pipeline. See `docs/27_openfoam_template_binding.md`.

## Result Viewer Dataset Binding

Unified result viewer binding lives across `osw.core.result_dataset`,
`osw.post.result_view_model`, and PySide6 viewer widgets. Core/post models
remain GUI-free and optional-dependency-light; GUI widgets consume
`ResultCatalog` and `ResultDataset` summaries without running solvers, scripts,
external commands, or heavy 3D renderers. CalculiX parsed summaries, OpenFOAM
residuals, FigureDataset records, MAT workspace variables, BoundaryCurve series,
and MeshInfo summaries can be normalized into scalar, series, table, figure,
artifact, and diagnostic records. See
`docs/28_result_viewer_dataset_binding.md`.

## Result Viewer Field Rendering

Field rendering metadata lives under `osw.post.field_dataset` and
`osw.post.field_view_model`. These modules summarize mesh-associated scalar,
vector, and tensor arrays from ResultDataset metadata, MeshInfo/MeshModel
records, and small VTK/VTU-style artifacts without running solvers or importing
PyVista. Optional rendering remains isolated in `osw.post.pyvista_scene`;
missing PyVista returns dependency diagnostics and vector glyph rendering is
explicitly deferred. The GUI FieldViewerPanel is a ResultViewer subpanel and
does not call subprocesses or make visualization dependencies mandatory. See
`docs/30_result_viewer_field_rendering.md`.

## 3D Workspace Active-Scene Lifecycle Foundation

One `MainWindow` document owns one `ActiveSceneController`. The controller is
Qt-free, creates at most one lazy `SceneRendererSession`, owns the scene
generation counter, and records only semantic `base_mesh` and `wireframe`
actors outside the session. Native renderer objects must remain inside the
session. Mesh replacement clears old session resources before replacing the
semantic records, so generation-guarded callbacks from the prior scene become
inert.

The existing `SceneAdapterProtocol` is retained inside a narrow compatibility
session. It is not a new generic renderer framework and does not establish an
interactive renderer. Project replacement closes the old controller before a
fresh document controller is installed, while `MainWindow.closeEvent()` closes
the current controller before Qt child teardown. Both controller and
off-screen `PyVistaScene` close operations are explicit and idempotent; Qt
parent deletion, Python garbage collection, and `__del__` are not cleanup
contracts.

PyVista remains lazy and optional. Screenshot and field-render paths close every
created off-screen Plotter, including failure paths. Missing or failed renderer
initialization stays an explicit metadata-only fallback. PyVistaQt,
`QtInteractor`, embedded interaction, picking, stable mesh identity,
ProjectSchema persistence, solver setup, and interactive result inspection
remain outside this foundation gate.

## 3D Workspace Scene Interaction Core

The central `CentralViewportPanel` is the sole 3D workspace host. It owns the Qt
layout, toolbar presentation, and fallback surface, while the document's
existing `ActiveSceneController` remains the sole logical scene owner. The
controller attaches at most one hosted session and routes bounded interaction
commands for camera fit/presets, trackball interaction, axes, representation,
semantic visibility/isolation, and one transient axis-aligned clipping plane.
The legacy Mesh Preview dialog uses this same controller and cannot create a
second live session.

`osw.gui.workspace_scene_pyvistaqt` contains the one interactive backend. Its
PyVista and PyVistaQt imports are lazy. The session privately owns the
`QtInteractor`, native `base_mesh`/`wireframe` actor handles, render timer,
camera, axes helper, clipping state, and backend callbacks. Representation maps
deterministically to the two semantic records: surface shows only `base_mesh`,
wireframe shows only `wireframe`, and surface-with-edges shows both. Clipping
rebuilds those two actors from the retained logical mesh payload without
persisting a native plane or introducing selection semantics.

PyVistaQt is declared only in the optional `viz` extra at the current
metadata-supported lower bound. A usable interactive environment therefore
requires both `gui` and `viz`; neither PyVista nor PyVistaQt is a base
dependency. Missing PyVista, missing PyVistaQt, or failed initialization keeps
the mock/non-interactive preview visible, reports an explicit diagnostic, and
disables unsupported controls. Session close explicitly stops its timer,
removes actors and transient helpers, closes the interactor, and drops native
references before Qt child cleanup.

The Scene Interaction Core itself added no picking, stable mesh/entity
identity, NamedSelection persistence, ProjectSchema change, camera
persistence, result interaction, solver/setup overlay, report redesign, or
native-locality behavior. Those boundaries remain the baseline for the next
bounded layer.

## 3D Workspace Entity Picking and Named Selections

`osw.mesh.identity` computes `osw.mesh_identity.v1` SHA-256 fingerprints from a
length-delimited byte stream containing the explicit coordinate basis, ordered
finite little-endian float64 points, ordered cell blocks, and complete
non-negative connectivity. Negative zero is normalized. Paths, names,
timestamps, result/quality arrays, renderer objects, and GUI state are
excluded. Source IDs can enter identity only through an explicit, complete,
unique validated namespace.

New node/cell `EntityLocator` records bind an entity namespace and deterministic
IDs to one mesh reference and exact fingerprint. Fallback node IDs are point
ordinals; fallback cell IDs are cell-block ordinal plus block-local ordinal.
VTK/PyVista indices remain transient lookup handles. The pure resolver returns
`UNRESOLVED`, `RESOLVED`, `PARTIAL`, `STALE`, or `INVALID`; only
`RESOLVED` is eligible for a future solver-setup handoff. Legacy positional
targets remain readable but resolve as
`STALE/LEGACY_IDENTITY_UNVERIFIED` until explicit reselection.

Project schemas `0.1` and `0.2` remain readable without automatic mesh access.
Creating durable locator data promotes serialization to schema `0.3`; reopening
preserves identity metadata but initially remains unresolved until an in-memory
mesh is explicitly supplied. Exact fingerprint reload resolves, while changed
coordinates/connectivity fail closed as stale. Camera, clipping,
representation, actor visibility, native handles, and full active-scene state
are not persisted.

The existing document `ActiveSceneController` maps generation-guarded point and
cell callbacks into durable locators and keeps hover, current transient
selection, and persisted NamedSelection overlays separate. One session owns
the semantic `hover`, `current_selection`, and `named_selection:<stable-id>`
native actors. Replace/add/toggle/clear are deterministic; mesh replacement
clears transient state and re-resolves persisted selections. The bounded GUI
supports Node/Cell modes and NamedSelection create, rename, target replacement,
and reference-checked delete. Face/Edge picking, selection invert, solver setup
overlays, result probes, and solver execution remain deferred.

## 3D Workspace Solver Setup Overlays

The local `OSW-3D-WORKSPACE-SOLVER-SETUP-OVERLAYS` feature branch adds three
typed, optional Project schema 0.3 structural records under `Project.physics`:
material-to-cell assignment, translational fixed support on nodes, and global
force on nodes with explicit `N`/`kN` magnitude and `PER_NODE` semantics.
Schemas 0.1 and 0.2 remain readable; typed setup data promotes new in-memory
projects to 0.3 and is never inferred from the legacy maps.

Readiness is computed from the current NamedSelection resolution and project
materials. Only enabled `READY` records project to semantic
`setup:material:<id>`, `setup:fixed-support:<id>`, or `setup:force:<id>` actor
payloads. Missing, legacy, partial, stale, invalid, wrong-domain, overlapping,
or otherwise unsupported records remain visible as blocked diagnostics but
produce no overlay or handoff. Force glyph projection is deterministically
bounded.

The GUI is a thin CRUD/filter/visibility/preview surface. It imports no solver
runner or subprocess API and requires an injected prepare service for its
CalculiX preview action. The CalculiX adapter maps only ready records to
in-memory, deterministic, one-based NSET/ELSET and input fragments; it writes
no deck and exposes no command or execution field. Pressure, thermal,
face/edge targeting, mesh diagnostics, results, and solver execution remain
deferred.

This architecture statement describes a local feature branch only. It is not
integrated into `develop`, not pushed, and not hosted-CI or live PyVistaQt
evidence.

## 3D Workspace Mesh Diagnostics

The chained local Mesh Diagnostics feature extends the existing aggregate
mesh-quality API with a separate fingerprint-bound per-cell analysis. Its only
metric is `osw.mesh_quality.edge_aspect_ratio.v1`, labeled **Edge aspect ratio
preview**: the maximum explicit topological edge length divided by the minimum
positive explicit topological edge length. Linear line, triangle,
quadrilateral, tetrahedron, hexahedron, wedge, and pyramid cells use declared
edge tables. Unknown, high-order, malformed, nonfinite, and degenerate inputs
fail closed instead of falling back to all-pairs distances or guessed corner
nodes. The prior aggregate API and its report serialization remain compatible.

Each immutable quality record carries the exact `osw.mesh_identity.v1`
fingerprint and the existing cell-block/local-ordinal identity namespace.
Analysis is cached only in the active scene controller by fingerprint, metric,
topology-rule version, and zero-edge tolerance. The threshold is deliberately
outside that cache key, so threshold changes derive a new deterministic bad
set without recomputing geometry. The table and the one semantic
`mesh_quality:bad_cells` actor are projected from that same ordered stable-key
set; backend global cell indices remain transient renderer inputs.

The thin panel displays metadata, counts, threshold, status, reasons, and a
deterministic table without reading or changing a mesh file. Highlight,
isolate, restore, and clear affect only diagnostics-owned visibility and retain
selection and solver-setup actors. Missing PyVistaQt keeps metadata and the
table usable while disabling renderer actions with an explicit diagnostic.
No quality value, cache, threshold, actor, or isolation state is persisted in
ProjectSchema, and diagnostics never mark the Project dirty.

This feature is read-only and preview-grade. It adds no mesh editing, repair,
smoothing, refinement, remeshing, cell deletion, automatic NamedSelection,
setup mutation, result inspection, report output, solver execution, or native
locality behavior. This statement describes a local chained feature commit
only: it is not integrated into `develop`, not pushed, and does not claim
hosted-CI or live PyVistaQt evidence.

## 3D Workspace Interactive Results and Stabilization B

The chained local Interactive Results feature retains readable
`osw.result_mesh_binding.v1` metadata but never auto-applies it:
`STALE / LEGACY_BINDING_FINGERPRINT_UNVERIFIED` requires an explicit rebind.
New confirmations persist `osw.result_mesh_binding.v2` with the exact
`osw.mesh_identity.v1` fingerprint. Node/cell counts remain diagnostic only;
equal-count geometry or connectivity changes fail closed.

Scalar projection accepts only exact point or cell rows with finite values.
AUTO range uses the finite data range (with a documented nonzero delta for a
constant field); MANUAL range requires finite ordered bounds. Vector projection
requires exactly three finite components, excludes zero vectors from glyph
construction, and uses deterministic rank sampling with stable entity keys.
Exact point/cell probes and the bounded selected-entity table use stored rows
only—no interpolation, nearest-neighbor transfer, topology conversion, or
result-artifact parser is introduced.

The active scene owns at most one actor for each semantic key:
`result:scalar`, `result:vector`, `result:probe`, and `result:colorbar`.
Scalar coloring snapshots only base-mesh/wireframe visibility, while selection,
setup, and mesh-quality actors keep their existing ownership. Diagnostics
isolation and scalar-surface coloring conflict explicitly rather than silently
overriding each other. Mesh replacement clears rendered result resources and
re-resolves the retained binding against the new exact fingerprint. Renderer
fallback retains pure binding/range/probe/table state and disables render
actions with an explicit reason.

Only explicit binding confirmation/rebinding changes persisted Project
metadata and marks the Project dirty. Field/component/range/colormap/colorbar,
vector sampling, probe, and table state remain transient and never auto-save,
auto-load a mesh, write a file, execute a solver, or change ProjectSchema.
Deformation, timestep/animation, tensors, streamlines, interpolation, results
report integration, and full scene persistence remain deferred. This describes
one isolated local feature branch: it is not integrated, pushed, hosted-CI
validated, or live-PyVistaQt evidence.

## 3D Workspace Persistence and Report Integration

The chained local persistence gate adds the pure
`osw.active_scene.v1` record to the existing Project schema `0.3`. An active
scene stores only an exact mesh reference and fingerprint, pure camera and
clipping values, bounded representation/selection preferences, semantic actor
visibility, stable NamedSelection/setup references, a resolved result-view
request, and the declarative Mesh Diagnostics request. It never stores mesh or
result rows, backend indices, native handles, probes, selected-result tables,
diagnostics caches, isolation snapshots, or scene-generation callbacks.
Canonical UTF-8 JSON produces a deterministic active-scene digest.

Only an explicit Project Save snapshots the current persistable scene. Project
Open remains metadata-only: it does not read a mesh or result artifact, create a
renderer, capture an image, or save the Project. After an explicit mesh load,
restore requires the same logical mesh reference and exact
`osw.mesh_identity.v1` fingerprint; otherwise it reports pending, partial,
stale, or invalid state without mutating NamedSelections, solver setup, mesh
data, or result data. Mesh Diagnostics values are recomputed rather than
persisted, and result actors require an available exact resolved v2 binding.

Screenshot capture is a separate explicit action against the current renderer
session and the exact caller-selected path. Successful capture verifies the
file, hashes its exact bytes, and attaches deterministic scene provenance to an
immutable screenshot record. Capture alone remains Project-dirty neutral.
Only explicit confirmation stages that metadata into
`Project.report_screenshots`; it does not copy the image or auto-save. Report
preview/export consumes persisted screenshot metadata only, performs no
implicit capture, and renders compact path-private provenance plus the existing
local-artifact caveat. The digest is deterministic; pixels are not claimed
identical across GPU, driver, OS, Qt, VTK, or PyVista versions.

Native report-path locality remains `DEFERRED_RETAINED`. This local chained
feature is not integrated into `develop`, not pushed, not hosted-CI validated,
and not live-PyVistaQt evidence.

## CHM CoolProp / Cantera Binding

CHM support lives under `osw.solvers.coolprop` and `osw.solvers.cantera` as
bounded optional-dependency adapters. CoolProp requests calculate simple
thermophysical property points and T/P sweeps through lazy `PropsSI` imports,
while Cantera requests run short in-process 0D constant-volume reactor examples
through lazy Cantera imports. Both adapters return structured diagnostics when
the optional package is missing and convert successful or partial results into
`ResultDataset` tables, scalar summaries, and series for the ResultViewer and
reports. The CHM layer does not run external executables, call subprocesses,
implement reacting CFD, or provide a process flowsheet simulator. See
`docs/29_chm_coolprop_cantera_binding.md`.
