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
