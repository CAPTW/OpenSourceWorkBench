# OpenFOAM template v12 pFinal fix design

## 1. Status

Design-only.

This gate carries: no source edits, no template edits, no golden fixture edits,
no solver execution, no live validation, no issue mutation, no release/tag/asset
mutation, no ProjectSchema mutation, no ProjectSchema evidence, and no
certification claim. It defines a fix contract only; it does not implement it.

## 2. Purpose

Design a **variant/algorithm-aware** fix for the OpenFOAM Foundation v12
`system/fvSolution/solvers` `pFinal` blocker so that generated PISO/`icoFoam`
cases run end-to-end on OpenFOAM Foundation v11/v12 **without changing**
SIMPLE/`simpleFoam` behavior or regressing legacy/ESI cases. This design
addresses GitHub issue #19 as a design only, and preserves the issue #18
relationship (physicalProperties).

## 3. Finding summary

- The OSW-EXP-142 Foundation v11/v12 generated cavity case correctly emits
  `constant/physicalProperties` (issue #18 fix), and `blockMesh` runs (exit 0).
- `icoFoam` then reads `physicalProperties`, reads fields `p`/`U`, enters the
  time loop, solves `Ux`/`Uy`/`p` (first corrector), and **fails** with
  `keyword pFinal is undefined in dictionary ".../system/fvSolution/solvers"`.
- The OSW cavity/duct `fvSolution/solvers` blocks define only `p` and `U`;
  `pFinal` appears **nowhere** in tracked source/tests/docs.
- This is a **separate** template gap from the `physicalProperties` fix: it is in
  `system/fvSolution` (not `constant/`), and it is an OpenFOAM 12 solver-entry
  requirement for the PISO **final corrector**, not a property-file concern.

## 4. Evidence basis

- GitHub issue **#19** — "OpenFOAM 12 cavity template should include pFinal solver
  entry" (OPEN; labels `bug`, `optional-dependency`, `live-solver`).
- GitHub issue **#18** — "OpenFOAM cavity template should support OpenFOAM 12
  physicalProperties" (OPEN); tracks the property-file fix implemented by
  OSW-EXP-142.
- Live validation evidence root:
  `artifacts/validation/OSW-VALID-OPENFOAM_TEMPLATE_V12_COMPATIBILITY_LIVE_VALIDATION_7ada538/`.
- Log evidence: `Reading physicalProperties` (success) and
  `keyword pFinal is undefined` (fatal) in the generated Foundation cavity
  `log.icoFoam`; `log.blockMesh` exit 0.
- Source inspection: `src/osw/solvers/openfoam/case_generator.py` (embedded cavity
  `_EMBEDDED_TEMPLATES` and duct `_EMBEDDED_DUCT_TEMPLATES` `fvSolution`) and
  `src/osw/solvers/openfoam/templates/cavity/system/fvSolution` define `p` and `U`
  solvers with a `PISO` block (cavity) or `$algorithm_block` (duct); no `pFinal`.
- Caveats: validation is **WSL-only**, not native Windows; `foamVersion` is an
  operator-created `/usr/local/bin/foamVersion` delegation wrapper to the OpenFOAM
  Foundation openfoam12 shell function; **no certification** or
  production-readiness claim is made.

## 5. Affected algorithms and cases

The `pFinal` requirement is an **algorithm** concern (PISO final pressure solve),
not a property-file/variant concern:

- **PISO / `icoFoam` cavity**: affected (cavity is always `icoFoam`). Requires
  `pFinal`.
- **SIMPLE / `simpleFoam` duct default**: **not affected** — steady-state SIMPLE
  has no final-corrector `pFinal` solve and must remain unchanged.
- **Duct configured with `icoFoam`** (PISO `$algorithm_block`): potentially
  affected — the duct `fvSolution` also lacks `pFinal`, so an `icoFoam` duct would
  hit the same error. Requires `pFinal` when the PISO algorithm is selected.
- **PIMPLE** (if supported later): uses `*Final` fields too and would require a
  separate review; out of scope here.

The property-file layout (`OpenFOAMPropertyFileLayout`, legacy vs
`foundation_v11_plus`) does **not** change `fvSolution`; the cavity `fvSolution`
is identical for both layouts, so the `pFinal` addition is keyed on **algorithm**,
not on the property-file layout.

## 6. Supported variant/version policy

- **PISO/`icoFoam` cases (all variants)**: emit `pFinal`. OpenFOAM Foundation
  v11/v12 **requires** it; older Foundation and ESI OpenFOAM **tolerate** an extra
  `pFinal` solver entry (unused entries are ignored). Adding `pFinal` universally
  for PISO is therefore both **required** for OF12 and **safe** for legacy/ESI.
- **SIMPLE/`simpleFoam` cases**: **do not** emit `pFinal` (no final-corrector
  pressure solve). Preserve existing behavior exactly.
- **Unknown/unsupported algorithm**: do not guess — preserve legacy behavior or
  emit a diagnostic rather than inventing solver entries.

This algorithm-gated policy avoids the two failure modes: (a) missing `pFinal` in
OF12 PISO cases, and (b) spurious `pFinal` in SIMPLE cases.

## 7. fvSolution layout policy

Recommended implementation approach: **minimal, algorithm-conditional insertion**
of a `pFinal` entry into the `fvSolution/solvers` dictionary for PISO cases,
driven by the existing solver/algorithm selection (`OpenFOAMSolverKind` /
the duct `_duct_solver_settings` algorithm block), rather than duplicating whole
`fvSolution` templates.

Options considered for the `pFinal` entry:

- **Separate explicit `pFinal { $p; relTol 0; }`** (preferred). Mirrors the
  OpenFOAM 12 `icoFoam` cavity tutorial convention: macro-expand the `p` solver
  settings via `$p`, then override `relTol` to `0` for the tight final solve. It
  is explicit, self-documenting, and unambiguous in golden fixtures.
- **Regex key `"(p|pFinal)"`** applied to the existing `p` block. Compact, but
  `$p`/relTol nuances are lost (the final corrector would reuse the base `relTol`),
  and regex keys read less clearly in a teaching template and in golden diffs.
- **Variant/algorithm-specific whole `fvSolution` template**. Heavier; duplicates
  shared content and increases fixture drift.

**Preferred**: the explicit `pFinal { $p; relTol 0; }` entry for PISO cases. A
generated PISO `fvSolution/solvers` should contain `p`, `pFinal`, and `U`; a
generated SIMPLE `fvSolution/solvers` should contain `p` and `U` only.

## 8. Version/algorithm selection policy

Future selection inputs, in preference order:

- the **solver kind** already carried by the request/config (`OpenFOAMSolverKind`
  — `icoFoam` ⇒ PISO ⇒ `pFinal`; `simpleFoam` ⇒ SIMPLE ⇒ no `pFinal`);
- the **algorithm** implied by the existing duct `algorithm_block` selection;
- the **template kind** (`OpenFOAMTemplateKind`: cavity is always PISO/`icoFoam`);
- an explicit user option only if a future need arises.

Constraints:

- **No background detection** and **no solver execution** for selection.
- `pFinal` presence is decided from the already-selected algorithm/solver, not by
  probing OpenFOAM.
- **Unknown** solver/algorithm combinations should preserve legacy behavior or
  emit a diagnostic rather than guessing.

## 9. Command/API impact

Likely affected surface (implementation-time only; not changed here):

- `src/osw/solvers/openfoam/case_generator.py` — cavity `_EMBEDDED_TEMPLATES`
  `fvSolution`, duct `_EMBEDDED_DUCT_TEMPLATES` `fvSolution`, and the
  `_duct_solver_settings` / context that assembles the solver dictionary.
- `src/osw/solvers/openfoam/templates/cavity/system/fvSolution` (on-disk cavity
  template).
- generated-case metadata (record whether `pFinal` was emitted).
- `OpenFOAMSolverKind` / `OpenFOAMTemplateKind` (read for algorithm decision; no
  new members required unless the design gate finds one necessary).
- `openfoam-write-case` (no new flag expected; behavior follows the selected
  template/solver).
- OpenFOAM docs and unit/golden tests.

This gate does not implement any of these.

## 10. Backward compatibility

- **SIMPLE/`simpleFoam` behavior must remain unchanged** — no `pFinal` added to
  steady-state cases.
- The **issue #18 physicalProperties fix must not regress** — `fvSolution` changes
  are independent of the `constant/` property-file layout.
- Existing golden fixtures either gain `pFinal` intentionally (the cavity, which is
  always PISO) or remain unchanged (the duct `simpleFoam` default).
- Do **not** add `pFinal` to SIMPLE-only cases; do not remove `p` or `U`.

## 11. Golden fixture strategy

Future implementation (OSW-EXP-144) should:

- **Update** the cavity `fvSolution` golden fixture(s) to include `pFinal` (the
  cavity is always `icoFoam`/PISO): `tests/golden/openfoam/cavity/system/fvSolution`
  (shared by both property-file layouts).
- **Preserve** the duct `simpleFoam` (SIMPLE) `fvSolution` golden fixture
  **without** `pFinal`: `tests/golden/openfoam/duct/system/fvSolution`.
- **Add** a duct `icoFoam`/PISO `fvSolution` golden fixture **with** `pFinal` only
  if the duct exposes that configuration in tests.
- Keep the OSW-EXP-142 Foundation v12 `physicalProperties` fixtures unchanged
  (they are `constant/` files, unaffected by `fvSolution`).
- Assert `pFinal` **presence** for PISO and **absence** for SIMPLE.

## 12. Test strategy

Future implementation should test:

- cavity Foundation v12 (PISO) `fvSolution` **emits** `pFinal`;
- cavity (PISO) `fvSolution` still **keeps** `p` (and `U`);
- cavity Foundation v12 still emits `constant/physicalProperties` (no regression);
- legacy cavity behavior preserved (still PISO, still gains `pFinal`, still uses
  `transportProperties` in legacy layout);
- duct `simpleFoam` (SIMPLE) `fvSolution` does **not** gain `pFinal`;
- duct `icoFoam` (PISO) `fvSolution` **gains** `pFinal` (if the configuration is
  exercised);
- generated `pFinal` content uses `relTol 0` (tight final solve);
- **no** unit test runs OpenFOAM or requires an OpenFOAM executable;
- **no** network or dependency install;
- bounded OpenFOAM live validation only in a separate validation gate.

## 13. Diagnostics vocabulary

Reserve design-only diagnostic codes:

- `OSW_OPENFOAM_FVSOLUTION_PFINAL_REQUIRED`
- `OSW_OPENFOAM_FVSOLUTION_PFINAL_MISSING`
- `OSW_OPENFOAM_FVSOLUTION_PFINAL_ADDED`
- `OSW_OPENFOAM_FVSOLUTION_PISO_FINAL_PRESSURE`
- `OSW_OPENFOAM_FVSOLUTION_SIMPLE_NO_PFINAL`
- `OSW_OPENFOAM_FVSOLUTION_VARIANT_UNSUPPORTED`
- `OSW_OPENFOAM_FVSOLUTION_GENERATION_BLOCKED`

These are reserved names for a future implementation; they trigger no runtime
behavior in this gate.

## 14. Documentation strategy

Future docs should explain:

- the PISO **final pressure solve** and why OpenFOAM 12 `icoFoam` looks up
  `pFinal`;
- why `pFinal` is needed for the OF12 cavity but **not** for SIMPLE/`simpleFoam`;
- the relationship to the `physicalProperties` fix (a separate `constant/` file);
- how the `pFinal` entry is derived from the selected algorithm/solver;
- the **WSL-only** evidence caveat and the `foamVersion` wrapper caveat.

## 15. Validation strategy

Future validation should include:

- unit/golden tests in the implementation gate (OSW-EXP-144);
- a bounded **WSL OpenFOAM live validation retry** of the generated Foundation
  cavity case, expecting `icoFoam` to run **end-to-end** (time directories beyond
  `0`);
- no broad solver workload;
- **no certification**, **no production readiness**, and **no native Windows
  validation** claim unless native Windows evidence exists.

## 16. Issue #19 relationship

- This design addresses issue **#19** as a design only.
- Issue **#19 must remain open** until implementation and live validation occur.
- **No issue mutation** occurs in this gate.

## 17. Issue #18 relationship

- Issue **#18**'s physicalProperties fix is implemented (OSW-EXP-142) and
  **partially validated** (OpenFOAM 12 reads `physicalProperties`).
- Issue **#18 remains open** until the generated cavity runs `icoFoam`
  **end-to-end**, which additionally requires the issue #19 `pFinal` fix.
- Issue #19 is a **separate blocker** that must land before #18 can be fully
  validated end-to-end.

## 18. Non-actions

This gate performs: no source edits, no template edits, no golden fixture edits,
no solver execution, no live validation, no issue mutation, no release/tag/asset
mutation, no version bump, no ProjectSchema mutation, no ProjectSchema evidence,
no dependency/solver install, no certification claim, no production-readiness
claim, no bundled-solver support claim, and no native-Windows-validation claim.

## 19. Future gates

- `OSW-EXP-144_OPENFOAM_TEMPLATE_V12_PFINAL_FIX_IMPLEMENTATION` — implement the
  algorithm-aware `pFinal` `fvSolution` generation + tests + golden fixtures +
  docs.
- `OSW-VALID-OPENFOAM_TEMPLATE_V12_COMPATIBILITY_LIVE_VALIDATION` — bounded live
  OpenFOAM validation retry of the generated Foundation cavity (expect end-to-end
  `icoFoam`).
- `OSW-OPENFOAM_TEMPLATE_V12_COMPATIBILITY_ISSUE_UPDATE_PLAN` — plan issue #18/#19
  updates once implementation and end-to-end validation exist.
- optional `OSW-OPENFOAM_TEMPLATE_V12_PFINAL_ISSUE_UPDATE_PLAN` — plan an issue #19
  update once the fix is implemented and validated.

Package metadata remains `0.1.5rc1`; public prerelease remains `v0.1.5-rc1`;
issues `#18` and `#19` remain open.

## 20. Implementation follow-up (OSW-EXP-144)

This design was implemented in `OSW-EXP-144` — see
[OpenFOAM template v12 pFinal fix implementation](openfoam_template_v12_pfinal_fix_implementation.md).
The implementation adds a `_PFINAL_SOLVER_BLOCK` (`pFinal { $p; relTol 0; }`)
injected via a `$pfinal_block` placeholder into the cavity/duct `fvSolution`
`solvers` dictionary: the cavity always gets it (always `icoFoam`), the duct gets
it only for `icoFoam` (PISO), and `simpleFoam` (SIMPLE) output is unchanged. The
cavity golden fixture gains `pFinal`; the duct golden fixture is unchanged; unit
tests never run a solver. Issues #18 and #19 remain open; end-to-end live
validation stays a separate gate.
