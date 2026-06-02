# v0.1 Handoff Manifest

This manifest is the compact owner handoff for the frozen internal v0.1 release
candidate. It records what to inspect, how to smoke test, and what not to stage.

## Repository

| Item | Value |
| --- | --- |
| Branch | `develop` |
| Latest committed base before handoff docs | `c2bbee7 feat(plugins): harden local plugin install flow` |
| Queue status | UI complete; functional queue frozen after `OSW-FUNC-023_V0_1_FREEZE_AND_HANDOFF` |
| Public tag/push | Not created, not pushed |
| Package metadata | `0.1.2` |
| Local tag line | Historical tags exist through `v0.1.2`; current `develop` is ahead and should use a new patch line such as `0.1.3rc1` / `v0.1.3-rc1` if a current candidate is needed. |

The exact handoff commit is the commit containing this manifest and is recorded
in the final run output.

## Main Docs Index

- [README](../../README.md)
- [v0.1 Freeze Handoff](v0_1_freeze_handoff.md)
- [v0.1 Release Notes](v0_1_release_notes.md)
- [v0.1 Release Candidate](v0_1_release_candidate.md)
- [Known Limitations For v0.1](known_limitations_v0_1.md)
- [Release Checklist](../10_release_checklist.md)
- [Validation Matrix](../04_validation_matrix.md)
- [Packaging and Release Docs](../32_packaging_release_docs.md)
- [Plugin Install Hardening](../33_plugin_install_hardening.md)
- [Plugin Contract](../03_plugin_contract.md)
- [UI Completion Summary](../ui/ui_completion_summary.md)

## Major Commands

Base environment:

```powershell
python -m osw.cli --help
python -m osw.cli doctor
python -m osw.cli --version
```

Project/report smoke:

```powershell
python -m osw.cli project-demo-json --out artifacts\release\freeze_demo_project.json
python -m osw.cli project-validate artifacts\release\freeze_demo_project.json
python -m osw.cli report-export artifacts\release\freeze_demo_project.json --out artifacts\release\freeze_report.html
python -m osw.cli report-summary artifacts\release\freeze_demo_project.json
```

Plugin smoke:

```powershell
python -m osw.cli plugins-list
python -m osw.cli plugins-health
python -m osw.cli plugins-installed --install-root artifacts\plugin\freeze_install_root
```

Demo surface smoke:

```powershell
python -m osw.cli mesh-formats
python -m osw.cli mscript-preview tests\fixtures\mscript\simple_plot.m
python -m osw.cli mscript-scan tests\fixtures\mscript\dangerous_system.m
python -m osw.cli octave-check
python -m osw.cli gmsh-check
python -m osw.cli coolprop-check
python -m osw.cli cantera-check
```

## Test / QA Commands

```powershell
.venv\Scripts\python.exe -m pytest tests/unit -q
.venv\Scripts\python.exe -m pytest tests/gui -q
.venv\Scripts\python.exe -m pytest tests/integration -q
.venv\Scripts\python.exe -m pytest tests/golden -q
.venv\Scripts\python.exe -m pytest tests/validation -q
ruff check src tests
ruff check tests/unit tests/gui tests/integration tests/validation
python tools/qa/run_release_gate.py
python -m json.tool .codex/func_queue_state.json
git diff --check
```

Raw `ruff check src tests` should pass after post-freeze duplicate-file
hygiene. If duplicate desktop files reappear, quarantine them in a separate
hygiene task before release validation.

## Artifact Policy

Do not stage:

- `artifacts/**`
- `.codex/reports/**`
- duplicate `* (1)` files
- root `GUI.png`
- generated solver/runtime outputs
- rejected runtime report artifacts

Generated smoke outputs should stay under `artifacts/release`,
`artifacts/plugin`, or `artifacts/ui` and remain uncommitted.

## Optional Dependency Matrix

| Optional stack | Expected handoff behavior |
| --- | --- |
| PySide6 | GUI tests/screenshots run if installed; otherwise GUI commands skip or diagnose. |
| PyVista | Field rendering optional; metadata inspection remains available. |
| meshio | Mesh conversion optional; base mesh metadata remains import-safe. |
| Gmsh | `gmsh-check` may report missing; `.geo` generation remains available. |
| Octave | `octave-check` may report missing; `.m` import remains preview-first. |
| SciPy/hdf5storage/h5py | MAT support optional; missing readers produce diagnostics. |
| CoolProp | `coolprop-check` may report missing; no base failure. |
| Cantera | `cantera-check` may report missing; no base failure. |
| CalculiX `ccx` | Optional explicit backend run only; deck/parser tests are fixture-backed. |
| OpenFOAM | Optional explicit backend run only; template/parser tests are fixture-backed. |
| PyYAML | Optional YAML plugin manifest support; JSON manifests remain supported. |

## Release Blockers And Warnings

No P0/P1 blocker is accepted in this handoff if final QA passes. Remaining
warnings:

- Duplicate `* (1)` files were quarantined under ignored `artifacts/hygiene`;
  do not stage them.
- Runtime reports and artifacts are untracked by policy.
- Optional live dependencies and executables may be missing locally.
- No public tag/push/package publication is part of this handoff.
- Local `v0.1.2` exists as historical evidence and must not be moved or pushed
  as the current `develop` line.
- No plugin signing, remote plugin store, or dependency auto-install exists.

## Next-Owner Checklist

1. Confirm `git status --short` contains no tracked dirty files.
2. Confirm `.codex/func_queue_state.json` has `current_step: null` and
   `next_step: null`.
3. Review [v0.1 Freeze Handoff](v0_1_freeze_handoff.md).
4. Run the test/QA commands relevant to the local environment.
5. Keep generated artifacts and reports untracked.
6. Clean duplicate `* (1)` files only in a separate hygiene task if they
   reappear.
7. Prepare any current release tag only after explicit maintainer approval and
   version-line reconciliation.
