# Windows Portable ZIP

The unsigned Windows portable ZIP is a convenience artifact for the current
public `v0.1.5-rc1` prerelease. References to `v0.1.3-rc1` below identify a
historical release and never override current release authority.

## Static Verification Boundary

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

Use `--mode current-live` for the pinned current release, `--mode
explicit-remote` for a complete historical remote identity, or `--mode
local-set` for a complete identity paired with local assets. The canonical
synthetic fixture uses `--mode offline-fixture` and is not published portable
ZIP evidence.

## What This Asset Is

- An unsigned Windows portable ZIP and prerelease convenience artifact.
- A PyInstaller-style onedir bundle with a local executable and bundled Python
  runtime files.
- An artifact that a user may voluntarily extract and inspect after separately
  verifying its identity and checksums.

## What This Asset Is Not

- Not an MSI or signed installer.
- Not code-signed.
- Not a stable production release.
- Not an industrial or regulated solver platform.
- Not a bundled external solver distribution.
- Not release-readiness or engineering-correctness evidence.

External solvers such as Gmsh, GNU Octave, CalculiX `ccx`, and OpenFOAM remain
user-installed optional tools.

## Voluntary Manual Use

These are user actions, not checker behavior and not release-readiness
evidence:

1. Download the portable ZIP, `SHA256SUMS.txt`, and
   `release_asset_manifest.json` from the same selected release.
2. Verify release identity and checksums before running anything.
3. Extract the ZIP to a user-writable folder.
4. Open PowerShell in the extracted `OpenSolverWorkbench` folder.
5. Run help first:

   ```powershell
   .\OpenSolverWorkbench.exe --help
   ```

6. Launch GUI behavior only when the selected build supports it and only in a
   normal Windows desktop environment.

For `v0.1.5-rc1`, select the pinned `current-live` profile. For the historical
`v0.1.3-rc1` release, select `explicit-remote` or `local-set` with its complete
tag/version/peeled-target tuple before any voluntary manual use.

## Expected Layout

```text
OpenSolverWorkbench/
  OpenSolverWorkbench.exe
  README_RUN_FIRST.txt
  LICENSE
  _internal/
  ... bundled Python runtime files ...
```

`full-static` can inspect this layout without extraction for execution. A
warning about a missing expected member is static diagnostic evidence only.

## Troubleshooting

| Symptom | Guidance |
| --- | --- |
| Windows SmartScreen warning | The portable ZIP is unsigned and not code-signed. Verify identity, checksums, and source before choosing whether to run it. |
| Antivirus warning | Treat it as a local security decision; static checker success is not permission or runtime assurance. |
| Missing external solver | Install any optional external tool separately and use its explicit diagnostic command. |
| Path with spaces | Quote paths in PowerShell. |
| GUI does not launch | This is separate runtime evidence; the static checker neither launches nor validates the GUI. |

For the full verification contract, see
[Release Asset Download Smoke](release_asset_download_smoke.md). For future
installer and trust planning, see
[Code Signing And Installer Strategy](code_signing_installer_strategy.md).
