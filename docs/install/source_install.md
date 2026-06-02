# Source And Development Install

OSW v0.1 is release-ready through source checkout plus editable Python install.
Binary installers and Docker images are deferred.

## Supported Python

`pyproject.toml` requires Python 3.11 or newer and advertises Python 3.11 and
3.12 support.

## Base Editable Install

```powershell
python -m pip install -e .
python -m osw.cli --help
python -m osw.cli doctor
```

Base install should support CLI import, demo project JSON generation, project
validation, plugin manifest checks, report export, and result inspection without
heavy optional dependencies.

## Developer Install

```powershell
python -m pip install -e ".[dev]"
python -m pytest tests/unit -q
ruff check src tests
python tools/qa/run_fast_qa.py
```

The `dev` extra currently installs pytest and Ruff.

## Research Optional Install

```powershell
python -m pip install -e ".[gui,viz,mesh,mscript,chm]"
```

This installs optional Python packages for GUI, visualization, mesh conversion,
MAT-file preview, CoolProp, and Cantera. It does not install external solver
programs.

## Conda Or Mamba

Use the checked-in `environment.yml` for a base development shell:

```powershell
conda env create -f environment.yml
conda activate osw-dev
python -m osw.cli doctor
```

The environment file intentionally installs `-e .[dev]` only. Install optional
extras explicitly if the workflow needs them.

## Local QA

```powershell
python -m pytest tests/unit -q
python -m pytest tests/integration -q
python -m pytest tests/golden -q
python -m pytest tests/validation -q
python tools/qa/check_docs_links.py
python tools/qa/check_scope_drift.py
python tools/qa/check_architecture_boundaries.py
python tools/qa/check_no_solver_artifacts_committed.py
python tools/qa/run_release_gate.py
python -m json.tool .codex/func_queue_state.json
git diff --check
```

If raw recursive checks include untracked desktop duplicate `* (1)` files, clean
or ignore those local files rather than staging them. They are not release
artifacts.

## CLI Quickstart

```powershell
python -m osw.cli project-demo-json --out artifacts\release\demo_project.json
python -m osw.cli project-validate artifacts\release\demo_project.json
python -m osw.cli plugins-list
python -m osw.cli plugins-health
python -m osw.cli report-export artifacts\release\demo_project.json --out artifacts\release\demo_report.html
python -m osw.cli report-summary artifacts\release\demo_project.json
python -m osw.cli result-catalog-inspect tests\fixtures\results\mixed_result_catalog.json
```

Generated files under `artifacts/release/` are local runtime outputs and should
remain untracked.
