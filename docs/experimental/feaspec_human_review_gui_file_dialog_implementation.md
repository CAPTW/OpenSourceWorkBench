# FEASpec human review GUI file dialog implementation

## 1. Title

FEASpec human review GUI file dialog implementation

## 2. Status

- Experimental review-record JSON file dialog implemented.
- No export bundle write.
- No solver execution.

The GUI can now choose a FEASpec human-review JSON save path through a
mockable `QFileDialog.getSaveFileName` path. The chooser only updates the
existing save plan. It does not write files by itself, and the actual write
still uses the existing human-review JSON save integration.

## 3. Release context

- `v0.1.4-rc1` is a public prerelease.
- This implementation is post-release development on `develop`.
- The public release, release tag, and release assets are unchanged.
- Issue `#8` live CalculiX validation remains separate and open.

## 4. Package path

- GUI module: `src/osw/gui/dialogs/feaspec_human_review_dialog.py`
- Dialog class: `FEASpecHumanReviewDialog`
- File-dialog entry point: `choose_review_record_save_path()`

## 5. Behavior

- Review-record JSON path selection only.
- Default filename is derived from a sanitized source FEASpec id and falls back
  to `feaspec-human-review.human_review.json`.
- Dialog filter is limited to FEASpec human-review JSON records and JSON files.
- Cancel is a no-op and does not change the current save path.
- Missing suffixes are normalized to `.human_review.json`.
- Non-JSON suffixes and `.inp`-derived paths are rejected.
- Existing files require explicit overwrite confirmation.
- Missing parent directories are not created and keep the save action disabled.
- A successful selection updates the view-model save plan and save-action state.

## 6. Save relationship

- Choosing a path does not write.
- Writing still uses the existing save integration.
- Successful save writes one review JSON only.

The dialog provider and overwrite confirmation provider are dependency-injected
so tests can avoid native dialogs and assert behavior deterministically.

## 7. Safety boundary

- No export bundle.
- No `.inp`.
- No result import.
- No run gate.
- No `ccx`.
- No SolverAdapter.
- No runner.
- No subprocess.
- No ProjectSchema mutation.
- No VLM API or credentials.

The file-dialog implementation is not live CalculiX validation and does not
close issue `#8`.

## 8. Testing

Focused GUI tests cover:

- mocked dialog provider;
- cancel no-op;
- deterministic default filename;
- path update and save-action re-evaluation;
- extension normalization and rejection;
- missing parent behavior;
- overwrite reject and accept paths;
- successful `tmp_path` JSON save;
- no `.inp`, export bundle, result import, run gate, SolverAdapter, runner,
  subprocess, ProjectSchema, VLM, or solver side effects.

## 9. Non-goals

- No export bundle chooser.
- No `.inp` writer from the GUI.
- No result import.
- No run gate.
- No CalculiX execution.
- No certification.
- No bundled external solver.
- No dependency install or upgrade.

## 10. Next implementation slices

- `OSW-EXP-027_FEASPEC_CALCULIX_RUN_GATE_INSTALLED_ONLY`
- `OSW-EXP-028_FEASPEC_RESULT_IMPORT_MODEL`
- `OSW-EXP-029_FEASPEC_HUMAN_REVIEW_PROJECT_CONTEXT_INTEGRATION`
