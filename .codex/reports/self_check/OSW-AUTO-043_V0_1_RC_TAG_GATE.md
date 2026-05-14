# OSW-AUTO-043 Self-Check

## Step ID

OSW-AUTO-043_V0_1_RC_TAG_GATE

## Branch / Worktree

- Branch: `feature/osw-p13-3-v0-1-rc-tag-gate`
- Worktree: `C:\Users\USER\source\repos\_worktrees\osw-p13-3-v0-1-rc-tag-gate`
- Base branch: `develop`

## Release Target

- Target package version: `0.1.0rc1`
- Target RC tag name: `v0.1.0-rc1`
- Final package version: `0.1.0`
- Final tag name: `v0.1.0`
- Expected source license: `GPL-3.0-or-later`
- Target commit before tag: not known at self-check time; record after squash
  merge and post-merge pre-tag QA.

## License And Metadata Evidence

- `pyproject.toml` package version is `0.1.0rc1`.
- `src/osw/__init__.py` package version is `0.1.0rc1`.
- `python -m osw.cli --version` reports `osw 0.1.0rc1`.
- `LICENSE` contains GNU GPL version 3 text and no placeholder wording.
- `pyproject.toml` license metadata is `GPL-3.0-or-later`.
- README License section records `GPL-3.0-or-later`.
- `docs/13_license_and_version_plan.md` records the maintainer
  `GPL-3.0-or-later` decision, version/tag plan, and no-push policy.
- `CHANGELOG.md` contains `0.1.0rc1` and `v0.1.0-rc1` release-candidate notes.
- `docs/14_third_party_notices.md` exists and keeps external solver binaries
  unbundled by default.
- No `v0.1*` tags existed before review.

## Files Changed

- `docs/10_release_checklist.md`
- `docs/09_risk_register.md`
- `docs/07_decision_log.md`
- `.codex/reports/self_check/OSW-AUTO-043_V0_1_RC_TAG_GATE.md`
- `.codex/reports/review/OSW-AUTO-043_V0_1_RC_TAG_GATE_review.md` after review

## QA Commands And Results

- `git status --short`: dirty only with intentional docs/report changes.
- `git tag --list "v0.1*"`: no tags.
- `python -m osw.cli --version`: `osw 0.1.0rc1`.
- `python -m osw.cli doctor`: passed; optional modules reported as available
  or missing without failing; external solver execution disabled.
- `python tools/qa/check_release_metadata.py`: passed.
- `python tools/qa/run_fast_qa.py`: passed.
- `python tools/qa/run_pre_merge_qa.py`: passed.
- `python tools/qa/check_scope_drift.py`: passed.
- `python tools/qa/check_architecture_boundaries.py`: passed.
- `python tools/qa/check_no_solver_artifacts_committed.py`: passed.
- `ruff check src tests`: passed.
- `pytest tests/unit -q`: `218 passed, 3 skipped`.
- `pytest -q --import-mode=importlib`: `236 passed, 19 skipped`.
- `pytest tests/integration -q -m "not external_solver"`:
  `4 passed, 3 skipped, 3 deselected`.
- `pytest tests/golden -q`: `10 passed`.
- `pytest tests/validation -q`: `4 passed`.
- `git diff --check`: passed.
- `python tools/qa/check_git_clean.py --allow-dirty`: reported dirty only for
  intentional files.
- `python tools/qa/check_docs_links.py`: skipped because the tool is not
  present.
- `pytest -q`: failed only with the documented P2 duplicate basename import
  mismatch between `tests/gui/test_plugin_manager_dialog.py` and
  `tests/unit/test_plugin_manager_dialog.py`.

## Known P2 Exceptions

- Default `pytest -q`: non-blocking P2 exception because the failure is exactly
  the already documented duplicate module basename collection mismatch and all
  targeted suites passed.
- Docs link checker: `tools/qa/check_docs_links.py` is absent and remains the
  documented P2 placeholder; it was not implemented in this step.

## Tag Safety

- No tag was created before review.
- `v0.1.0` was not created.
- No push occurred.
- No release artifacts, external solver binaries, solver runtime outputs,
  `dist/`, `build/`, or `wheelhouse/` paths are staged.

## Remaining Risks

- `v0.1.0-rc1` must be created only after squash merge and post-merge pre-tag
  checks pass on clean `develop`.
- Local RC tag remains non-public until a maintainer explicitly approves a push.
- Final `v0.1.0` tag requires a separate final release gate.
- Third-party notices remain a maintainer-review draft and are not legal advice.

## Merge / Tag Recommendation

Proceed to review. If review score is at least 90 and no hard blockers remain,
squash merge to `develop`, run post-merge pre-tag checks, and create local
annotated `v0.1.0-rc1` only if those checks pass.

## Next Prompt Recommendation

After local RC tag creation, the next prompt should be a maintainer-controlled
RC push/release-publication decision prompt. If the RC is rejected, use a
focused recovery prompt to record why and plan a later RC.
