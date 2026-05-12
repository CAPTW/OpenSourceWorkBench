# OSW Agent Guide

## Mission

Build OpenSolver Workbench v0.1 as an open-source educational and research
Engineering Solver & Script Workbench. Keep the codebase inspectable, testable,
and honest about its limits.

## Scope

Focus on PySide6 GUI architecture, plugin/add-in boundaries, project schema,
unit system, material database, result and figure datasets, standard exported
CAD/CAE/CFD/chemistry formats, meshio/Gmsh/PyVista/Matplotlib workflows, and
preview-first script handling.

Do not build native commercial CAD import, Simulink or `.mlapp` support, full
OpenFOAM coverage, full MATLAB toolbox compatibility, industrial certification
claims, or GUI direct subprocess solver execution.

## Architecture Rules

- Keep heavy dependencies behind optional extras and plugin boundaries.
- Treat solver execution as an explicit backend/service concern, not a GUI click
  path.
- Prefer preview, validation, and import summaries before mutating projects.
- Keep examples small and reproducible without commercial software.
- Use typed, narrow modules instead of broad utility buckets.

## Test Rules

- Add tests before production behavior changes.
- Keep unit tests network-free and solver-free.
- Put golden fixtures under `tests/golden` or `examples` so `.gitignore`
  allowlists them.
- Run `pytest tests/unit -q` and `ruff check src tests` before reporting success.

## Review Rules

- Lead with correctness, safety, validation, and scope drift risks.
- Reject claims that imply industrial certification or proprietary clone status.
- Check generated artifacts, runtime solver outputs, and secrets before commit.
- Preserve unrelated user changes.

## Codex Behavior

- Do not push, force-push, edit remotes, delete branches, delete worktrees, or
  run destructive Git recovery without explicit instruction.
- Use the tracked Git hooks and `tools/git/preflight_commit.py` before commits.
- Keep bootstrap work limited to repository structure and smoke behavior.
