# OpenFOAM template v12 compatibility fix design

## 1. Status

Design-only.

This gate carries: no source edits, no template edits, no golden fixture edits, no
solver execution, no live validation, no issue mutation, no release/tag/asset
mutation, no ProjectSchema mutation, no ProjectSchema evidence, and no
certification claim. It defines a fix contract only; it does not implement it.

## 2. Purpose

Design a **version/variant-aware** fix for the OpenFOAM `openfoam-write-case`
template/case generator so that generated cases run on OpenFOAM Foundation v11/v12
(which require `constant/physicalProperties`) **without breaking** OpenFOAM
variants that still use `constant/transportProperties` (ESI OpenFOAM and older
Foundation releases). This design addresses GitHub issue #18 as a design only.

## 3. Finding summary

- The current OSW template/case generator emits `constant/transportProperties`.
- OpenFOAM Foundation v11/v12 expects `constant/physicalProperties`, and `icoFoam`
  aborts with `cannot find file ".../constant/physicalProperties"` when only
  `transportProperties` is present.
- OpenFOAM Foundation 12's own official `icoFoam` cavity tutorial (which ships
  `physicalProperties`) ran successfully end-to-end during live validation.
- The OSW-generated cavity case therefore appears incompatible with OpenFOAM
  Foundation v12.
- This is a **template/case-generation** issue, not proof that OpenFOAM is
  unavailable: OpenFOAM is genuinely installed and functional (mesh generation and
  a real solver run were verified).

## 4. Evidence basis

- GitHub issue **#18** — "OpenFOAM cavity template should support OpenFOAM 12
  physicalProperties" (open at design time; labels `bug`, `optional-dependency`).
- Live validation evidence root:
  `artifacts/validation/OSW-VALID-OPTIONAL_LIVE_SOLVER_EVIDENCE_4f17c81/`
  (OSW template case + `solver.log` failing on missing `physicalProperties`; the
  OF12 official tutorial case running end-to-end).
- Source inspection: `src/osw/solvers/openfoam/case_generator.py` hardcodes
  `template_paths` including `constant/transportProperties` for both the cavity and
  duct generators; `src/osw/solvers/openfoam/templates/cavity/constant/transportProperties`
  exists; golden fixtures under `tests/golden/openfoam/**` assume
  `constant/transportProperties`; no tracked `physicalProperties` exists.
- Caveats: validation was **WSL-only**, not native Windows; `foamVersion` is a
  shell function in all OpenFOAM variants and the validation used an
  operator-created `/usr/local/bin/foamVersion` delegation wrapper; **no
  certification** or production-readiness claim is made.

## 5. Supported variant/version policy

The design targets these OpenFOAM families:

- **OpenFOAM Foundation <= 10** (openfoam.org, legacy Foundation): use
  `constant/transportProperties`.
- **OpenFOAM Foundation >= 11** (openfoam.org, including v11 and Foundation
  v11/v12): use `constant/physicalProperties`.
- **ESI OpenFOAM** (openfoam.com, e.g. v1912–v25xx): use
  `constant/transportProperties`.
- **Unknown/unspecified variant**: do not guess; require an explicit selection or
  emit a diagnostic and (optionally) a conservative default with a compatibility
  warning.

This policy explicitly avoids a **blanket rename** of `transportProperties` to
`physicalProperties`, which would break ESI and older Foundation cases.

## 6. Template layout policy

Future implementation should generate the correct property file per variant. The
recommended approach is a **data-model-driven property file** (parameterize the
file name and content by variant) rather than duplicating whole template trees;
variant-specific files (`constant/transportProperties` vs
`constant/physicalProperties`) may also be kept as small variant fragments.

Expected files:

- `constant/transportProperties` (legacy Foundation <= 10 and ESI)
- `constant/physicalProperties` (Foundation >= 11 / v11/v12)

A generated case should contain **exactly one** of these files for the selected
variant by default; emitting both is allowed only if a future gate explicitly
decides it is safe for the target OpenFOAM family.

## 7. Version/variant selection policy

Future selection inputs, in preference order:

- an **explicit CLI/user option** (e.g. `--openfoam-flavor` / `--openfoam-version`
  / a variant enum extending the existing `OpenFOAMTemplateKind`/`OpenFOAMSolverKind`
  models);
- an **adapter option** passed from calling code;
- **detected `foamVersion`** (only if already available and read passively);
- an **environment-derived variant**;
- a documented **fallback/compatibility mode**.

Constraints:

- **No background detection** is designed or performed in this gate.
- **No solver execution** is required for selection.
- **Unsafe or unknown variants** should require an explicit user choice, or park
  generation with a diagnostic, rather than silently guessing.

## 8. Command/API impact

Likely affected surface (implementation-time only; not changed here):

- `openfoam-write-case` (CLI command)
- `src/osw/solvers/openfoam/case_generator.py` (cavity + duct generators,
  `template_paths`)
- `src/osw/solvers/openfoam/adapter.py`
- `src/osw/solvers/openfoam/validation.py` / `residual_parser.py` (verify no
  assumptions break)
