# Release Tooling

This directory contains maintainer-only helpers for release verification.

## Asset Download Smoke

`check_release_assets.py` verifies GitHub Release assets without mutating the
release. It can either inspect a local asset directory or download assets with
`gh release download` and then verify them.

The tool never uploads assets, edits a GitHub Release, pushes Git refs, creates
tags, retargets tags, or overwrites release assets.

Typical local verification:

```powershell
.venv\Scripts\python.exe tools\release\check_release_assets.py `
  --asset-dir artifacts\release\download_smoke\v0.1.3-rc1 `
  --tag v0.1.3-rc1 `
  --expected-version 0.1.3rc1
```

Typical GitHub download verification:

```powershell
.venv\Scripts\python.exe tools\release\check_release_assets.py `
  --repo CAPTW/OpenSourceWorkBench `
  --tag v0.1.3-rc1 `
  --download `
  --download-dir artifacts\release\download_smoke\v0.1.3-rc1_auto `
  --expected-version 0.1.3rc1
```
