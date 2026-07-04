# OpenFOAM template v12 compatibility fix implementation

## 1. Status

Implementation complete (`OSW-EXP-142`).

- Implements the variant/version-aware OpenFOAM property-file generation
  designed in
  [OpenFOAM template v12 compatibility fix design](openfoam_template_v12_compatibility_fix_design.md)
  (`OSW-EXP-141`) and tracked by GitHub issue #18.
- **No live solver validation** occurs in this gate: no OpenFOAM execution, no
  `blockMesh`/`icoFoam`/`simpleFoam`/`foamVersion` invocation, and no unit test
  that requires an installed OpenFOAM.
- **No issue mutation**: issue #18 stays OPEN for a later validation/update gate.
- **No certification**, production-readiness, bundled-solver, or
  native-Windows-validation claim is made.
- Package metadata remains `0.1.5rc1`; public prerelease remains `v0.1.5-rc1`.

## 2. Public API / option names

- `OpenFOAMPropertyFileLayout` (in `osw.solvers.openfoam.model`), a `StrEnum`:
  - `LEGACY_TRANSPORT_PROPERTIES = "legacy"` (default)
  - `FOUNDATION_V11_PLUS_PHYSICAL_PROPERTIES = "foundation_v11_plus"`
- `OpenFoamCavityConfig.property_file_layout` and
  `OpenFoamDuctConfig.property_file_layout` (default: legacy).
- `OpenFoamGeneratedCase.property_file_layout` and the `property_file` property
  (relative path of the emitted constant property file).
- `resolve_property_file_layout(value)` — resolves an enum/alias/`None` to a
  layout, raising `OpenFoamCaseTemplateError` for unknown spellings.
- `property_file_for_layout(layout)` and `layout_diagnostic_code(layout)`.
- CLI: `openfoam-write-case --property-file-layout {legacy,foundation_v11_plus}`
  (default `legacy`).

All symbols are re-exported from `osw.solvers.openfoam`.

## 3. Variant / version policy

- **Legacy** layout (`legacy`) → `constant/transportProperties`. Targets ESI
  OpenFOAM (openfoam.com) and OpenFOAM Foundation <= 10 (openfoam.org).
- **Foundation v11+** layout (`foundation_v11_plus`) →
  `constant/physicalProperties`. Targets OpenFOAM Foundation v11/v12.
- Selection is **explicit** (config field, request metadata, or CLI option). No
  background detection and no `foamVersion` invocation are performed.
- Unknown/unsupported selectors are **not guessed**: they raise a deterministic
  `OpenFoamCaseTemplateError` tagged `OSW_OPENFOAM_TEMPLATE_VARIANT_UNSUPPORTED`
  (surfaced as an `openfoam-case-generation-failed` diagnostic in the request
  flow).
- Accepted aliases resolve case-insensitively with `-`/`_` normalized: legacy
  accepts `legacy`, `transportProperties`, `esi`, `foundation_v10`, `v10`;
  foundation accepts `foundation_v11_plus`, `foundation_v11`, `foundation_v12`,
  `physicalProperties`, `v11`, `v12`.

This is a **variant-aware swap, never a blanket rename**: a generated case emits
exactly one of the two property files for the selected layout.

## 4. Template layout behavior

The generators keep their legacy `template_paths` (which list
`constant/transportProperties`). At generation time
`_apply_property_file_layout()` rewrites that single entry to
`constant/physicalProperties` for the Foundation v11/v12 layout and leaves every
other file untouched. The property files are pure text templates rendered
through the existing `string.Template` path with the standard generated header.

The Foundation `physicalProperties` content mirrors OpenFOAM Foundation 12's own
`icoFoam` cavity tutorial (captured as live evidence): a single
`nu [0 2 -1 0 0 0 0] <viscosity>;` entry and no `transportModel` key. Turbulence
handling is unchanged — the duct still emits `constant/turbulenceProperties`
(`simulationType laminar;`) in both layouts.

## 5. Legacy behavior preservation

- The default layout is legacy for every config, the request flow, and the CLI.
- Existing golden fixtures (`tests/golden/openfoam/cavity`,
  `tests/golden/openfoam/duct`) and existing unit tests are unchanged and still
  pass.
- No `transportProperties` template or fixture was removed. Removing legacy
  support is explicitly **out of scope** and would require a separate deprecation
  gate.

## 6. Foundation v11/v12 behavior

- Cavity and duct both emit `constant/physicalProperties` (and not
  `constant/transportProperties`) when the Foundation layout is selected.
- The generated `physicalProperties` includes the expected dimensioned `nu`
  entry with the case viscosity.

## 7. CLI behavior