- OpenFOAM docs
- OpenFOAM unit/integration/golden tests

This gate does not implement any of these.

## 9. Backward compatibility

Older Foundation (<= 10) and ESI support must be **preserved**. Non-goal: do not
remove `transportProperties` support without a separate, explicit deprecation
policy/gate. Existing default behavior must remain available (e.g. via
the legacy/ESI variant selection) so current users and fixtures are not broken.

## 10. Golden fixture strategy

- **Add** a Foundation v12 fixture that includes `constant/physicalProperties`.
- **Retain** the legacy `transportProperties` fixture (ESI / Foundation <= 10).
- Add **expected-path assertions** (which property file is present for which
  variant).
- Keep fixtures deterministic and **avoid unbounded solver execution** in unit
  tests.

## 11. Test strategy

Future implementation (OSW-EXP-142) should test:

- variant selection (each input path resolves to the intended variant);
- generated file **names** (`transportProperties` vs `physicalProperties`);
- generated file **content**;
- no both-files ambiguity unless explicitly chosen;
- legacy behavior preserved (default/legacy variant still emits
  `transportProperties`);
- Foundation v12 behavior emits `physicalProperties`;
- CLI/help/output diagnostics;
- golden fixture updates (cavity and duct);
- **no network**;
- **no solver execution** in unit tests;
- optional bounded OpenFOAM live validation only in a separate validation gate.

## 12. Diagnostics vocabulary

Reserve design-only diagnostic codes:

- `OSW_OPENFOAM_TEMPLATE_VARIANT_UNSPECIFIED`
- `OSW_OPENFOAM_TEMPLATE_VARIANT_UNSUPPORTED`
- `OSW_OPENFOAM_TEMPLATE_FOUNDATION_V12_PHYSICAL_PROPERTIES`
- `OSW_OPENFOAM_TEMPLATE_LEGACY_TRANSPORT_PROPERTIES`
- `OSW_OPENFOAM_TEMPLATE_VARIANT_DETECTION_UNAVAILABLE`
- `OSW_OPENFOAM_TEMPLATE_COMPATIBILITY_WARNING`
- `OSW_OPENFOAM_TEMPLATE_GENERATION_BLOCKED`

These are reserved names for a future implementation; they trigger no runtime
behavior in this gate.

## 13. Documentation strategy

Future docs should explain:

- OpenFOAM **Foundation vs ESI** differences;
- `transportProperties` vs `physicalProperties`;
- how users **select** a variant;
- what is auto-detected, if anything (and that detection is passive/optional);
- limitations;
- the **WSL-only** evidence caveat and the `foamVersion` wrapper caveat.

## 14. Validation strategy

Future validation should include:

- source/unit/golden tests in the implementation gate (OSW-EXP-142);
- optional **WSL OpenFOAM live validation** in a separate validation gate;
- **no certification**, **no production readiness**, and **no native Windows
  validation** claim unless native Windows evidence exists.

## 15. Issue #18 relationship

- This design addresses issue **#18** as a design only.
- At design time, issue **#18 had to remain open** until implementation and
  validation occurred.
- **No issue mutation** occurs in this gate.

## 16. Non-actions

This gate performs: no source edits, no template edits, no golden fixture edits,
no solver execution, no issue mutation, no release/tag/asset mutation, no version
bump, no ProjectSchema mutation, no ProjectSchema evidence, no dependency/solver
install, no certification claim, no production-readiness claim, no bundled-solver
support claim, and no native-Windows-validation claim.

## 17. Future gates

- `OSW-EXP-142_OPENFOAM_TEMPLATE_V12_COMPATIBILITY_FIX_IMPLEMENTATION` — implement
  the variant-aware property-file generation + tests + golden fixtures + docs.
- `OSW-VALID-OPENFOAM_TEMPLATE_V12_COMPATIBILITY_LIVE_VALIDATION` — bounded live
  OpenFOAM validation of the generated case in a prepared environment.
- `OSW-OPENFOAM_TEMPLATE_V12_COMPATIBILITY_ISSUE_UPDATE_PLAN` — plan an issue #18
  update once implementation and validation exist.

Package metadata remains `0.1.5rc1`; public prerelease remains `v0.1.5-rc1`.
At design time, issues `#6` through `#11` and `#18` remained open.

## 18. Implementation follow-up (OSW-EXP-142)

This design was implemented in `OSW-EXP-142` — see
[OpenFOAM template v12 compatibility fix implementation](openfoam_template_v12_compatibility_fix_implementation.md).
The implementation adds an explicit `OpenFOAMPropertyFileLayout` selector
(`legacy` → `constant/transportProperties`, `foundation_v11_plus` →
`constant/physicalProperties`) with the legacy layout preserved as the default,
a `--property-file-layout` CLI option on `openfoam-write-case`, Foundation
v11/v12 golden fixtures alongside the retained legacy fixtures, and unit tests
that never run a solver. Later WSL-scoped validation plus the `pFinal` follow-up
provided the issue-specific evidence used to close issues #18 and #19. Issue #9
and optional validation issues #6 through #11 remain open and separate.
