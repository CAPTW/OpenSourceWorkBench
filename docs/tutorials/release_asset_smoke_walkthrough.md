# Release Asset Smoke Walkthrough

This walkthrough is for maintainers who want static, identity-bound release
asset verification. The current public prerelease is `v0.1.5-rc3`; examples
using `v0.1.5-rc2`, `v0.1.5-rc1`, or `v0.1.3-rc1` are explicit historical verification examples. The checker
never uploads assets, edits a GitHub Release, creates or retargets tags, or
pushes Git refs.

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

This offline fixture check uses the frozen local fixture without network access.
It is not a live GitHub Release download, and the checker does not upload files or data.

`tests/fixtures/release_assets` is a frozen synthetic, non-installable
fixture. It is not a byte snapshot of the published `v0.1.3-rc1` assets and
supplies no remote provenance.

## Choose One Explicit Mode

- `current-live` selects the repository-pinned current `v0.1.5-rc1` profile.
- `explicit-remote` requires a complete repository, tag, version, and peeled
  target tuple, such as the historical `v0.1.3-rc1` identity.
- `local-set` verifies caller-supplied assets against a complete caller-supplied
  identity tuple without network access.
- `offline-fixture` accepts only the canonical fixture directory and is
  intentionally `quick`-only.

Remote modes require `--download-dir`; local modes require `--asset-dir`.
Choose `--verification-level quick` or, except for `offline-fixture`,
`--verification-level full-static` explicitly.

## Copy-Paste Commands

Current public release:

```powershell
.venv\Scripts\python.exe tools\qa\check_release_asset_smoke.py --mode current-live --download-dir artifacts\release\download_smoke\manual-current --verification-level quick --json-out artifacts\release\download_smoke\manual-current-summary.json
```

Historical explicit remote release:

```powershell
.venv\Scripts\python.exe tools\qa\check_release_asset_smoke.py --mode explicit-remote --repo CAPTW/OpenSourceWorkBench --tag v0.1.3-rc1 --expected-version 0.1.3rc1 --expected-target a6e8d3a8211e02359841d10e1947e16ab847b132 --download-dir artifacts\release\download_smoke\manual-v013 --verification-level quick --json-out artifacts\release\download_smoke\manual-v013-summary.json
```

Local historical asset set:

```powershell
.venv\Scripts\python.exe tools\qa\check_release_asset_smoke.py --mode local-set --tag v0.1.3-rc1 --expected-version 0.1.3rc1 --expected-target a6e8d3a8211e02359841d10e1947e16ab847b132 --asset-dir artifacts\release\download_smoke\local-v013\assets --verification-level quick
```

Offline synthetic fixture:

```powershell
.venv\Scripts\python.exe tools\qa\check_release_asset_smoke.py --mode offline-fixture --asset-dir tests\fixtures\release_assets --verification-level quick
```

## Workflow Dispatch Path

The `Release asset smoke` workflow runs `offline-fixture` with `quick` on pull
requests and `develop` pushes. Manual `workflow_dispatch` runs either
`current-live` or `explicit-remote`, with an explicit `quick` or `full-static`
selection and read-only `contents: read` permission.

## Release Asset Warnings

- The Windows portable ZIP is unsigned.
- No MSI installer or code signing is claimed.
- External solvers are not bundled.
- Optional science and solver dependencies remain user-provided tools.

See [Release Asset Download Smoke](../release/release_asset_download_smoke.md)
for the full mode and identity contract.
