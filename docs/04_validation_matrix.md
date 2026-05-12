# Validation Matrix

| Area | Bootstrap Target | Evidence |
| --- | --- | --- |
| Package import | `import osw` succeeds | `tests/unit` |
| CLI version | `python -m osw.cli --version` | `tests/unit` |
| CLI doctor | reports Python and optional modules | `tests/unit` |
| Solver execution | disabled in bootstrap | CLI doctor output |
| Generated artifacts | blocked by Git preflight | `tools/git/preflight_commit.py` |

Future rows should cover schema validation, unit conversion, importer previews,
golden datasets, and report output.
