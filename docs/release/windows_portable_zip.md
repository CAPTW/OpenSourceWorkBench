# Windows Portable ZIP

The Windows portable ZIP is a convenience artifact for the public
`v0.1.3-rc1` prerelease. It is intended for quick inspection of OSW CLI and,
when supported by the build, GUI launch behavior after extracting a single
folder.

## What This Asset Is

- A Windows portable ZIP.
- A prerelease convenience artifact.
- A PyInstaller-style onedir bundle with a local executable and bundled Python
  runtime files.
- A way to run `OpenSolverWorkbench.exe --help` without setting up a source
  checkout first.

## What This Asset Is Not

- Not an MSI installer.
- Not a signed installer.
- Not code-signed.
- Not a stable production release.
- Not an industrial-certified solver platform.
- Not a bundled external solver distribution.

External solvers such as Gmsh, GNU Octave, CalculiX `ccx`, and OpenFOAM remain
user-installed optional tools.

## How To Use

1. Download `OpenSolverWorkbench-v0.1.3rc1-windows-x64-portable.zip` from the
   GitHub Release.
2. Download `SHA256SUMS.txt` and `release_asset_manifest.json` from the same
   release.
3. Verify checksums before running the executable.
4. Extract the ZIP to a user-writable folder, for example under your Downloads
   or Documents directory.
5. Open PowerShell in the extracted `OpenSolverWorkbench` folder.
6. Run help first:

   ```powershell
   .\OpenSolverWorkbench.exe --help
   ```

7. If GUI support is present in the build, launch it only in a normal Windows
   desktop environment.

## Expected Layout

```text
OpenSolverWorkbench/
  OpenSolverWorkbench.exe
  README_RUN_FIRST.txt
  LICENSE
  _internal/
  ... bundled Python runtime files ...
```

Older prerelease builds may differ slightly. The release asset smoke checker
records those differences as warnings rather than mutating or rejecting the
already-published asset.

## Troubleshooting

| Symptom | Guidance |
| --- | --- |
| Windows SmartScreen warning | The portable ZIP is unsigned and not code-signed. Verify checksums and source before running. |
| Antivirus warning | Treat as a local security decision; verify the release checksums and inspect the source release. |
| Missing external solver | Install the external tool separately and ensure it is on `PATH`, then use the relevant `*-check` command. |
| Optional dependency missing | Some solver/science workflows require optional packages that may not be bundled. The command should report diagnostics. |
| Path with spaces | Use quotes around paths in PowerShell if needed. |
| Non-ASCII path | If launch fails, retry from a simple ASCII path such as `C:\Users\<you>\Documents\OSW\`. |
| GUI does not launch | Use `--help` and CLI commands first; GUI launch requires a Windows desktop environment. |

## Safety And Limitations

- Unsigned portable build.
- No MSI installer.
- No code signing.
- No industrial certification or production CAE claim.
- External solvers are not bundled.
- Optional scientific packages may be absent.
- Engineering results must be independently validated.

## Verification

Use the release asset smoke checker for local or downloaded assets:

```powershell
.venv\Scripts\python.exe tools\release\check_release_assets.py `
  --repo CAPTW/OpenSourceWorkBench `
  --tag v0.1.3-rc1 `
  --download `
  --download-dir artifacts\release\download_smoke\v0.1.3-rc1_auto `
  --expected-version 0.1.3rc1 `
  --full-smoke
```

The checker verifies `SHA256SUMS.txt`, `release_asset_manifest.json`, safe
archive structure, portable ZIP UX warnings, and optional executable `--help`
smoke on Windows.

The same checker is wired into the `Release asset smoke` GitHub Actions
workflow. Pull requests and `develop` pushes use offline fixtures; live release
asset download smoke remains a manual `workflow_dispatch` check.

## Future Improvements

- MSI or installer strategy.
- Code signing.
- Better first-run launcher.
- GUI-specific portable smoke.
- Clearer optional solver discovery in packaged builds.
