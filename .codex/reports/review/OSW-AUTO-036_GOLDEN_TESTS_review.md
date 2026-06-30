# Review: OSW-AUTO-036_GOLDEN_TESTS

## Review Score

96 / 100

## Decision

approve

## Scope Review

- Changed files are limited to the required Codex reports, `docs/04_validation_matrix.md`,
  `tests/AGENTS.md`, and `tests/golden/**`.
- No product implementation, solver adapter, GUI, runner, dependency, or example
  executable asset files changed.
- No external solver execution is introduced.

## Architecture Review

- Golden helpers live under `tests/golden` and are used only by tests.
- Product code remains independent of test helpers.
- The plugin manifest health golden builds a `PluginManifest` and health record
  from manifest metadata only; it does not import or execute plugin entry-point
  code.

## Test Coverage / Regression Safety

- The golden suite now covers generated CalculiX input decks, OpenFOAM cavity
  and duct templates, mesh export summary JSON, report required sections, SU2
  config output, plugin manifest health output, and helper behavior.
- Text comparisons normalize line endings, trailing whitespace, timestamps, and
  caller-provided volatile paths.
- JSON comparisons canonicalize sort order and formatting before diffing.
- Diff output uses unified diffs with expected/actual labels.

## Documentation / Policy Review

- `tests/AGENTS.md` documents the golden update policy: use shared helpers,
  normalize volatile content, update fixtures only for intentional contract
  changes, review diffs, and do not auto-regenerate or execute external solvers.
- `docs/04_validation_matrix.md` records golden fixture evidence in the
  bootstrap/guardrail evidence table.

## Wording / Safety Review

- No industrial certification, production validation, native commercial CAD, or
  full solver coverage claims were added.
- The validation matrix continues to frame evidence as v0.1 educational and
  research-oriented.

## QA Evidence Review

- `pytest tests/golden -q`: passed, `10 passed`.
- `pytest tests/unit -q`: passed, `202 passed, 3 skipped`.
- `ruff check src tests`: passed.
- `python tools/qa/run_fast_qa.py`: passed.
- `python tools/qa/check_scope_drift.py`: passed.
- `python tools/qa/check_architecture_boundaries.py`: passed.
- `python tools/qa/check_no_solver_artifacts_committed.py`: passed.
- `python tools/qa/check_plugin_manifests.py`: passed.
- `git diff --check`: passed.

## Required Amend Items

None.

## Final Merge Recommendation

Merge `feature/osw-p11-2-golden-tests` into `develop` with squash commit
message:

`test(golden): add generator and parser golden tests`
