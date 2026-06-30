# OSW-AUTO-059 Release Version Recovery Decision Self-Check

## Decision

- Step: OSW-AUTO-059_RELEASE_VERSION_RECOVERY_DECISION
- Decision: SELECT_PATCH_RELEASE_V0_1_1
- Current develop commit before this docs-only change: `50e606b869e7a9a9c2e0275c32470c4d011a94a1`
- Current package version: `0.1.0`
- Expected source license: `GPL-3.0-or-later`
- Selected next candidate: package `0.1.1rc1`, tag `v0.1.1-rc1`
- Selected next final: package `0.1.1`, tag `v0.1.1`

## Tag Preservation Evidence

- `v0.1.0`: annotated tag object `tag`, peeled target `da8728adf679314442755ed781c1dd57d1c6ed27`
- `v0.1.0-rc1`: annotated tag object `tag`, peeled target `29c5c8bec8df30c7f7be72fc9be5e5409794968e`
- `v0.1.0-rc2`: annotated tag object `tag`, peeled target `684dc6138d4257564bbcdd176a9d5ed311a7316d`
- `v0.1.0-rc3`: annotated tag object `tag`, peeled target `dc7df75c53f0a4acb0a1ccf33d97c01ffdde4b16`
- No tag was created, deleted, moved, retargeted, recreated, overwritten, or pushed by this prompt.
- Existing local `v0.1.0` is preserved as historical local-only evidence and is not recommended for publication as the current release because `develop` is ahead of it.

## Source-Install Retest Evidence

External report: `C:/Users/USER/source/repos/_test_runs/osw-source-run-retest-058/OSW-AUTO-058_SOURCE_INSTALL_UAT_RETEST_AFTER_FIX_report.md`

- Retest status: passed
- Editable install: full extras plus dev install succeeded
- Package version: `0.1.0`
- License: `GPL-3.0-or-later`
- Ruff: `0.15.13`, passed
- UP042 recurrence: no
- Default pytest recurrence of OSW-AUTO-056 failures: no
- Default pytest: `290 passed, 5 skipped, 2 warnings`
- Importlib pytest: `290 passed, 5 skipped, 2 warnings`
- Fast QA: passed
- Pre-merge QA: passed
- GUI launch: launched offscreen
- P0 blockers: none
- P1 blockers: none
- P2 follow-ups: optional solver executables missing locally, GUI interaction not fully automated, live external solver runs not performed, external URL freshness out of scope, packaging artifacts not built, historical `v0.1.0` is not publishable as-is.

## Docs Changed

- `docs/07_decision_log.md`: added ADR-0018 recording the source-install recovery decision and selected patch path.
- `docs/09_risk_register.md`: reduced source-install QA risk after retest and documented historical tag and tag-mutation risks.
- `docs/10_release_checklist.md`: recorded source-install UAT retest PASS, blocked public `v0.1.0` publish, and added pending `0.1.1rc1` candidate row.
- `docs/13_license_and_version_plan.md`: recorded historical `v0.1.0`, current `develop` ahead of it, and the next `0.1.1rc1` -> `0.1.1` path.

## Checks Run On Feature Branch

- `python -m osw.cli --version`: passed, `osw 0.1.0`
- `python -m osw.cli doctor`: passed with optional dependency diagnostics
- `python tools/qa/check_docs_links.py`: passed, 30 Markdown files and 59 local links checked
- `python tools/qa/check_duplicate_test_basenames.py`: passed
- `python tools/qa/check_release_metadata.py --expected-version 0.1.0 --expected-source-license GPL-3.0-or-later --allowed-prior-rc-tag v0.1.0-rc1 --allowed-prior-rc-target 29c5c8bec8df30c7f7be72fc9be5e5409794968e --allowed-prior-rc-tag v0.1.0-rc2 --allowed-prior-rc-target 684dc6138d4257564bbcdd176a9d5ed311a7316d --allowed-prior-rc-tag v0.1.0-rc3 --allowed-prior-rc-target dc7df75c53f0a4acb0a1ccf33d97c01ffdde4b16 --expected-final-tag v0.1.0 --expected-final-target da8728adf679314442755ed781c1dd57d1c6ed27 --require-annotated-final-tag`: passed
- `ruff check src tests`: passed
- `pytest -q`: passed, 276 passed, 19 skipped
- `python tools/qa/run_fast_qa.py`: passed, unit subrun 258 passed, 3 skipped
- `python tools/qa/run_pre_merge_qa.py`: passed, unit subrun 258 passed, 3 skipped
- `python tools/qa/check_no_solver_artifacts_committed.py`: passed
- `git diff --check`: passed
- `git status --short`: only intentional docs/report changes before staging

## Safety Confirmations

- No package version bump was performed.
- No license metadata was changed.
- No source, test, solver adapter, GUI behavior, release artifact, external solver binary, or public announcement file was changed.
- No push occurred.
- No tag operation occurred.

## Next Prompt Recommendation

Run OSW-AUTO-060_PATCH_V0_1_1_RC1_PREP to prepare `0.1.1rc1` metadata and the `v0.1.1-rc1` local tag gate path.
