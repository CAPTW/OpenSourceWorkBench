# Optional solver plugin manifest loading design

## Status

Design-only.

This gate adds:

- optional solver plugin manifest loading design
- future manifest source categories
- future trust labels and diagnostics
- future CLI/GUI display implications

This gate does not add:

- no plugin loading implementation
- no plugin code execution
- no filesystem plugin scan
- no network marketplace integration
- no solver execution
- no external solver command execution
- no dependency installation
- no solver installation
- no issue mutation
- no release mutation

## Current baseline

- `v0.1.5-rc1` public prerelease is the current public release.
- v0.1.5-rc1 public prerelease state is retained for this design gate.
- Built-in optional solver manifests exist.
- Passive discovery service exists.
- CLI doctor preview exists.
- GUI health panel/refresh/export exist.
- `#6~#11 open/skipped-missing`.
- Issues `#6` through `#11` remain open.
- OSW-VALID-005 classified the current machine as `skipped-missing` for the
  target optional solver and science stacks.
- External solvers are not bundled.

## Purpose

The future plugin manifest loading model should allow plugins to contribute
optional solver manifest metadata while keeping the same declarative safety
boundary as the built-in manifests.

The purpose is to:

- allow future plugins to contribute optional solver manifest metadata
- keep built-in and plugin manifests schema-compatible
- provide trust labels and diagnostics
- improve optional stack guidance without bundling solvers
- keep CLI/GUI discovery surfaces honest about source and trust

## Manifest source categories

Future manifest source categories should be explicit and visible:

- built-in core manifests
- project-local manifests
- user-local manifests
- plugin package manifests
- future organization-managed manifests
- no network marketplace in initial scope

Built-in core manifests are packaged with OSW source. Project-local and
user-local manifests are files chosen by the user or project policy in a future
gate. Plugin package manifests are third-party metadata shipped with plugin
packages, but loading the metadata must not execute plugin package code.
Organization-managed manifests are future policy-controlled inputs, not a
network marketplace.

## Trust model

Trust labels are display metadata, not proof of engineering correctness.

Initial labels:

- built-in trusted
- project-local reviewed
- user-local user-provided
- plugin-provided third-party
- untrusted/invalid blocked

Rules:

- trust label must be displayed in CLI/GUI
- trust label is not certification
- plugin-provided third-party manifests are not trusted by default
- untrusted or invalid manifests are blocked from discovery inputs
- trusted display status does not mean validation success
- trust metadata must be preserved in diagnostics and exported summaries

## Loading boundary

Future loading must remain data-only:

- load manifest data only
- never execute plugin code during manifest loading
- never run install commands
- never run solver commands
- never import optional solver packages as loading side effect
- schema validate before use
- invalid manifests are quarantined/diagnostic only

The future loader should accept only accepted manifest records into discovery
and health-panel builders. Quarantined manifests may be displayed as invalid
records with diagnostics, but they must not be used for discovery refresh,
validation planning, or issue policy.

## Candidate file formats

Initial future format:

- JSON first

Future formats may be considered only after a separate policy and dependency
review:

- optional future TOML/YAML only if dependencies/policy allow
- no executable manifest format
- schema version required

JSON keeps the first implementation small, deterministic, and aligned with the
existing manifest JSON helpers. Executable formats, scripts, Python modules,
notebooks, shell snippets, and installer recipes are not manifest formats.

## Candidate locations

Future candidate locations should be opt-in and bounded:

- built-in package resources
- project `.osw/optional_solvers/` future path
- user config directory future path
- plugin package metadata future path
- explicit file path future CLI/GUI import
- safe path/traversal checks

The first implementation gate should not scan arbitrary plugin directories.
Any project-local or user-local path must be normalized, constrained to the
declared source category, and rejected if traversal, symlink confusion, or
unexpected parent creation would be required.

## Conflict handling

Conflicts should produce diagnostics instead of silent overrides:

- duplicate stack id
- plugin overrides forbidden by default
- explicit override policy future-only
- multiple manifests for same stack get diagnostics
- built-ins win by default

