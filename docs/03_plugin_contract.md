# Plugin Contract

OpenSolver Workbench plugins are bounded add-ins for import, preparation,
post-processing, scripting, property models, and reporting. The v0.1 contract is
manifest-first: OSW can discover, validate, and report plugin health without
executing plugin code or external solver binaries.

## Purpose

The plugin layer gives OSW a small typed boundary for future adapters while
keeping the completed GUI baseline and core project schema independent of heavy
optional integrations.

Plugins may eventually prepare cases, import results, preview scripts, evaluate
properties, or generate reports. External execution remains behind a future
runner boundary and is not part of discovery.

## Plugin Types

Supported manifest `type` values are:

- `cad_importer`
- `mesh_importer`
- `mesh_generator`
- `solver_adapter`
- `script_importer`
- `property_model`
- `post_processor`
- `report_plugin`
- `ui_extension`
- `unknown`

The Python contract classes mirror these families:

- `WorkbenchPlugin`
- `CADImporterPlugin`
- `MeshImporterPlugin`
- `MeshGeneratorPlugin`
- `SolverAdapterPlugin`
- `ScriptImporterPlugin`
- `PropertyModelPlugin`
- `PostProcessorPlugin`
- `ReportPlugin`

## Domains

Supported manifest `domain` values are:

- `CAE`
- `CFD`
- `CHM`
- `MATH`
- `GEOMETRY`
- `MESH`
- `REPORT`
- `GENERAL`

Legacy lowercase domains from early manifests are normalized to these values.

## Manifest Schema

Supported manifest file names:

- `manifest.yaml`
- `manifest.yml`
- `manifest.json`
- `plugin.yaml`
- `plugin.json`
- `osw-plugin.yaml`
- `osw-plugin.yml`
- `osw-plugin.json`

Required fields:

- `id`
- `name`
- `version`
- `domain`
- `type`
- `license`
- `capabilities`

Optional fields:

- `description`
- `author`
- `homepage`
- `input_formats`
- `output_formats`
- `requires`
- `optional_requires`
- `executable_names`
- `entry_point`
- `min_osw_version`
- `max_osw_version`
- `ui_panels`
- `example_projects`
- `tags`
- `metadata`

Unknown manifest fields are preserved in `metadata` and surfaced as structured
warnings. Missing required fields and unsupported plugin types are structured
errors.

## Local Directory Discovery

Local discovery accepts:

- a single manifest file;
- a plugin folder containing one manifest;
- a parent folder containing multiple plugin folders;
- explicit search roots from the caller;
- roots listed in `OSW_PLUGINS_PATH`, split by the platform path separator.

Discovery returns manifests, diagnostics, duplicate IDs, and skipped paths. It
does not import local plugin Python modules.

## Python Entry Point Discovery

OSW recognizes these entry point groups:

- `osw.plugins`
- `opensolver_workbench.plugins`

Entry point metadata discovery lists records only. Loading an entry point object
is a separate explicit operation through `load_entry_point_plugin()`.

## Health Check Model

Health statuses are:

- `ok`
- `warning`
- `error`
- `unavailable`
- `unknown`

Health checks inspect manifest data only:

- required Python packages in `requires`;
- optional Python packages in `optional_requires`;
- executable names in `executable_names`;
- legacy executable capability markers such as `requires_executable:ccx`.

Executable checks use `shutil.which()` or explicit configured paths. They do not
run solver binaries.

After `OSW-FUNC-003_RUNNER_DIAGNOSTICS`, plugin health can share
`ExecutablePathRegistry` resolution semantics with the backend runner while
remaining manifest-only. Health checks still do not execute plugin code or
solver binaries.

## Security Rules

- Manifest validation does not execute plugin code.
- Local plugin discovery reads data files only.
- Entry point loading is explicit.
- Solver executables are not run during health checks.
- Script import plugins must not auto-run `.m` files.
- Plugin imports must avoid writing files, changing global state, launching
  processes, or importing heavy dependencies unnecessarily.
- Discovery never performs network access.

## What Discovery Must Not Do

Discovery must not:

- execute OpenFOAM, CalculiX, SU2, Octave, MATLAB, or other external tools;
- import local plugin Python modules just to validate a manifest;
- mutate a project;
- install plugins from remote sources;
- create files outside explicitly requested output/report paths.

## Example Manifests

CalculiX-like solver adapter:

```yaml
id: osw.calculix
name: CalculiX Adapter
version: "0.1.0"
domain: CAE
type: solver_adapter
license: GPL-compatible
input_formats:
  - internal_project_schema
  - inp
output_formats:
  - frd
  - dat
  - vtk
requires: []
optional_requires: []
executable_names:
  - ccx
capabilities:
  - linear_static
  - thermal_placeholder
```

MATLAB/Octave script importer:

```yaml
id: osw.mscript_preview
name: MATLAB/Octave Script Preview Importer
version: "0.1.0"
domain: MATH
type: script_importer
license: GPL-compatible
input_formats:
  - m
output_formats:
  - script_preview
  - script_ref
requires: []
optional_requires: []
executable_names: []
capabilities:
  - m_file_preview
  - function_signature_detection
  - safety_scan
  - plot_hint_detection
  - project_script_ref_binding
```

## Future Extension Points

`OSW-FUNC-004_PLUGIN_MANAGER_DIALOG_BINDING` adds a manifest-first Plugin
Manager dialog. The dialog displays discovered manifests, dependency health,
executable diagnostics, and local enable/disable state without loading plugin
code or running executables.

Later functional steps will bind this contract to:

- MATLAB/Octave preview workflows;
- report generator binding.

`OSW-FUNC-005_MESH_IMPORT_BRIDGE` adds the built-in data-only `osw.meshio`
manifest for the standard mesh import bridge. It declares `mesh_importer`
capabilities and the optional `meshio` dependency, but discovery and health
checks still do not execute plugin code or external tools.

`OSW-FUNC-006_MSCRIPT_IMPORT_PREVIEW` adds the built-in data-only
`osw.mscript_preview` manifest for previewing MATLAB/Octave `.m` files. It
declares `script_importer` capabilities for metadata extraction, safety scan,
plot hints, and ProjectSchema `ScriptRef` binding. It does not require or run
MATLAB, Octave, or script content.

`OSW-FUNC-007_OCTAVE_RUNNER` extends the same manifest with optional GNU Octave
execution capabilities: `octave_execution`, `timeout_policy`,
`stdout_stderr_capture`, `isolated_workspace`, and `artifact_collection`.
`executable_names` may include `octave` and `octave-cli`; health checks resolve
those names only and still do not run Octave, plugin code, or scripts.

## Next Step

Next functional step: `OSW-FUNC-008_FIGURE_CAPTURE_DATASET`.
