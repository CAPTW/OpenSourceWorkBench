# FEASpec CalculiX result write GUI post-write polish

## Status

Experimental GUI polish implemented. This is post-write polish only. It improves
how the existing write dialog displays writer results after an explicit,
already-gated ResultDataset write attempt.

No solver execution. No artifact copying. No open-output shell command. No OS
clipboard integration.

## Release context

- `v0.1.4-rc1` is a public prerelease.
- This implementation is post-release development on `develop`.
- The public release, release tag, release assets, and GitHub issues are not
  edited by this work.

## Package path

- `src/osw/gui/dialogs/feaspec_calculix_result_write_dialog.py`

## Polished displays

The write dialog now exposes clearer post-write display text for:

- written files;
- hashes;
- diagnostics;
- limitations;
- failure details;
- retry guidance.

Written files are shown with file name, payload kind, byte size, and SHA-256
hash when the writer result supplies those fields. Diagnostics are grouped as
blocker, error, warning, and info entries. Limitations preserve writer-provided
limitations and existing view-model safety limitations.

Failure display distinguishes ordinary failed or blocked writer results from
`partial-cleanup-failed`, which tells users to inspect the selected output
directory for temporary files before retrying.

## Copy-ready summaries

The dialog exposes a deterministic plain-text summary as display/accessor only.
The summary includes status, output directory, written file table, diagnostics,
limitations, retry guidance, and the safety boundary.

This is not OS clipboard integration. The dialog does not call clipboard APIs,
does not use `pyperclip`, and does not copy text automatically.

## Disabled and retry text

Disabled reasons still come from the existing write gates and selected-output
state. Missing acknowledgement, missing output directory, unsafe path,
overwrite-required, create-dir-required, and selected-output mismatch states are
still shown without changing write enablement semantics.

Retry guidance is display-only. It recommends refreshing the write plan,
checking the output directory, renewing overwrite/create-dir acknowledgements
when needed, and manually retrying after review. There is no automatic retry.

## Safety boundary

This polish preserves:

- no solver execution;
- no CalculiX `ccx` invocation;
- no artifact copying;
- no open-output shell command;
- no OS clipboard integration;
- no SolverAdapter;
- no runner;
- no subprocess;
- no CLI behavior change;
- no library writer behavior change;
- no ProjectSchema mutation;
- no VLM API;
- no provider credentials;
- no release, tag, asset, or issue mutation.

GUI writes still occur only through the existing library writer after enabled
gates and explicit confirmation. Directory selection remains display/state
selection and does not create directories or write files.

## Relationship to #8

Post-write polish does not validate live `ccx`. Issue `#8` remains open until a
separate prepared-machine live CalculiX validation gate records passing
evidence. A clearer ResultDataset write summary is not live solver validation
and must not close issue `#8`.

## Non-goals

- no solver validation;
- no live `ccx` validation;
- no artifact copying;
- no open-output-folder command;
- no OS clipboard integration;
- no CLI behavior change;
- no library writer behavior change;
- no ResultDataset writer semantic change;
- no SolverAdapter or runner integration;
- no subprocess use;
- no ProjectSchema mutation;
- no VLM API or provider credentials;
- no bundled solver;
- no certification;
- no industrial certification.

External solvers are optional and not bundled.

## Next implementation slices

- [FEASpec CalculiX result write GUI closure review](feaspec_calculix_result_write_gui_closure_review.md)
  closes the experimental review-first ResultDataset write GUI slice as
  complete for standard review-file persistence. It adds no runtime behavior,
  no source writer changes, no solver execution, no live `ccx` validation, and
  no issue `#8` closure.
- `OSW-VALID-004_LIVE_CALCULIX_RUN_GATE_VALIDATION_IF_INSTALLED`
