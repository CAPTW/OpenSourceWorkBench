# Live optional validation matrix for v0.1.5-rc1

## Status

`completed-with-warnings`

OSW-VALID-005 reran the prepared-machine live optional validation matrix for
the public `v0.1.5-rc1` prerelease. The current machine was not prepared with
the optional solver and science stacks, so every target is recorded as
`skipped-missing`.

This page is historical evidence for OSW-VALID-005. Later issue-specific
prepared-machine validation and closure gates closed #6 through #11 with
bounded caveats. The `skipped-missing` rows below remain historical setup
evidence and are not the current issue state.

No dependency installation, solver installation, release mutation, tag
mutation, asset upload, issue closure, bundled solver claim, or certification
claim occurred.

## Release context

- Current public release: `v0.1.5-rc1`
- Release URL:
  https://github.com/CAPTW/OpenSourceWorkBench/releases/tag/v0.1.5-rc1
- Release state: public prerelease, not draft
- Release tag object: `88d683c2e08265c86ee419d0c70c55d93f023893`
- Release tag target: `85c8144f7ff19159ab02c40adb6483ce6b13c017`
- Develop HEAD during validation:
  `befdf917786d06ac73f296a8b7d90c59f59e3ded`
- Package/CLI version: `0.1.5rc1`
- Release assets: five expected assets remain present

## Environment discovery summary

Discovery used installed-only checks through `where.exe`, `shutil.which`, and
Python import probes. Nothing was installed or upgraded.

| Group | Discovery result |
| --- | --- |
| Gmsh | Python `gmsh`, `gmsh` executable, and `meshio` were not discovered. |
| GNU Octave | `octave` and `octave-cli` were not discovered. |
| CalculiX | `ccx` was not discovered. |
| OpenFOAM | `foamVersion`, `blockMesh`, `icoFoam`, `simpleFoam`, and `foamRun` were not discovered. |
| CoolProp / Cantera | Python `CoolProp` and `cantera` were not importable. |
| PyVista / meshio | Python `pyvista`, `vtk`, and `meshio` were not importable. |

## Per-target result

| Issue | Target | Classification | Live execution | Rationale |
| --- | --- | --- | --- | --- |
| `#6` | Gmsh | `skipped-missing` | No | Neither Python `gmsh` nor the `gmsh` executable was discovered; `meshio` was also missing. |
| `#7` | GNU Octave | `skipped-missing` | No | Neither `octave` nor `octave-cli` was discovered. |
| `#8` | CalculiX `ccx` | `skipped-missing` | No | `ccx` was not discovered, matching the OSW-VALID-004 skipped-missing condition. |
| `#9` | OpenFOAM | `skipped-missing` | No | No OpenFOAM command was discovered. |
| `#10` | CoolProp / Cantera | `skipped-missing` | No | Neither Python `CoolProp` nor `cantera` was importable. |
| `#11` | PyVista / meshio | `skipped-missing` | No | Neither Python `pyvista` nor `meshio` was importable; `vtk` was also missing. |

## Artifacts

- Artifact root:
  `artifacts/validation/live_optional/OSW-VALID-005/`
- Environment discovery:
  `artifacts/validation/live_optional/OSW-VALID-005/environment_discovery.json`
- Summary JSON:
  `artifacts/validation/live_optional/OSW-VALID-005/live_optional_validation_summary.json`
- Command log:
  `artifacts/validation/live_optional/OSW-VALID-005/command_log.txt`

The artifact root is ignored local evidence and must not be staged.

## Issue policy

- At this OSW-VALID-005 gate, issues `#6`, `#7`, `#8`, `#9`, `#10`, and `#11`
  remained open.
- Later issue-specific bounded validation and closure gates closed #6 through
  #11. Treat those later closures as scoped issue-state evidence only.
- `skipped-missing` targets are not passing live validation evidence.
- A passed installed-only target would still require a separate closure-review
  gate before issue closure.
- This gate may comment evidence on issues, but it does not close issues.

## Safety boundaries

- No dependency installation.
- No solver installation.
- No solver execution occurred because all targets were missing.
- No public release edit, create, publish, or asset mutation.
- No tag creation, tag push, all-tags push, or force push.
- No runtime source mutation.
- No bundled solver claim.
- No industrial certification or production CAE claim.

## Next action

Rerun the prepared-machine validation matrix on a machine where the intended
optional solver or science stacks are already installed. Passed installed-only
targets may then move to separate closure-review gates. Skipped, failed,
partial, or blocked targets need a prepared environment or a focused follow-up
before closure can be considered.
