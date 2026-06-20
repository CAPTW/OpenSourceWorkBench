# FEASpec CalculiX result write GUI writer integration

Status: experimental GUI writer integration implemented. Final confirmation
required. Acknowledgements required. No solver execution. The dialog keeps
directory-only `QFileDialog` directory selection, enables the write action only
after the review gates pass, and delegates persistence to the existing library
writer.

## Release context

- `v0.1.4-rc1` is a public prerelease.
- This implementation is post-release development on `develop`.
- The public release, release tag, release assets, and GitHub issues are not
  edited by this work.

## Package path

- `src/osw/gui/dialogs/feaspec_calculix_result_write_dialog.py`

## Dialog input

The dialog accepts `FEASpecCalculiXResultWriteViewModel`, an optional mockable
output-directory chooser, an injectable ResultDataset writer, and an injectable
confirmation callback for tests. Production use defaults to the existing
library writer. The dialog does not accept a solver adapter, runner, CLI
command, ProjectSchema mutator, artifact-copy provider, VLM provider, or
credential provider.

QFileDialog directory selection remains directory-only and only updates the
reviewed selected-output state.

## Write enablement

The write action is enabled only when the current view-model and selected
output state satisfy all gates:

- import, draft mapping, write plan, and schema payload are ready;
- limitations and review-required acknowledgements are present;
- overwrite acknowledgement is present when the reviewed target collides;
- create-directory acknowledgement is present when the write plan requires it;
- the selected output directory matches the reviewed write-plan target;
- callable write-plan and schema payload objects are present.

Missing or stale evidence keeps the action disabled with visible reasons. A
selected output directory alone does not authorize a write.

## Confirmation flow

Before any writer call, the dialog requires explicit confirmation text with the selected
output directory, reviewed target directory, overwrite state, and planned
standard ResultDataset files. Canceling confirmation is a no-op. Accepting
confirmation authorizes one bounded call to the existing library writer.

## Writer boundary

The GUI writer boundary is deliberately narrow:

- actual ResultDataset file write is delegated to
  `write_calculix_result_dataset`;
- the writer is called at most once per accepted write attempt;
- written-file names, sizes, SHA-256 hashes, diagnostics, and status are shown
  from the writer result;
- successful writes disable repeat writes in the same dialog session;
- writer failures and partial-cleanup failures are surfaced in the result
  panel and remain retryable after review.

The dialog does not implement raw JSON file writes, atomic-write internals, or
library writer policy. Those remain in the existing writer layer.

## Post-write display polish

[FEASpec CalculiX result write GUI post-write polish](feaspec_calculix_result_write_gui_post_write_polish.md)
extends this dialog's result display with a written-file table, payload kind,
byte size, SHA-256 hash, grouped diagnostics, grouped limitations, failure
details, retry guidance, and a deterministic copy-ready plain-text summary.
That polish is display/accessor only: no OS clipboard integration, no
open-output shell command, no artifact copying, no new writer invocation path,
no CLI behavior change, and no library writer behavior change.

## Safety boundary

This GUI integration preserves:

- directory-only `QFileDialog` selection;
- selected output directory review before write;
- actual ResultDataset file write only through the existing library writer;
- no original solver artifact copying;
- no open-output-folder shell command;
- no CLI behavior change;
- no library writer behavior change;
- no solver execution;
- no subprocess;
- no SolverAdapter;
- no runner;
- no ProjectSchema mutation;
- no VLM API;
- no provider credentials;
- no release, tag, asset, or issue mutation.

External solvers are optional and not bundled. A successful ResultDataset write
is persistence evidence only; it is not engineering correctness, live solver
validation, or certification evidence.

## Relationship to issue #8

The GUI writer integration does not validate live `ccx`. Issue `#8` remains
open until a separate prepared-machine live CalculiX validation gate records
passing evidence. Writing reviewed ResultDataset files must not close issue
`#8`.

## Test strategy

GUI tests cover:

- enabled write only when gates are satisfied;
- disabled write with missing acknowledgements, overwrite acknowledgement, or
  create-directory acknowledgement;
- confirmation accepted and canceled;
- injected writer success and failure;
- real library writer smoke under pytest `tmp_path`;
- selected output mismatch blocking writer calls;
- no artifact copying;
- no solver execution, SolverAdapter, runner, subprocess, ProjectSchema, VLM,
  release, tag, asset, or issue mutation paths.

Tests use generated `tmp_path` result and output directories. No tracked solver
output fixtures are added by this gate.

## Non-goals

- no solver execution;
- no live `ccx` validation;
- no artifact copying;
- no open-output-folder command;
- no CLI behavior change;
- no library writer behavior change;
- no raw writer implementation in GUI code;
- no ResultDataset schema or write-plan model change;
- no SolverAdapter or runner integration;
- no subprocess use;
- no ProjectSchema mutation;
- no VLM API or provider credentials;
- no bundled solver;
- no certification;
- no industrial certification.

## Next implementation slices

- `OSW-EXP-052_FEASPEC_RESULT_IMPORT_WRITE_GUI_POST_WRITE_POLISH`
- [FEASpec CalculiX result write GUI closure review](feaspec_calculix_result_write_gui_closure_review.md)
  records the completed experimental GUI write flow after post-write polish.
  The closure review is docs/tests only and does not change GUI writer
  behavior, library writer behavior, solver execution policy, or issue `#8`
  state.
- `OSW-VALID-004_LIVE_CALCULIX_RUN_GATE_VALIDATION_IF_INSTALLED`
