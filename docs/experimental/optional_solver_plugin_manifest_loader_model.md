# Optional solver plugin manifest loader model

## Status

Experimental loader model implemented for explicit dict/file loading only.

This gate adds a data-only loader for optional solver manifest documents. It has
no plugin code execution, no directory scanning, no network fetch, no solver
execution, and no dependency installation.

Status boundaries:

- no plugin code execution
- no directory scanning
- no network fetch
- no solver execution
- no dependency installation

## Relationship to plugin manifest loading design

The loader implements the model slice described in
`optional_solver_plugin_manifest_loading_design.md`. It keeps future
plugin-provided optional solver metadata declarative and schema-compatible while
leaving CLI preview, GUI display, package discovery, and plugin integration to
later gates.

## Package path and public API

Package path:

`src/osw/experimental/optional_solvers/plugin_manifest_loader.py`

Public API:

- `OptionalSolverManifestSourceType`
- `OptionalSolverManifestTrustLabel`
- `OptionalSolverManifestSource`
- `OptionalSolverPluginManifestDocument`
- `OptionalSolverLoadedManifest`
- `OptionalSolverRejectedManifest`
- `OptionalSolverManifestConflict`
- `OptionalSolverPluginManifestLoadDiagnostic`
- `OptionalSolverPluginManifestLoadReport`
- `OptionalSolverPluginManifestLoaderOptions`
- `load_optional_solver_plugin_manifest_dict`
- `load_optional_solver_plugin_manifest_json`
- `load_optional_solver_plugin_manifest_documents`
- `explain_optional_solver_plugin_manifest_load_report`

## Source types and trust labels

Supported source types are `builtin`, `project_local`, `user_local`,
`plugin_package`, `organization_managed`, `explicit_file`, and
`explicit_dict`.

Trust labels are `trusted_builtin`, `reviewed_project`, `user_provided`,
`third_party_plugin`, `organization_managed`, `untrusted`, and `invalid`.
Third-party plugin manifests are not trusted by default. A trust label is a
display and policy signal, not certification.

## Loader inputs

The loader accepts explicit dict input through
`load_optional_solver_plugin_manifest_dict`.

The loader accepts one explicit JSON file path through
`load_optional_solver_plugin_manifest_json`.

The loader does not scan directories, import plugin packages, read package entry
points, or fetch manifests from the network.

## Validation and diagnostics

Manifest payloads are parsed with `parse_optional_solver_manifest_dict` and
validated with `validate_optional_solver_manifest`. Loader diagnostics include
code, severity, category, message, source reference, optional stack id, and
suggested fix.

Diagnostic categories are `schema`, `source`, `trust`, `conflict`, `safety`,
`policy`, and `io`.

## Conflict handling

Duplicate stack ids are diagnosed as conflicts. Built-ins win by default, and
plugin, user, or project manifests cannot override built-in stack ids by
default.

Multiple non-built-in manifests for the same stack id keep the first accepted
manifest and reject later conflicting documents.

## Safety policy checks

The loader rejects manifest text that contains installer commands, executable
code references, bundled-solver claims, or certification claims. These checks
are metadata policy checks only; they do not execute probes, discovery, or
solver commands.

Safety diagnostics cover installer commands, executable code references,
bundled-solver claims, and certification claims.

## Accepted/rejected manifest records

Accepted records include the parsed manifest, source metadata, schema version,
validation report, and non-blocking diagnostics.

Rejected records include source metadata marked invalid, schema version, stack
id when available, raw manifest data, and blocking diagnostics.

Load reports expose accepted records, rejected records, conflicts, and
diagnostics separately.

## Relationship to built-ins

Built-in manifests can be represented as `trusted_builtin` only when explicitly
passed to the loader as built-in source data. Built-ins win by default.

Plugin overrides are forbidden by default.

## Relationship to CLI/GUI

Future CLI and GUI preview gates can display accepted and rejected manifests
from this model. There is no current CLI/GUI behavior change in this gate.

## Relationship to #6~#11

Manifest loading is not validation evidence. Issues `#6` through `#11` remain
open, and skipped-missing remains not pass evidence.

Issues `#6` through `#11` remain open.

## Future gates

- `OSW-EXP-071_OPTIONAL_SOLVER_PLUGIN_MANIFEST_CLI_PREVIEW`
- `OSW-EXP-072_OPTIONAL_SOLVER_PLUGIN_MANIFEST_GUI_DESIGN`
- `OSW-VALID` prepared-machine validation reuse
