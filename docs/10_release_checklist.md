# Release Checklist

## Packaging Gate

- [ ] `pyproject.toml` metadata, package discovery, and `requires-python >=3.11` are current.
- [ ] Base install has no mandatory heavy GUI, visualization, mesh, chemistry, or script extras.
- [ ] Optional extras are declared for `gui`, `viz`, `mesh`, `mscript`, and `chm`.
- [ ] `environment.yml` installs the editable development package without optional solver stacks.
- [ ] `python -m osw.cli --version` reports the intended version.
- [ ] `python -m osw.cli doctor` reports optional stack availability without failing when extras are absent.

## Quality Gate

- [ ] `python -m osw.cli --version` reports the intended version.
- [ ] `python -m osw.cli doctor` reports environment status.
- [ ] `pytest tests/unit -q` passes.
- [ ] `ruff check src tests` passes or has a documented blocker.
- [ ] README scope and non-goals are current.
- [ ] `docs/known_limitations.md` is current and linked from README.
- [ ] Validation matrix reflects implemented workflows.
- [ ] No solver runtime artifacts, secrets, or generated report dumps are staged.
- [ ] License decision is finalized before public release.

## Release Discipline

- [ ] Public packages do not claim industrial certification or full commercial solver parity.
- [ ] Known limitations are included in release notes or linked from release documentation.
- [ ] External solver installers are not bundled into the base package.
- [ ] Generated reports and runtime case outputs are excluded unless they are curated examples or tests.
