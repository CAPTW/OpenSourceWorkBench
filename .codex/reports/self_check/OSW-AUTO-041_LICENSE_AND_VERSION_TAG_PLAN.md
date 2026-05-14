# OSW-AUTO-041 License And Version Tag Plan Self-Check

## Step ID

OSW-AUTO-041_LICENSE_AND_VERSION_TAG_PLAN

## Branch And Worktree

- Branch: `feature/osw-p13-1-license-version-tag-plan`
- Worktree: `C:\Users\USER\source\repos\_worktrees\osw-p13-1-license-version-tag-plan`
- Base branch: `develop`

## Files Changed

- `docs/13_license_and_version_plan.md`
- `docs/10_release_checklist.md`
- `docs/09_risk_register.md`
- `docs/07_decision_log.md`
- `README.md`
- `.codex/reports/self_check/OSW-AUTO-041_LICENSE_AND_VERSION_TAG_PLAN.md`

The review report is created after this self-check as the review-gate evidence
for the same phase.

## Scope Summary

This step creates a license decision packet and version/tag plan only. It does
not finalize the license, alter `LICENSE`, alter `pyproject.toml`, change source
code, change tests, fix broad pytest collection, implement docs link checking,
vendor external solver binaries, create Git tags, push, or announce a public
release.

## License State Inventory

- `LICENSE`: present but placeholder; explicitly not the final license grant.
- `pyproject.toml`: license metadata present but provisional:
  `GPL-3.0-or-later recommended; final license pending project decision`.
- README: now links `docs/13_license_and_version_plan.md`; no final license
  section was added.
- `docs/10_release_checklist.md`: keeps final license as P1 blocked, marks
  version/tag planning as PASS, and blocks public tag/announcement until final
  license decision and metadata alignment.
- `docs/09_risk_register.md`: now records version/tag, third-party notices, and
  external solver binary bundling risks.
- `docs/07_decision_log.md`: adds a process ADR stating license/tag gates need
  maintainer approval; final license remains pending.
- Plugin manifests: built-in solver/property plugin manifests declare license
  fields, generally `GPL-3.0-or-later`; plugin manifest contract requires a
  `license` field.
- Optional external dependencies: install docs treat CalculiX, OpenFOAM, Gmsh,
  GNU Octave, and SU2 as optional external runtime tools and Cantera/CoolProp as
  optional Python dependencies.

## License Decision Status

Maintainer decision still required. No final legal/license decision was made in
this prompt, and `LICENSE` was not replaced.

## Version / Tag Plan Status

Ready as a planning packet:

- Package release candidate: `0.1.0rc1`
- Package final release: `0.1.0`
- Git release candidate tag: `v0.1.0-rc1`
- Git final tag: `v0.1.0`
- Tag creation remains blocked until P1 license blockers are cleared and a
  dedicated release/tag prompt runs.

## Commands Run

- `git status --short`
- `git branch --show-current`
- `git worktree list`
- `git show-ref --verify --quiet refs/heads/develop`
- `git tag --list "v0.1*"`
- `git worktree add -b feature/osw-p13-1-license-version-tag-plan C:\Users\USER\source\repos\_worktrees\osw-p13-1-license-version-tag-plan develop`
- `rg -n "license|GPL|MIT|BSD|Apache|LGPL|AGPL" README.md docs pyproject.toml LICENSE src tests examples .github`
- `python tools/qa/run_fast_qa.py`
- `python tools/qa/run_pre_merge_qa.py`
- `pytest tests/unit -q`
- `ruff check src tests`
- `python tools/qa/check_scope_drift.py`
- `python tools/qa/check_architecture_boundaries.py`
- `python tools/qa/check_no_solver_artifacts_committed.py`
- `python tools/qa/check_docs_links.py` if present
- `python tools/qa/check_git_clean.py` if present
- `git diff --check`
- Targeted local markdown link check for README and release docs

## Command Results

- `python tools/qa/run_fast_qa.py`: passed.
- `python tools/qa/run_pre_merge_qa.py`: passed.
- `pytest tests/unit -q`: passed, `216 passed, 3 skipped`.
- `ruff check src tests`: passed.
- `python tools/qa/check_scope_drift.py`: passed.
- `python tools/qa/check_architecture_boundaries.py`: passed.
- `python tools/qa/check_no_solver_artifacts_committed.py`: passed.
- `git diff --check`: passed.
- `git tag --list "v0.1*"`: passed with no tags listed.
- Targeted local markdown link check: passed.
- `python tools/qa/check_docs_links.py`: skipped because the file is not
  present.
- `python tools/qa/check_git_clean.py`: present; before checkpoint it reported
  dirty because this step's docs were intentionally uncommitted. It must be
  rerun after checkpoint/merge when cleanliness is expected.

## Skipped Checks

- Docs link checker: skipped because `tools/qa/check_docs_links.py` is absent.
- Broad `pytest -q`: not required for this prompt and remains a documented P2
  follow-up from OSW-AUTO-040.
- External solver smoke: skipped because this prompt must not require optional
  external solver availability.

## Tag Status

No tag was created. `git tag --list "v0.1*"` returned no local v0.1 tags.

## Remaining Risks

- P1: final license selection is still a maintainer decision.
- P1: public release tag and public announcement remain blocked until final
  license, metadata, notices, release notes, and QA are complete.
- P2: default `pytest -q` collection mismatch remains a separate follow-up.
- P2: docs link checker remains a separate follow-up.
- P2: optional external solver executable smoke remains environment-specific.

## Merge Recommendation

Merge the planning packet into `develop` as release documentation evidence. Do
not create release tags or announce public v0.1 until the P1 license and release
metadata blockers are cleared.
