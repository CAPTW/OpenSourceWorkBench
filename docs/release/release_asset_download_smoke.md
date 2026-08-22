# Release Asset Download Smoke

This page documents the read-only, identity-bound release asset checker. The
current public prerelease is `v0.1.5-rc3`. The published `v0.1.5-rc2`, `v0.1.5-rc1`, and `v0.1.3-rc1` asset sets
remain available as explicit historical verification examples.

The checker never uploads assets, edits a GitHub Release, creates or retargets
tags, pushes Git refs, or overwrites release assets.

## Assurance Boundary

The checker verifies release identity and static consistency only. `quick`
reports `IDENTITY_BOUND_QUICK`; `full-static` adds static package and
portable-layout inspection and reports `IDENTITY_BOUND_FULL_STATIC`. Both set
`release_readiness=false`. Neither level extracts or installs a package,
imports downloaded code, runs a downloaded CLI, launches
`OpenSolverWorkbench.exe`, proves runtime behavior, establishes engineering
correctness, or establishes publication readiness.

`quick` verifies the selected identity, exact asset inventory, nonzero file
sizes, `SHA256SUMS.txt`, `release_asset_manifest.json`, and safe archive member
names. `full-static` adds static wheel, sdist, and portable-layout inspection.
Neither level executes artifact content.

Immutable target authority is the annotated Git tag object peeled to its exact
40-hex commit. GitHub Release `target_commitish` is display context only and
cannot override the selected profile or caller-supplied target.

## Explicit Modes

- `current-live` uses the repository-pinned `v0.1.5-rc1` repository, version,
  annotated tag, and peeled target profile. Identity overrides are rejected.
- `explicit-remote` requires one complete caller-supplied repository, tag,
  version, and peeled-target tuple.
- `local-set` requires one complete caller-supplied tag, version, and
  peeled-target tuple plus a local asset directory.
- `offline-fixture` accepts only `tests/fixtures/release_assets` and only the
  `quick` level.

Remote modes require `--download-dir` and reject `--asset-dir`. Local modes
require `--asset-dir` and reject `--download-dir`. Every invocation must select
`--verification-level quick` or `--verification-level full-static` explicitly.

## Command Contracts

Current live release:

```powershell
.venv\Scripts\python.exe tools\qa\check_release_asset_smoke.py --mode current-live --download-dir artifacts\release\download_smoke\manual-current --verification-level quick --json-out artifacts\release\download_smoke\manual-current-summary.json
```

Explicit historical remote release:

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

Use `--verification-level full-static` only when the additional static package
and portable-layout inspection is required. It does not add installation,
import, CLI, executable, runtime, engineering, or release-readiness evidence.

## Frozen Offline Fixture

`tests/fixtures/release_assets` is a frozen synthetic, non-installable
fixture. It is not a byte snapshot of the published `v0.1.3-rc1` assets and
supplies no remote provenance.

The fixture checks deterministic parsing, hashing, manifest comparison, archive
member safety, result shape, and fail-closed behavior without network access.
It cannot establish anything about current GitHub Release state.

## CI And Manual GitHub Actions

The `Release asset smoke` workflow uses read-only `contents: read` permission.
Pull requests and `develop` pushes run `offline-fixture` at `quick`. A manual
`workflow_dispatch` selects `current-live` or `explicit-remote` and separately
selects `quick` or `full-static`. Live summaries are uploaded only as workflow
artifacts; they are not GitHub Release assets.

4. Use `tag=v0.1.3-rc1` for the public prerelease current at the time of this smoke validation.

That sentence is a historical workflow record. Current live authority is the
pinned `v0.1.5-rc1` profile; historical identities must use `explicit-remote`.

## Portable ZIP Guidance

The portable ZIP is unsigned. It is not an MSI installer, is not code-signed,
and does not bundle external solvers. The checker only inspects it statically.
Voluntary manual extraction and launch are separate user actions documented in
[Windows Portable ZIP](windows_portable_zip.md); they are not checker behavior
or release-readiness evidence.

For the distinction between checksums, artifact attestations, code signing,
and installer packaging, see
[Code Signing And Installer Strategy](code_signing_installer_strategy.md).

## Troubleshooting

| Symptom | Meaning / action |
| --- | --- |
| GitHub CLI is unavailable or unauthenticated | Use `local-set` or `offline-fixture`, or separately establish read-only GitHub access. |
| Selected mode rejects an argument | Supply only the atomic identity and path arguments allowed by that explicit mode. |
| Asset inventory, checksum, or manifest mismatch | Treat the selected asset set as invalid and investigate without executing it. |
| Annotated tag or peeled target mismatch | Treat the selected release identity as invalid; `target_commitish` cannot repair it. |
| Forbidden archive member | Treat the archive as unsafe; do not distribute or manually extract it. |
| `release_readiness=false` | Expected: this checker never establishes publication readiness. |
