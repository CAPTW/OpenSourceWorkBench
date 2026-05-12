# OSW Agent Guide

This file is the repository-level contract for Codex work in OpenSolver
Workbench (OSW). Directory `AGENTS.md` files may add local rules, but must not
weaken this root policy.

## Mission

Build OSW v0.1 as an open-source educational and research Engineering Solver &
Script Workbench. Keep workflows inspectable, reproducible, and honest about
their limits.

OSW is not a MATLAB clone, ANSYS clone, Simulink clone, industrial-certified CAE
product, or commercial CAD replacement.

## v0.1 Scope

Focus on:

- PySide6 desktop GUI shell and preview workflows.
- Plugin/add-in architecture for importers, solvers, scripts, post-processing,
  and reports.
- ProjectSchema, UnitSystem, MaterialDB, ResultDataset, and FigureDataset
  contracts.
- Standard/exported CAD, CAE, CFD, chemistry, `.m`, and `.mat` workflows.
- meshio, Gmsh, PyVista, and Matplotlib integration points.
- Bounded CalculiX, OpenFOAM template, Cantera, CoolProp, and MATLAB/Octave
  demo workflows.
- HTML report output, validation matrix, and golden tests.

## Must Not Support

Do not implement or claim:

- Native SolidWorks, CATIA, NX, Creo, or other commercial CAD direct import.
- Simulink, `.slx`, or `.mlapp` compatibility.
- Full OpenFOAM solver coverage or a full OpenFOAM UI.
- Full MATLAB proprietary toolbox compatibility.
- Industrial certification, compliance, accuracy, or production CAE claims.
- GUI direct subprocess solver execution.
- Mandatory heavy dependencies for bootstrap, CLI smoke, or unit tests.

## Architecture Rules

- Keep core contracts small, typed, and independent of GUI and heavy optional
  dependencies.
- Keep dependency direction inward: GUI and adapters may depend on core
  contracts; core must not depend on GUI, solver binaries, or plugin
  implementations.
- Prefer preview, validation, and explicit user confirmation before project
  mutation.
- Put importer, solver, script, post-processing, and report behavior behind
  plugin-style contracts.
- Keep examples small and reproducible without commercial software.
- Add abstractions only when they protect a real boundary or remove meaningful
  duplication.

## Dependency Direction

- Base install must support package import, CLI smoke, and lightweight tests.
- PySide6, meshio, Gmsh, PyVista, Matplotlib, Cantera, CoolProp, and solver
  tooling belong behind optional extras or guarded imports.
- Unit tests must not require heavy extras, network access, or external solver
  executables.
- Optional dependency errors must be explicit and actionable.

## Runner Rule

External solver or script execution is a backend/service concern, not a GUI
button path. v0.1 GUI code may prepare cases, preview commands, validate inputs,
and import results, but must not directly run solver subprocesses.

Any future runner must provide dry-run output, explicit working directory and
environment handling, cancellation/timeout design, log capture, artifact
classification, and tests that do not execute external solvers by default.

## Plugin Manifest Rule

Plugins should declare a small manifest before behavior is wired in:

- stable id, display name, version, and plugin type;
- entry point or adapter class;
- capabilities and supported standard/exported formats;
- optional extras required;
- whether preview is required before mutation;
- whether the plugin can prepare a case, import results, or request external
  execution;
- validation messages and user-visible limitations.

Plugin import must avoid side effects such as launching processes, writing
files, changing global state, or importing heavy dependencies unnecessarily.

## Unit System Rule

Physical values must carry explicit units at project boundaries. Do not pass
ambiguous bare floats through project schema, material, solver, or result
interfaces when the quantity has dimensions. Keep conversions centralized in
UnitSystem-facing code and document assumptions in reports.

## MATLAB/Octave `.m` Safety

`.m` and `.mat` workflows are preview-first. Do not execute arbitrary `.m`
scripts by default. Do not support Simulink, `.slx`, `.mlapp`, or proprietary
toolbox compatibility claims. Treat script output as untrusted until parsed,
previewed, and explicitly accepted into a project. Block or surface shell
escape, file mutation, network, or subprocess behavior in preview.

## Test Rules

- Add or update focused tests when production behavior changes.
- Keep unit tests network-free, solver-free, and independent of heavy extras.
- Put golden fixtures under `tests/golden` or curated `examples` paths.
- Do not commit runtime solver artifacts, generated reports, caches, or logs.
- Before reporting success, run the requested QA commands or state the exact
  skipped reason.

## Review Rules

- Review for scope, safety, architecture, tests, and user-facing claims before
  style.
- Merge is forbidden unless the review gate in `docs/06_review_protocol.md`
  passes and required fixes are complete.
- Reject scope drift into commercial native CAD import, Simulink or `.mlapp`,
  full OpenFOAM coverage, industrial certification, GUI direct solver
  execution, secrets, or generated runtime artifacts.

## Git Rules

- Do not push, force-push, edit remotes, delete branches, delete worktrees, run
  `git reset --hard`, or run `git clean` unless the user explicitly requests the
  exact operation.
- Use feature and amend worktrees for isolated phase-step work.
- Preserve unrelated user changes.
- Do not commit without explicit instruction from the active prompt.
