# v0.1.3rc2 onboarding issue closure evidence

Related issue: `#13` Improve onboarding examples and tutorials

Repository evidence point:

- Branch: `develop`
- HEAD before closure evidence commit:
  `fe595519eb78aebb7f6b8f8d55d9aebda53d2637`
- Closure evidence commit: `docs(maintenance): record onboarding closure evidence`

Public release:

- Release: `v0.1.3-rc1`
- Tag target: `a6e8d3a8211e02359841d10e1947e16ab847b132`
- State: public prerelease

Active development version: `0.1.3rc2.dev0`

## Evidence

- Tutorial index exists:
  [Tutorials](../tutorials/README.md)
- First CLI walkthrough exists and was smoke-tested:
  [First CLI Walkthrough](../tutorials/first_cli_walkthrough.md)
- First GUI walkthrough exists:
  [First GUI Walkthrough](../tutorials/first_gui_walkthrough.md)
- Result dataset walkthrough exists:
  [Result Dataset Walkthrough](../tutorials/result_dataset_walkthrough.md)
- Release asset smoke walkthrough exists:
  [Release Asset Smoke Walkthrough](../tutorials/release_asset_smoke_walkthrough.md)
- Examples index was updated:
  [Examples](../examples.md) and [examples README](../../examples/README.md)
- Public docs QA was updated to require tutorial coverage.
- Onboarding docs tests were added and pass.

## Smoke Results

Safe copy-paste commands from the first CLI walkthrough were rerun for closure:

```powershell
.venv\Scripts\python.exe -m osw.cli --version
.venv\Scripts\python.exe -m osw.cli --help
.venv\Scripts\python.exe -m osw.cli project-demo-json --out artifacts\tutorials\closure_first_cli_demo_project.json
.venv\Scripts\python.exe -m osw.cli project-validate artifacts\tutorials\closure_first_cli_demo_project.json
.venv\Scripts\python.exe -m osw.cli report-summary artifacts\tutorials\closure_first_cli_demo_project.json
.venv\Scripts\python.exe -m osw.cli result-dataset-inspect tests\fixtures\fields\scalar_field_dataset.json
.venv\Scripts\python.exe -m osw.cli field-dataset-inspect tests\fixtures\fields\scalar_field_dataset.json
```

Result:

- CLI version remained `0.1.3rc2.dev0`.
- Help output listed the documented commands.
- Demo project generation passed.
- Demo project validation passed with documented MATLAB/Octave preview warnings.
- Report summary passed without running solvers or scripts.
- Result dataset and field dataset fixture inspection passed.
- Generated tutorial artifacts remained under ignored `artifacts/` paths.

## Known Limitations

- `v0.1.3-rc1` remains a prerelease.
- The Windows portable ZIP is unsigned.
- There is no MSI installer.
- There is no code signing.
- External solvers are optional and are not bundled.
- Optional solver and science dependencies are environment-specific.
- Users must validate engineering results independently.

## Decision

Issue `#13` is eligible for closure.

The acceptance criteria are met: the examples index covers CLI and GUI paths,
multiple end-to-end tutorials exist, screenshots and expected outputs are
linked or described, optional dependency diagnostics are documented, and the
docs preserve prerelease and scope limitations.

## Next Recommended Issue

- Issue `#16`: code signing and installer strategy, if release trust is the
  next priority.
- Issue `#12`: v0.1.4 feature selection planning, if feature planning is the
  next priority.
