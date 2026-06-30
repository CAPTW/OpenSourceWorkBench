# OSW-AUTO-024 CalculiX ccx Runner Review

Decision: Merge possible
Score: 94/100
Checkpoint: a83417f

## Scope And Files

- `src/osw/solvers/calculix/__init__.py`
- `src/osw/solvers/calculix/ccx_runner.py`
- `tests/unit/test_calculix_runner.py`
- `tests/integration/test_calculix_runner_optional.py`

The change stays inside the CalculiX solver package and runner tests. It adds a
backend `ccx` runner that delegates process execution to `ExternalCommandRunner`
and records known CalculiX artifacts from the case directory.

## Review Score

| Category | Score | Evidence |
| --- | ---: | --- |
| Architecture Compliance | 18/18 | Runner stays under `osw.solvers.calculix` and uses the existing backend runner service. No GUI imports or UI execution path. |
| Test Coverage / Regression Safety | 18/18 | Tests cover fake `ccx` success, stdout/stderr capture, artifact recording, missing executable diagnostics, timeout handling, registry path use, and optional real executable detection. |
| User Workflow Quality | 11/12 | Missing executable messages tell users to install `ccx` or configure `ExecutablePathRegistry`; run artifacts are classified for later reporting. |
| Numerical / Validation Safety | 11/12 | Runner executes prepared decks only and does not add solver validation or result interpretation. |
| Error Handling / Robustness | 10/10 | Missing deck, wrong extension, missing executable, timeout, and nonzero runner status are handled through `RunResult` diagnostics. |
| Security / Script Safety | 10/10 | No script execution path, secrets, network access, or GUI direct subprocess coupling. |
| Documentation | 3/5 | Behavior is covered by tests and docstrings; broader user docs can follow after result import. |
| Scope Discipline | 5/5 | No GUI runner, no full result parser, no unrelated solver domains. |
| Git / Local Environment Safety | 8/10 | Feature worktree is clean, checkpointed, and uses no destructive Git operations. |

## Issues

Critical issues: none
High issues: none
Medium issues: none
Low issues:
- Real `ccx` execution is optional locally; this environment skips because
  `ccx` is not installed.
- The runner records `.dat`, `.frd`, and `.sta` artifacts but does not parse
  them in this phase.

## Commands Run

- `pytest tests\unit -q` -> passed, 134 passed, 1 skipped at baseline.
- `pytest tests\unit\test_calculix_runner.py tests\integration\test_calculix_runner_optional.py -q` -> failed before implementation with missing `osw.solvers.calculix.ccx_runner`.
- `pytest tests\unit\test_calculix_runner.py tests\integration\test_calculix_runner_optional.py -q` -> passed, 4 passed, 1 skipped.
- `ruff check src tests` -> passed.
- `python tools\qa\run_fast_qa.py` -> passed, 138 passed, 1 skipped.
- `python tools\qa\check_scope_drift.py` -> passed.
- `python tools\qa\check_architecture_boundaries.py` -> passed.
- `python tools\qa\check_no_solver_artifacts_committed.py` -> passed.
- `python tools\qa\check_plugin_manifests.py` -> passed.

## Required Fixes

None.

## Required Rerun Commands

- `python tools\qa\run_pre_merge_qa.py`
- `pytest tests\unit\test_calculix_runner.py tests\integration\test_calculix_runner_optional.py -q`

## Generated/Runtime Artifact Check

No solver runtime artifacts are staged. Fake runner files are generated only
under pytest temporary directories.

## Residual Risks

- Result file parsing remains a later reviewed step.
- Real `ccx` behavior should be exercised in an environment where CalculiX is
  installed on PATH or registered explicitly.
