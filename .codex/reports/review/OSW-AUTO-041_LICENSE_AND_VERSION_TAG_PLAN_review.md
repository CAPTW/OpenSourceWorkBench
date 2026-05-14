# OSW-AUTO-041 License And Version Tag Plan Review

## Review Score

Final score: 95 / 100

Initial review score: 88 / 100, decision `minor amend`. The amend pass fixed
the required review-artifact evidence issue.

## Decision

Approve for merge as release planning documentation.

The final OSW public release remains blocked until maintainers select the final
license and align `LICENSE`, package metadata, README, notices, and release
notes. This review approves the decision packet and version/tag plan; it does
not approve a public release, create a tag, or provide legal advice.

## Scope Review

- The diff is documentation/report-only and stays inside the allowed files.
- No source code, tests, dependency versions, solver adapters, generated release
  artifacts, external solver binaries, remotes, or tags were changed.
- The plan preserves v0.1 scope and avoids claims of industrial certification,
  full solver parity, proprietary CAD direct import, Simulink/`.mlapp`, full
  OpenFOAM UI, or GUI direct solver execution.

## License Decision Safety

- `LICENSE` remains a placeholder and was not replaced.
- `pyproject.toml` remains unchanged with provisional license metadata.
- The plan clearly states final license selection is a maintainer decision.
- The plan recommends a GPL-compatible path without claiming legal finality or
  legal advice.
- Third-party license compatibility and redistribution obligations are recorded
  as release risks and maintainer-review items.

## Version And Tag Safety

- No Git tag was created. `git tag --list "v0.1*"` returned no tags.
- The plan documents PEP 440 package versions `0.1.0rc1` and `0.1.0`.
- The plan documents Git tag names `v0.1.0-rc1` and `v0.1.0`.
- Tag creation remains blocked until P1 license blockers are cleared and a
  dedicated release/tag prompt runs.
- The rollback section only documents local tag deletion for a future prompt and
  explicitly stops before touching remote tags.

## Distribution And Plugin Review

- External solver binaries remain unbundled.
- CalculiX, OpenFOAM, Gmsh, GNU Octave, and SU2 are documented as optional
  external runtime tools.
- Cantera and CoolProp are documented as optional Python dependencies.
- Plugin manifests remain expected to declare license and dependency metadata.
- Manifest validation remains described as non-executing.

## Release Checklist And Risk Review

- `docs/10_release_checklist.md` marks the version/tag plan as `PASS` because
  the planning packet exists.
- Final license, public tag creation, and public announcement remain
  `P1 BLOCKED`.
- P2 default `pytest -q` collection and docs link checker follow-ups remain
  separate; this step does not attempt to fix them.
- `docs/09_risk_register.md` adds version/tag, third-party notice, and external
  solver binary risks.
- `docs/07_decision_log.md` records process ADR-0008 without selecting a final
  license.

## QA Evidence Review

Recorded checks:

- `python tools/qa/run_fast_qa.py`: passed.
- `python tools/qa/run_pre_merge_qa.py`: passed.
- `pytest tests/unit -q`: passed, `216 passed, 3 skipped`.
- `ruff check src tests`: passed.
- `python tools/qa/check_scope_drift.py`: passed.
- `python tools/qa/check_architecture_boundaries.py`: passed.
- `python tools/qa/check_no_solver_artifacts_committed.py`: passed.
- `git diff --check`: passed.
- `git tag --list "v0.1*"`: returned no tags.
- Targeted local markdown link check: passed.
- `python tools/qa/check_git_clean.py`: passed after checkpoint.

Recorded skips:

- `tools/qa/check_docs_links.py` is absent.
- Broad `pytest -q` remains a documented P2 follow-up, not part of this prompt.
- Optional external solver smoke remains environment-specific.

## Required Amend Items

Completed:

- Added this review report.
- Clarified the self-check file list so it does not claim the review report was
  already present before review.
- Updated merge-readiness wording to reference the OSW-AUTO-041 amend and squash
  message.

No further required amend items remain.

## Hard Blocker Review

No hard blockers found:

- No release tag created.
- No public announcement finalized.
- No license finalized without maintainer decision.
- No legal finality claim for third-party compatibility.
- No external solver binaries vendored or committed.
- No secrets, runtime artifacts, destructive Git operations, or scope drift.

## Final Merge Recommendation

Merge the amend branch into `develop` by squash commit with:

`docs(release): define license decision packet and version tag plan`

Next release work should resolve the maintainer license decision and metadata
alignment before any tag or announcement prompt.
