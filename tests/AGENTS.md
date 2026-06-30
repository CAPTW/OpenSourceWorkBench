# Test Agent Rules

This directory owns OSW tests and fixtures.

- Unit tests must be fast, network-free, solver-free, and independent of heavy
  optional extras.
- Integration, GUI, golden, and validation tests may use markers or opt-in
  commands when they require heavier dependencies.
- Do not execute external solvers, MATLAB, Octave, OpenFOAM, CalculiX, or Gmsh
  in default unit tests.
- Keep fixtures small, deterministic, and license-safe.
- Golden files must document their source and expected update process.
- Golden comparisons should use `tests/golden/helpers.py` for normalized text or
  JSON diffs. Normalize line endings, trailing whitespace, known volatile paths,
  and timestamps before comparing.
- Golden fixtures are updated only for intentional contract changes. Review the
  unified diff, keep fixtures small, and rerun `pytest tests/golden -q` plus the
  relevant unit or QA checks before committing.
- Golden tests must not regenerate fixtures automatically during normal test
  runs and must not execute external solvers or optional heavy tools by default.
- Before reporting success, run the requested test command or record the exact
  skipped reason.
