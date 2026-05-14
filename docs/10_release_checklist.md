# Release Checklist

Use this checklist for v0.1 release readiness review. The release gate confirms
documentation, workflow smoke evidence, QA evidence, and known limitations. It
does not claim external solver availability in every environment.

## Release Scope Confirmation

- [ ] Release notes describe OSW v0.1 as an educational/research prototype.
- [ ] README scope and non-goals are current.
- [ ] `docs/known_limitations.md` is current and linked from README.
- [ ] Public docs do not claim industrial certification or full commercial
  solver parity.
- [ ] Public docs do not claim native commercial CAD direct import support.
- [ ] `.m` workflows remain preview-first, and execution is user-triggered.

## Packaging Gate

- [ ] `pyproject.toml` metadata, package discovery, and `requires-python >=3.11` are current.
- [ ] Base install has no mandatory heavy GUI, visualization, mesh, chemistry, or script extras.
- [ ] Optional extras are declared for `gui`, `viz`, `mesh`, `mscript`, and `chm`.
- [ ] `environment.yml` installs the editable development package without optional solver stacks.
- [ ] `python -m osw.cli --version` reports the intended version.
- [ ] `python -m osw.cli doctor` reports optional stack availability without failing when extras are absent.

## Documentation Checklist

- [ ] [Tutorial examples](tutorials.md) cover examples `01` through `08`.
- [ ] [Demo smoke checklist](demo_smoke_checklist.md) covers examples `01`
  through `08`.
- [ ] [Known limitations](known_limitations.md) covers solver, validation,
  optional dependency, CAD, and script execution boundaries.
- [ ] Each tutorial has goal, prerequisites, steps, expected output, and
  troubleshooting.
- [ ] Documentation distinguishes tutorial smoke from optional local executable
  smoke.
- [ ] Documentation does not imply that documentation-only examples are
  executable fixtures.

## Demo Smoke Checklist

- [ ] `docs/demo_smoke_checklist.md` has a recorded review entry for each v0.1
  example.
- [ ] Demo smoke evidence records pass, skip, or optional local executable
  status for each example.
- [ ] Optional dependency examples have explicit skip reasons when dependencies
  are missing.
- [ ] External solver examples document that executable smoke is optional and
  local-environment dependent.
- [ ] Generated solver outputs, reports, logs, and runtime directories are not
  staged unless they are curated fixtures.
- [ ] Smoke evidence links to self-check or review reports when available.

## QA Command Checklist

- [ ] `python -m osw.cli --version` reports the intended version.
- [ ] `python -m osw.cli doctor` reports environment status.
- [ ] `python tools/qa/run_fast_qa.py` passes or has a documented blocker.
- [ ] `pytest tests/unit -q` passes.
- [ ] `ruff check src tests` passes or has a documented blocker.
- [ ] `python tools/qa/check_scope_drift.py` passes.
- [ ] `python tools/qa/check_architecture_boundaries.py` passes.
- [ ] `python tools/qa/check_no_solver_artifacts_committed.py` passes.
- [ ] `tools/qa/check_docs_links.py` is run if present; if absent, the skip is
  recorded.
- [ ] A local markdown link/content check is run if a project command exists; if
  absent, the skip is recorded.
- [ ] Validation matrix reflects implemented workflows.
- [ ] No solver runtime artifacts, secrets, or generated report dumps are staged.

## Optional Dependency Checklist

- [ ] `python -m osw.cli doctor` output records optional dependency status.
- [ ] Missing PySide6, meshio, Gmsh, PyVista, Cantera, CoolProp, GNU Octave, or
  external solver executables are reported as optional unless the specific
  smoke entry explicitly requires them.
- [ ] Optional local executable smoke records the local dependency version or
  missing-dependency diagnostic when available.
- [ ] Base CLI smoke and unit tests do not require heavy optional stacks.

## Known Limitations Checklist

- [ ] Release notes or release documentation link `docs/known_limitations.md`.
- [ ] Reports and demo evidence include known limitations or link to the known
  limitations page.
- [ ] External solver availability is not guaranteed.
- [ ] Results without validation evidence remain marked as preview,
  template-based, fixture-backed, or educational as appropriate.

## Report Evidence Checklist

- [ ] `.codex/reports/self_check/` contains the phase self-check report.
- [ ] `.codex/reports/review/` contains the phase review report.
- [ ] Reports record commands run, command results, skipped checks, remaining
  risks, and merge recommendation.
- [ ] Report evidence does not include secrets, generated solver runtime
  directories, binary outputs, or uncontrolled report exports.

## Merge Readiness Checklist

- [ ] Feature worktree is clean after checkpoint/review commits.
- [ ] Target `develop` worktree is clean before merge.
- [ ] Review score meets the threshold in `docs/06_review_protocol.md`.
- [ ] Required amend items are complete, if any.
- [ ] Squash merge uses the approved release/docs commit message.

## Final Sign-Off Checklist

- [ ] Target `develop` commit hash is recorded.
- [ ] Post-merge fast QA result is recorded.
- [ ] Post-merge scope drift, architecture boundary, and solver artifact checks
  are recorded.
- [ ] Validation matrix reflects implemented workflows.
- [ ] License decision is finalized before public release.

## Release Discipline

- [ ] Public packages do not claim industrial certification or full commercial solver parity.
- [ ] Known limitations are included in release notes or linked from release documentation.
- [ ] External solver installers are not bundled into the base package.
- [ ] Generated reports and runtime case outputs are excluded unless they are curated examples or tests.
