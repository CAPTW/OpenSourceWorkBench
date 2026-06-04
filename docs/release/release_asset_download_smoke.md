# Release Asset Download Smoke

This page documents the reusable release asset download smoke added for Issue
`#2`. It turns the manual `v0.1.3-rc1` asset verification into a repeatable
local QA command.

The smoke checker verifies downloaded release assets only. It does not upload
assets, edit a GitHub Release, create tags, retarget tags, push branches, push
tags, or overwrite existing release assets.

## Expected v0.1.3-rc1 Assets

- `open_solver_workbench-0.1.3rc1-py3-none-any.whl`
- `open_solver_workbench-0.1.3rc1.tar.gz`
- `OpenSolverWorkbench-v0.1.3rc1-windows-x64-portable.zip`
- `SHA256SUMS.txt`
- `release_asset_manifest.json`

## Offline Local Verification

Use this when assets were already downloaded to a local directory:

```powershell
.venv\Scripts\python.exe tools\release\check_release_assets.py `
  --asset-dir artifacts\release\download_smoke\v0.1.3-rc1 `
  --tag v0.1.3-rc1 `
  --expected-version 0.1.3rc1 `
  --json-out artifacts\release\download_smoke\v0.1.3-rc1\summary.json
```

Offline verification checks expected asset presence, nonzero file sizes,
`SHA256SUMS.txt`, `release_asset_manifest.json`, and safe archive structure.

## GitHub Download Verification

Use this when GitHub CLI is installed and authenticated:

```powershell
.venv\Scripts\python.exe tools\release\check_release_assets.py `
  --repo CAPTW/OpenSourceWorkBench `
  --tag v0.1.3-rc1 `
  --download `
  --download-dir artifacts\release\download_smoke\v0.1.3-rc1_auto `
  --expected-version 0.1.3rc1 `
  --json-out artifacts\release\download_smoke\v0.1.3-rc1_auto\summary.json
```

If the target download directory already contains files, the tool creates a
timestamped subdirectory unless `--reuse-dir` is passed.

## Full Smoke

Add `--full-smoke` to run deeper checks:

- install the downloaded wheel in a fresh virtual environment;
- run `python -m osw.cli --version` and `--help`;
- extract and optionally install the sdist in a separate virtual environment;
- extract the Windows portable ZIP safely;
- run `OpenSolverWorkbench.exe --help` on Windows unless
  `--skip-portable-exe` is provided.

The portable ZIP is unsigned. It is not an MSI installer, not code-signed, and
does not bundle external solvers. Optional solver/science dependencies remain
local user-provided tools.

The checker also records portable ZIP UX warnings, including missing or
incomplete `README_RUN_FIRST.txt` guidance, missing checksum guidance, missing
license files, multi-folder layouts, and absent `OpenSolverWorkbench.exe`.
Warnings do not mutate or overwrite already-published assets.

For user-facing portable ZIP guidance, see
[Windows Portable ZIP](windows_portable_zip.md).

## QA Wrapper

The QA wrapper defaults to the public `v0.1.3-rc1` release:

```powershell
.venv\Scripts\python.exe tools\qa\check_release_asset_smoke.py --full-smoke
```

For CI-safe offline runs, provide a local asset directory:

```powershell
.venv\Scripts\python.exe tools\qa\check_release_asset_smoke.py `
  --offline-asset-dir tests\fixtures\release_assets
```

## Troubleshooting

| Symptom | Meaning / action |
| --- | --- |
| `gh` is unavailable or unauthenticated | Run offline verification or authenticate with `gh auth login`. |
| Checksum mismatch | Treat the asset set as invalid; redownload and compare with the published release. |
| Manifest mismatch | Inspect `release_asset_manifest.json` against the downloaded files before relying on the assets. |
| Portable executable `--help` fails | Rerun with `--skip-portable-exe` only to isolate archive/hash checks, then investigate the portable build separately. |
| Path traversal or forbidden archive entry | Treat the archive as unsafe; do not extract or distribute it. |

## Limitations

- The tool verifies assets; it does not publish or mutate the release.
- Full wheel and portable smoke can be platform-specific.
- The Windows portable ZIP is unsigned and may trigger operating-system trust
  prompts outside this automated smoke.
- Optional solvers, MATLAB/Octave tools, and science backends are not bundled.
