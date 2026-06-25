# Optional solver plugin manifest CLI preview

## Status

Experimental CLI preview implemented.

This gate loads only explicitly supplied optional solver plugin manifest JSON
files through the data-only loader model.

Status boundaries:

- explicit JSON files only
- no plugin package loading
- no directory scan
- no network fetch
- no solver execution
- no dependency installation

## Command name and options

Command:

`optional-solver-plugin-manifest-preview`

Options:

- `--manifest <path>`: explicit optional solver plugin manifest JSON file; may
  be repeated.
- `--format text|json`: output format; default is `text`.
- `--include-builtins`: use built-in optional solver stack ids as trusted
  conflict context.
- `--strict`: return nonzero when manifests are rejected or conflicts are
  present.
- `--include-diagnostics`: include loader diagnostics in text output.
- `--show-policy`: include detailed safety policy disclaimers in text output.

The command does not provide scan, fetch, install, execute, smoke-test, or issue
mutation options.

## Text output behavior

Text output reports accepted, rejected, and conflict counts, followed by accepted
manifest rows, rejected manifest rows, conflict rows, diagnostics, and safety
disclaimers.

Rows include stack id, source type, trust label, and diagnostic codes where
available.

Text output states that plugin manifest presence is not validation evidence and
that third-party/plugin manifests are not trusted by default.

## JSON output behavior

JSON output is parseable and includes:

- `accepted_count`
- `rejected_count`
- `conflict_count`
- `accepted`
- `rejected`
- `conflicts`
- `diagnostics`
- `policy`

The policy block records data-only loading, explicit JSON file scope, no plugin
package loading, no directory scan, no network fetch, no solver execution, no
dependency installation, no issue mutation, and no release mutation.

## Strict mode

Default preview mode exits `0` when manifest files were read and the loader
report contains rejected manifests or conflicts. This keeps invalid or
conflicting manifests reportable as preview results.

Strict mode exits `2` when any manifest is rejected or any conflict is present.

Missing or unreadable files remain command failures and exit `1`.

## Built-in conflict context

`--include-builtins` supplies built-in optional solver stack ids as trusted
conflict context. It does not load manifests from external locations and does
not change built-in manifest behavior.

Built-ins win by default when a plugin/user/project manifest attempts to reuse a
built-in stack id.

## Diagnostics and conflicts

Diagnostics surface loader model codes, severity, category, source reference,
stack id when available, message, and suggested fix where available.

Conflicts are reported separately from rejected manifest records so users can
see which stack id and source relationship caused the rejection.

## Trust labels

Third-party manifests are not trusted by default.

Trust labels are display and policy signals, not certification.

The CLI preview displays source type and trust label for accepted and rejected
manifest records.

## Safety boundary

The command performs data-only loading:

- no plugin code execution
- no plugin package loading
- no directory scan
- no network fetch
- no solver execution
- no install commands
- no issue mutation
- no release mutation

The preview does not import optional solver packages and does not run discovery
or active smoke validation.

## Relationship to #6~#11

The preview is not validation evidence. Issues `#6` through `#11` remain open,
and skipped-missing remains not pass evidence.

Plugin manifest previews cannot close issues or replace prepared-machine
validation.

## Future gates

- `OSW-EXP-072_OPTIONAL_SOLVER_PLUGIN_MANIFEST_GUI_DESIGN`
- `OSW-EXP-073_OPTIONAL_SOLVER_PLUGIN_MANIFEST_EXPLICIT_IMPORT_GUI`
  remains the earlier explicit-import GUI follow-up name; the GUI work is now
  split into the view-model, implementation, and activation-design gates below.
- `OSW-EXP-073_OPTIONAL_SOLVER_PLUGIN_MANIFEST_GUI_VIEWMODEL`
- `OSW-EXP-074_OPTIONAL_SOLVER_PLUGIN_MANIFEST_GUI_IMPLEMENTATION`
- `OSW-EXP-075_OPTIONAL_SOLVER_PLUGIN_MANIFEST_ACTIVATION_DESIGN`
- `OSW-VALID` prepared-machine validation reuse

## GUI design follow-up

[Optional solver plugin manifest GUI design](optional_solver_plugin_manifest_gui_design.md)
defines the future review-focused GUI workflow for the same loader reports.
The design keeps GUI preview separate from activation, directory scanning,
plugin package loading, network fetch, solver execution, dependency
installation, issue mutation, release mutation, validation-pass claims,
issue-closure claims, external-solver bundling claims, and certification
claims.