Built-in manifests remain the default source for known stack ids. A future
override policy would need an explicit user or organization trust decision and
must still preserve the original built-in manifest in diagnostics.

## Validation diagnostics

Future validation should surface stable diagnostic codes for at least:

- schema invalid
- unsupported schema version
- duplicate stack id
- unsafe path
- untrusted source
- missing trust metadata
- installer command present
- executable code reference present
- bundled-solver claim present
- certification claim present

Diagnostics should include severity, source category, source label, manifest
path or package metadata label when safe, field path, and suggested fix.
Diagnostics must avoid full private paths unless the user explicitly opts in to
full-path display in a later gate.

## CLI/GUI display implications

Future CLI and GUI surfaces should:

- list source and trust label
- show invalid manifests separately
- distinguish built-in and plugin manifests
- show user guidance but no install/run buttons
- discovery/refresh consumes only accepted manifests

The CLI doctor preview, GUI health panel, GUI export summary, and GUI passive
refresh should continue to distinguish setup evidence from validation evidence.
Plugin manifest source and trust labels should appear near stack identity,
diagnostics, and export summaries so users can tell whether a row came from
OSW core metadata or third-party metadata.

## CLI preview follow-up

`OSW-EXP-071_OPTIONAL_SOLVER_PLUGIN_MANIFEST_CLI_PREVIEW` implements the
design's CLI preview slice for explicit JSON files. It displays source type,
trust label, accepted/rejected status, diagnostics, and conflicts while keeping
plugin package loading, directory scanning, network fetch, solver execution,
dependency installation, issue mutation, release mutation, validation-pass
claims, issue-closure claims, bundled-solver claims, and certification claims
out of scope.

## Privacy/security

The model must preserve the current optional solver privacy boundary:

- no telemetry
- no credentials
- no network fetch in initial scope
- no environment dumping
- no execution from manifest
- clear warning for third-party manifests

Manifest loading must never collect provider secrets, package-manager tokens,
private environment variable values, raw PATH values, raw solver outputs, or
validation artifacts. Third-party manifests should be displayed with a warning
that they are metadata from outside OSW core and are not trusted by default.

## Relationship to validation

Manifests guide discovery and future validation planning. They are not
validation evidence.

- manifests guide discovery and future validation
- plugin manifest presence is not validation evidence
- skipped-missing remains not pass
- issue closure requires separate validation/closure gates

Issues `#6` through `#11` remain open until prepared-machine validation and a
separate explicit issue-closure gate provide sufficient evidence.

## Non-goals

- no implementation in this gate
- no plugin code execution
- no package manager integration
- no network marketplace
- no solver bundling
- no solver execution
- no issue mutation
- no release mutation
- no dependency installation
- no plugin directory scanning
- no CLI source mutation
- no GUI source mutation

## Loader model follow-up

`OSW-EXP-070_OPTIONAL_SOLVER_PLUGIN_MANIFEST_LOADER_MODEL` implements the first
data-only follow-up in
[Optional solver plugin manifest loader model](optional_solver_plugin_manifest_loader_model.md).
That model accepts only explicit dict input and explicit JSON files, reuses the
declarative optional solver manifest validation path, attaches source/trust
labels, detects duplicate stack conflicts, and quarantines unsafe or invalid
records as diagnostics. It adds no CLI/GUI behavior change, package import,
directory scan, network fetch, solver execution, dependency installation,
issue mutation, release mutation, validation-pass claim, issue-closure claim,
bundled-solver claim, or certification claim.

## Future gates

- `OSW-EXP-070_OPTIONAL_SOLVER_PLUGIN_MANIFEST_LOADER_MODEL` - completed as a
  data-only explicit dict/JSON loader model in
  [Optional solver plugin manifest loader model](optional_solver_plugin_manifest_loader_model.md).
- `OSW-EXP-071_OPTIONAL_SOLVER_PLUGIN_MANIFEST_CLI_PREVIEW`
- `OSW-EXP-072_OPTIONAL_SOLVER_PLUGIN_MANIFEST_GUI_DESIGN`
- `OSW-VALID` prepared-machine validation reuse
