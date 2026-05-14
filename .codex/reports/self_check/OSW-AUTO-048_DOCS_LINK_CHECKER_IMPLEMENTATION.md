# OSW-AUTO-048 Docs Link Checker Self-Check

## Scope

This step implements a local-only Markdown documentation link checker and closes
the remaining P2 docs-link QA placeholder. It does not change product source
code, package version metadata, license metadata, release tags, or public
release announcement wording.

## Previous Checker Status

`tools/qa/check_docs_links.py` was missing before this step.

## Checker Design Summary

- `tools/qa/check_docs_links.py` uses only the Python standard library.
- Default scan targets:
  - `README.md`
  - `CHANGELOG.md`
  - `docs/**/*.md`
  - `examples/**/*.md`
  - `examples/**/README*.md`
- Default exclusions include `.git`, virtual environments, caches, build output,
  wheel output, `.codex/reports`, `.codex/rescue`, and common generated solver
  runtime directories.
- It parses inline Markdown links, image links, reference-style link
  definitions/usages, and common external autolinks outside fenced code blocks.
- It validates local files, directories, URL-decoded paths, reference-style
  usage targets, same-file anchors, and file-plus-anchor targets.
- It generates GitHub-style Markdown heading anchors, including duplicate
  heading suffixes.
- It rejects unsupported schemes, absolute local paths by default, and local
  links that escape the repository root.
- It classifies `http`, `https`, `mailto`, and `tel` links as skipped external
  links by default and performs no network access.
- It can emit JSON with `--json`.

## Broken Links Found And Fixed

The checker found no broken local documentation links in the default scan:

```text
Markdown files checked: 30
Local links checked: 58
External links skipped: 0
```

No broad documentation rewrites were needed. Release checklist, risk register,
and decision log were updated only to record that the docs-link checker P2 issue
is resolved and that rc1/rc2 remain local historical evidence after develop
advances.

## Feature Branch QA

Passed:

- `python -m osw.cli --version`: `osw 0.1.0rc2`
- `python -m osw.cli doctor`
- `python tools/qa/check_docs_links.py`
- `python tools/qa/check_duplicate_test_basenames.py`
- `python tools/qa/check_release_metadata.py --expected-version 0.1.0rc2 --expected-source-license GPL-3.0-or-later --allowed-prior-rc-tag v0.1.0-rc1 --allowed-prior-rc-target 29c5c8bec8df30c7f7be72fc9be5e5409794968e --expected-rc-tag v0.1.0-rc2 --expected-rc-target 684dc6138d4257564bbcdd176a9d5ed311a7316d --require-annotated-rc-tag`
- `pytest tests/unit/test_docs_links.py -q`: `18 passed`
- `pytest tests/unit/test_qa_tools.py -q`: `5 passed`
- `pytest tests/unit -q`: `248 passed, 3 skipped`
- `pytest tests/gui -q`: `10 skipped`
- `pytest -q --import-mode=importlib`: `266 passed, 19 skipped`
- `pytest tests/integration -q -m "not external_solver"`:
  `4 passed, 3 skipped, 3 deselected`
- `pytest tests/golden -q`: `10 passed`
- `pytest tests/validation -q`: `4 passed`
- `pytest -q`: `266 passed, 19 skipped`
- `ruff check src tests`
- `python tools/qa/check_scope_drift.py`
- `python tools/qa/check_architecture_boundaries.py`
- `python tools/qa/check_no_solver_artifacts_committed.py`
- `python tools/qa/run_fast_qa.py`
- `python tools/qa/run_pre_merge_qa.py`
- `git diff --check`

## Amend Review Fixes

The initial review scored 88/100 and requested two narrow fixes:

- Check reference-style link usages such as `[Doc][id]` and fail undefined
  references with a source file and line number.
- Handle valid inline local paths that contain a balanced parenthesis group.

The amend adds regression tests for both cases and updates the parser without
changing product source, solver adapters, package version metadata, license
metadata, release tags, or broad documentation content.

## Tag Preservation Evidence

Before review:

- `v0.1.0-rc1` object type: `tag`
- `v0.1.0-rc1` peeled commit:
  `29c5c8bec8df30c7f7be72fc9be5e5409794968e`
- `v0.1.0-rc2` object type: `tag`
- `v0.1.0-rc2` peeled commit:
  `684dc6138d4257564bbcdd176a9d5ed311a7316d`
- `v0.1.0`: absent

No tag was created, deleted, moved, overwritten, retargeted, or pushed.

## Remaining Risks

- After this prompt merges, local `v0.1.0-rc2` remains historical feedback
  evidence and no longer represents current `develop`; a later RC3 tag gate is
  required if a current pushable RC is needed.
- The checker intentionally does not fetch external URLs by default, so external
  URL freshness remains outside local QA.
