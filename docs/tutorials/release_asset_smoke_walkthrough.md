# Release Asset Smoke Walkthrough

This walkthrough is for maintainers who want to verify release assets. It never
uploads assets, edits a GitHub Release, creates tags, retargets tags, pushes
branches, or pushes tags.

## Offline Fixture Mode

Use this mode in CI or local checks without network access:

```powershell
.venv\Scripts\python.exe tools\qa\check_release_asset_smoke.py --offline-asset-dir tests\fixtures\release_assets
```

Expected result:
- fixture asset names are checked
- `SHA256SUMS.txt` is verified
- `release_asset_manifest.json` is verified
- archive safety checks run

## Live GitHub Release Download Mode

Use this only when GitHub CLI is installed and authenticated:

```powershell
.venv\Scripts\python.exe tools\qa\check_release_asset_smoke.py --download --full-smoke
```

This downloads assets from the public release into ignored
`artifacts/release/download_smoke/` paths. Full smoke may install the wheel and
sdist in temporary virtual environments and may inspect the Windows portable
ZIP. It does not upload, overwrite, or edit GitHub Release assets.

## Workflow Dispatch Path

The repository also has a `Release asset smoke` workflow:
- pull requests and `develop` pushes run offline fixture checks
- live GitHub release downloads are manual `workflow_dispatch` only
- workflow permissions are read-only
- `full_smoke=true` is optional maintainer evidence

See [Release Asset Download Smoke](../release/release_asset_download_smoke.md)
for details.

## Release Asset Warnings

- The Windows portable ZIP is unsigned.
- No MSI installer is provided.
- No code signing is claimed.
- External solvers are not bundled.
- Optional science/solver dependencies remain local user-provided tools.
