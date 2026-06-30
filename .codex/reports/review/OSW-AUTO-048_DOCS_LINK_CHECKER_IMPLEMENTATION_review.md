# OSW-AUTO-048 Docs Link Checker Review

Decision: Merge possible after amend

Score: 98/100

Checkpoint: `9b479ee0ba7084312d14aedfdfc680ec0fc6cb7f`

Amend branch: `amend/osw-p14-2-docs-link-checker-review-01`

## Review Scope

Reviewed the OSW-AUTO-048 branch against the prompt hard blockers,
`docs/06_review_protocol.md`, and the repository AGENTS rules. The change adds
a local-only Markdown documentation link checker, focused temp-directory tests,
fast/pre-merge QA wiring, and narrow release-status documentation updates.

## Initial Review Findings

The first review scored 88/100 with two medium required fixes:

- Reference-style usages such as `[Doc][missing]` were not checked, so an
  undefined reference usage could pass with no local link checked.
- Inline local links containing a balanced parenthesis group, such as
  `docs/page_(draft).md`, could be truncated and false-fail.

Both findings were fixed in the amend branch
`amend/osw-p14-2-docs-link-checker-review-01`.

## Score

| Category | Score | Notes |
| --- | ---: | --- |
| Architecture Compliance | 8/8 | QA tool stays under `tools/qa`, uses stdlib only, and does not touch product source or solver adapters. |
| Test Coverage / Regression Safety | 24/24 | Tests cover required local files, anchors, fences, external classification, unsupported schemes, images, definitions/usages, URL decoding, traversal, Windows-style paths, JSON payload serialization, diagnostics, undefined references, and balanced parentheses. |
| User Workflow Quality | 6/6 | CLI output includes file count, local link count, skipped external count, and clear file/line/reason failures. |
| Numerical / Validation Safety | 4/4 | No numerical behavior, validation math, or solver execution changed. |
| Error Handling / Robustness | 12/12 | Handles missing files, missing anchors, absolute paths, traversal, unsupported schemes, undefined reference usages, balanced parentheses, and directory anchors. |
| Security / Script Safety | 8/8 | No network access by default, no file mutation while checking, no external solver or script execution. |
| Documentation / Release Checklist | 16/16 | Release checklist marks docs-link checker resolved and records rc1/rc2 as historical local evidence after develop advances. |
| Scope Discipline | 8/8 | No product feature, GUI behavior, solver adapter, version, or license metadata changes. |
| Git / Local Environment Safety | 8/8 | Worktrees are isolated; no push, destructive Git command, remote edit, or tag mutation performed. |
| Release Tag Safety | 8/8 | rc1 and rc2 object type/peeled target verified; final `v0.1.0` absent; no new RC tag created. |

Normalized score: 98/100.

## Findings

Critical issues: none.

High issues: none.

Medium issues: none remaining.

Low issues: pre-merge QA runs the docs checker directly after fast QA also runs
it. This is redundant but harmless and confirms the required pre-merge command.

## Required Fixes

None remaining.

## Required Evidence

Amend-branch checks passed:

- `python -m osw.cli --version`: `osw 0.1.0rc2`
- `python tools/qa/check_docs_links.py`: 30 Markdown files, 58 local links, 0 skipped external links, 0 failures
- `python tools/qa/check_duplicate_test_basenames.py`
- `python tools/qa/check_release_metadata.py --expected-version 0.1.0rc2 --expected-source-license GPL-3.0-or-later --allowed-prior-rc-tag v0.1.0-rc1 --allowed-prior-rc-target 29c5c8bec8df30c7f7be72fc9be5e5409794968e --expected-rc-tag v0.1.0-rc2 --expected-rc-target 684dc6138d4257564bbcdd176a9d5ed311a7316d --require-annotated-rc-tag`
- `pytest tests/unit/test_docs_links.py -q`: 18 passed
- `pytest tests/unit/test_qa_tools.py -q`: 5 passed
- `pytest tests/unit -q`: 248 passed, 3 skipped
- `pytest -q`: 266 passed, 19 skipped
- `ruff check src tests`
- `python tools/qa/check_scope_drift.py`
- `python tools/qa/check_architecture_boundaries.py`
- `python tools/qa/check_no_solver_artifacts_committed.py`
- `python tools/qa/run_fast_qa.py`
- `python tools/qa/run_pre_merge_qa.py`
- `git diff --check`

Tag evidence before merge:

- `v0.1.0-rc1` object type: `tag`
- `v0.1.0-rc1` peeled commit: `29c5c8bec8df30c7f7be72fc9be5e5409794968e`
- `v0.1.0-rc2` object type: `tag`
- `v0.1.0-rc2` peeled commit: `684dc6138d4257564bbcdd176a9d5ed311a7316d`
- `v0.1.0`: absent

## Generated And Runtime Artifact Check

`python tools/qa/check_no_solver_artifacts_committed.py` passed. The only
generated evidence included in scope is the required text self-check and review
report under `.codex/reports/`.

## Residual Risks

- The checker intentionally skips external URL freshness because release QA must
  remain local-only and no-network by default.
- The Markdown parser covers the local link forms required for OSW docs QA, not
  every possible Markdown extension.

## Merge Recommendation

Proceed with pre-merge QA and squash merge to `develop` using:

`test(docs): add local markdown link checker`
