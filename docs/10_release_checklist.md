# Release Checklist

- [ ] `python -m osw.cli --version` reports the intended version.
- [ ] `python -m osw.cli doctor` reports environment status.
- [ ] `pytest tests/unit -q` passes.
- [ ] `ruff check src tests` passes or has a documented blocker.
- [ ] README scope and non-goals are current.
- [ ] Validation matrix reflects implemented workflows.
- [ ] No solver runtime artifacts, secrets, or generated report dumps are staged.
- [ ] License decision is finalized before public release.
