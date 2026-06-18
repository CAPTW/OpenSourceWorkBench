# FEASpec human review GUI file dialog design

## 1. Title

FEASpec human review GUI file dialog design

## 2. Status

- Design-only.
- No file dialog implementation.
- No solver execution.

This document designs a future file-dialog path chooser for saving one
FEASpec human-review JSON record. This gate does not add `QFileDialog` usage,
does not modify GUI source, does not write files from the GUI, does not import
results, does not implement a run gate, and does not execute solvers.

## 3. Release context

- `v0.1.4-rc1` is a public prerelease.
- This design is post-release development on `develop`.
- The public release, release tag, and release assets are unchanged by this
  design gate.

## 4. Relationship to existing layers

The future file-dialog behavior is downstream of existing FEASpec human review
layers:

- FEASpec human review GUI dialog.
- FEASpec human review GUI save integration.
- Human review record IO.
- View-model save plan.

The file dialog should only choose a path. The actual save must continue to use
the existing save integration, which validates the record preview and writes
one review-record JSON file to an explicit path.

## 5. Existing GUI file-dialog patterns

Read-only inspection found these existing GUI patterns:

- `ExecutablePathDialog` uses `QFileDialog.getOpenFileName` to select an
  executable path and then stores the selected string in a table cell.
- `PluginManagerDialog` uses `QFileDialog.getExistingDirectory` for local
  plugin folders and `QFileDialog.getOpenFileName` for ZIP archives before
  handing the path to explicit installer methods.
- The legacy `PluginManagerDialog` wrapper uses the same folder/ZIP browse
  pattern for managed local plugin install paths.
- `MatPreviewPanel` uses `QFileDialog.getSaveFileName` for explicit CSV export
  when the caller does not provide an output path.

This gate inspected those patterns only. It does not reuse or add file-dialog
source code.

## 6. File-dialog goals

- Choose review record JSON save path.
- Keep explicit user intent.
- Preserve overwrite guard.
- Preserve parent-dir behavior.
- No export bundle write.
- No solver execution.

The file dialog is path selection only. It must not write export bundles,
write `.inp` files, import results, request runs, call solver adapters, or run
external commands.

## 7. Entry points

Future entry points may include:

- the existing Save Record button when no save path is configured;
- an optional Choose Path button beside the save status row;
- a future menu/action if OSW adds a human-review workflow menu.

All entry points must converge on the same selected path state and then
re-evaluate the existing save-plan disabled reasons.

## 8. Default filename strategy

The suggested filename should be deterministic and safe:

- start from the source FEASpec id when it is present and safe;
- sanitize unsafe characters before using the id in a filename;
- strip path separators, drive prefixes, wildcard characters, control
  characters, and leading/trailing whitespace;
- collapse repeated separators to a single hyphen;
- append the suffix `.human_review.json`;
- use the fallback `feaspec-human-review.human_review.json` when the source id
  is missing or sanitizes to an empty string.

The source FEASpec id must never be treated as a directory path.

## 9. Filter/extension policy

- JSON files only.
- The suggested extension is `.human_review.json`.
- A future implementation may normalize a missing extension by appending
  `.human_review.json` before updating the save plan.
- If a selected path has a non-JSON extension, the implementation should reject
  it with a visible message rather than silently writing a differently typed
  file.

The dialog filter should be narrow, such as
`Human review JSON (*.human_review.json *.json)`.

## 10. Directory policy

- The initial directory should come from the current project directory or an
  explicit last-used review directory only in a future settings gate.
- No hidden parent creation.
- Parent directories must already exist unless a later explicit create-dir
  option is designed and implemented.
- A canceled directory or save path choice is a no-op.

The file dialog must not invent project directories or create hidden output
folders.

## 11. Overwrite policy

- Existing target prompts user.
- There is no silent overwrite.
- User acceptance maps to the existing save integration overwrite flag.
- User rejection keeps the existing save path and save-plan state unchanged.

The overwrite confirmation should happen before calling the existing save
integration. The JSON IO helper remains the final overwrite guard.

## 12. Path safety

- No traversal.
- No drive/path injection through filename.
- No wildcard/control chars.
- No system-wide writes without user choice.
- No automatic selection of protected or broad system locations.

The selected path must be normalized only for validation and display. The
implementation should reject unsafe derived filenames instead of interpreting
untrusted FEASpec ids as path fragments.

## 13. Save-plan integration

- Selected path updates view-model/dialog save path.
- Save button re-evaluates disabled reason.
- Actual write still uses existing save integration.

The future dialog should call the existing `set_save_path` and
`set_overwrite_enabled` style hooks rather than creating a second save path
state. All save availability and disabled reason display should remain
view-model driven.

## 14. Error handling

- Canceled dialog is no-op.
- Invalid path shows message.
- Failed write shows message.

Path validation errors should be shown near the save controls and should also
remain available through testable status/error state. Failed writes should
reuse the existing save integration status behavior.

## 15. UX copy

Future user-facing copy should state:

- saves review record only;
- does not write export bundle;
- does not run solver;
- no bundled solver;
- no certification;
- no industrial certification.

The dialog must not imply that selecting a review JSON path approves export,
imports results, validates local `ccx`, or authorizes solver execution.

## 16. Test plan for future implementation

Future implementation tests should cover:

- dialog cancel;
- selected safe path;
- unsafe filename;
- missing extension;
- overwrite prompt accept/reject;
- no parent creation;
- no solver/export side effects.

Additional guardrail tests should verify that file-dialog implementation stays
inside the GUI layer, still writes only human-review JSON through the existing
save integration, and does not introduce result import, run gates,
SolverAdapter, runner, subprocess, ProjectSchema mutation, or VLM paths.

## 17. Non-goals

- No implementation.
- No `QFileDialog` in this gate.
- No result import.
- No run gate.
- No solver execution.
- No export bundle write.
- No `.inp` write.
- No SolverAdapter or runner integration.
- No subprocess or external command invocation.
- No ProjectSchema mutation.
- No VLM API or credentials.
- No dependency install or upgrade.
- No release, tag, asset, or issue mutation.
- No industrial certification.

## 18. Next implementation slices

- `OSW-EXP-026_FEASPEC_HUMAN_REVIEW_GUI_FILE_DIALOG_IMPLEMENTATION`
- `OSW-EXP-027_FEASPEC_CALCULIX_RUN_GATE_INSTALLED_ONLY`
- `OSW-EXP-028_FEASPEC_RESULT_IMPORT_MODEL`