`openfoam-write-case` gains `--property-file-layout` (default `legacy`). The
selected layout is threaded into the request metadata and echoed back:

```powershell
python -m osw.cli openfoam-write-case --template cavity --out-dir artifacts\openfoam\cavity
python -m osw.cli openfoam-write-case --template cavity --property-file-layout foundation_v11_plus --out-dir artifacts\openfoam\cavity12
python -m osw.cli openfoam-write-case --template duct --property-file-layout foundation_v11_plus --out-dir artifacts\openfoam\duct12
```

The command prints `Property file layout:` and `Property file:` lines. It still
does not run OpenFOAM.

## 8. Golden fixture updates

- Added `tests/golden/openfoam/cavity_foundation_v12/constant/physicalProperties`
  (viscosity `0.01`).
- Added `tests/golden/openfoam/duct_foundation_v12/constant/physicalProperties`
  (viscosity `1e-05`).
- Added `tests/golden/openfoam/test_openfoam_foundation_v12_golden.py` comparing
  generated Foundation cases against these fixtures and asserting the legacy file
  is absent.
- Legacy golden fixtures are retained unchanged.

## 9. Test coverage

- `tests/unit/test_openfoam_template_v12_compatibility.py` covers: default =
  legacy; legacy/foundation alias resolution; unknown-layout error; cavity and
  duct legacy vs foundation file names/content; shared-file preservation;
  request-flow metadata for both layouts and the duct; request-flow unknown
  layout diagnostic; CLI option presence/help; CLI legacy/default/foundation
  output for cavity and duct; and a generator-source scan asserting no subprocess
  execution.
- Golden coverage as in §8.
- No unit test runs OpenFOAM, requires an OpenFOAM executable, installs
  dependencies, or uses the network. Generated cases use `tmp_path`.

## 10. Diagnostics / errors

- `OSW_OPENFOAM_TEMPLATE_VARIANT_UNSUPPORTED` — raised/reported for unknown
  layout selectors.
- `OSW_OPENFOAM_TEMPLATE_FOUNDATION_V12_PHYSICAL_PROPERTIES` and
  `OSW_OPENFOAM_TEMPLATE_LEGACY_TRANSPORT_PROPERTIES` — informational codes
  surfaced in `OpenFOAMCaseResult.metadata["property_file_diagnostic"]`. Normal
  generation stays status `ok` (no new warnings), so existing callers/tests are
  unaffected.

## 11. Relationship to issue #18

- This gate implements the source fix requested by issue #18.
- Issue #18 remains **OPEN**; it is closed only after a separate live-validation
  gate confirms the generated Foundation case runs, followed by an explicit
  issue-update gate. No issue mutation occurs here.

## 12. Validation still required

- `OSW-VALID-OPENFOAM_TEMPLATE_V12_COMPATIBILITY_LIVE_VALIDATION` — bounded live
  OpenFOAM validation of the generated Foundation `physicalProperties` case in a
  prepared environment (WSL-only evidence; discloses the `foamVersion` wrapper
  caveat).
- No certification, production-readiness, or native-Windows-validation claim is
  made until such evidence exists.

## 13. Non-actions

No live solver execution, no OpenFOAM runtime validation, no issue mutation, no
issue comment/closure, no release/tag/asset mutation, no version bump, no
ProjectSchema mutation, no ProjectSchema evidence, no dependency/solver install,
no certification claim, no production-readiness claim, no bundled-solver claim,
and no native-Windows-validation claim.

## 14. Future gates

- `OSW-VALID-OPENFOAM_TEMPLATE_V12_COMPATIBILITY_LIVE_VALIDATION` — live
  validation of the generated case.
- `OSW-OPENFOAM_TEMPLATE_V12_COMPATIBILITY_ISSUE_UPDATE_PLAN` /
  `..._ISSUE_UPDATE_APPLY` — plan and apply an issue #18 update once
  implementation and validation exist.

## 15. Follow-up: pFinal fvSolution gap (issue #19)

Live validation (`OSW-VALID-OPENFOAM_TEMPLATE_V12_COMPATIBILITY_LIVE_VALIDATION`)
confirmed this physicalProperties fix works — OpenFOAM 12 `icoFoam` reads
`constant/physicalProperties` — but the generated Foundation cavity does **not**
yet run `icoFoam` end-to-end: it fails on a **separate** `system/fvSolution`
`pFinal` gap, tracked by issue #19 and designed in
[OpenFOAM template v12 pFinal fix design](openfoam_template_v12_pfinal_fix_design.md)
(`OSW-EXP-143`). Issue #18 remains open until both fixes land and the cavity runs
`icoFoam` end-to-end.
