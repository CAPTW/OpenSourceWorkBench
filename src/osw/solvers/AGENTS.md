# Solver Agent Rules

This directory owns solver adapter contracts and bounded demo preparation.

- Solver adapters may validate inputs, prepare educational demo cases, describe
  commands, and import structured results.
- Do not implement GUI direct subprocess execution here or expose APIs that make
  GUI direct execution natural.
- External execution, if later approved, must go through an explicit runner
  service with dry-run, cwd/env controls, timeout/cancel design, log capture,
  and artifact classification.
- Keep CalculiX and OpenFOAM support bounded to the v0.1 demos until a later
  roadmap item expands scope.
- Unit tests must not require installed solver binaries.
- Solver outputs must map toward ResultDataset, FigureDataset, validation
  messages, and report evidence instead of raw file dumps.
