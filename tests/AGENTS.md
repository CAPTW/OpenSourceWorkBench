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
- Before reporting success, run the requested test command or record the exact
  skipped reason.
