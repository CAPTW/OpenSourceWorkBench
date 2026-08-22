# Release Tooling

This directory contains maintainer-only release verification helpers. The
current public prerelease is `v0.1.5-rc3`; `v0.1.5-rc2`, `v0.1.5-rc1`, and `v0.1.3-rc1` examples are retained
only as explicit historical identities.

## Identity-Bound Asset Verification

Use `tools/qa/check_release_asset_smoke.py` with exactly one mode:
`current-live`, `explicit-remote`, `local-set`, or `offline-fixture`. Select
`quick` or `full-static` explicitly; `offline-fixture` is `quick`-only.

The checker verifies release identity and static consistency only. `quick`
reports `IDENTITY_BOUND_QUICK`; `full-static` adds static package and
portable-layout inspection and reports `IDENTITY_BOUND_FULL_STATIC`. Both set
`release_readiness=false`. Neither level extracts or installs a package,
imports downloaded code, runs a downloaded CLI, launches
`OpenSolverWorkbench.exe`, proves runtime behavior, establishes engineering
correctness, or establishes publication readiness.

Immutable target authority is the annotated Git tag object peeled to its exact
40-hex commit. GitHub Release `target_commitish` is display context only and
cannot override the selected profile or caller-supplied target.

`tests/fixtures/release_assets` is a frozen synthetic, non-installable
fixture. It is not a byte snapshot of the published `v0.1.3-rc1` assets and
supplies no remote provenance.

Current live verification:

```powershell
.venv\Scripts\python.exe tools\qa\check_release_asset_smoke.py --mode current-live --download-dir artifacts\release\download_smoke\manual-current --verification-level quick --json-out artifacts\release\download_smoke\manual-current-summary.json
```

Explicit historical remote verification:

```powershell
.venv\Scripts\python.exe tools\qa\check_release_asset_smoke.py --mode explicit-remote --repo CAPTW/OpenSourceWorkBench --tag v0.1.3-rc1 --expected-version 0.1.3rc1 --expected-target a6e8d3a8211e02359841d10e1947e16ab847b132 --download-dir artifacts\release\download_smoke\manual-v013 --verification-level quick --json-out artifacts\release\download_smoke\manual-v013-summary.json
```

Local historical asset-set verification:

```powershell
.venv\Scripts\python.exe tools\qa\check_release_asset_smoke.py --mode local-set --tag v0.1.3-rc1 --expected-version 0.1.3rc1 --expected-target a6e8d3a8211e02359841d10e1947e16ab847b132 --asset-dir artifacts\release\download_smoke\local-v013\assets --verification-level quick
```

Offline synthetic fixture verification:

```powershell
.venv\Scripts\python.exe tools\qa\check_release_asset_smoke.py --mode offline-fixture --asset-dir tests\fixtures\release_assets --verification-level quick
```

Remote modes require a download directory and may download public assets.
Local modes are network-free. None of the modes uploads assets, edits a GitHub
Release, pushes Git refs, creates tags, retargets tags, or overwrites release
assets.
