# Post-experimental release-boundary decision

## Status

`completed`

This is a decision-only release-boundary gate after the post-`v0.1.4-rc1`
FEASpec/CalculiX ResultDataset experimental line. It does not align metadata,
create tags, edit releases, build assets, upload assets, execute solvers, or
mutate issues.

## Current public release

- Current public release: `v0.1.4-rc1`
- Release state: public prerelease, not draft
- Release URL:
  https://github.com/CAPTW/OpenSourceWorkBench/releases/tag/v0.1.4-rc1
- Release tag target: `f1683b441ab308fd65318ef6de3f1282549946a1`
- Release assets: wheel, sdist, Windows portable ZIP, `SHA256SUMS.txt`, and
  `release_asset_manifest.json`

## Current develop

- Current develop HEAD: `212f76949be9d3877929f6161728bb512f3aa004`
- Current package and CLI metadata still report `0.1.4rc1`
- `develop` is newer than the public `v0.1.4-rc1` tag
- Metadata is not aligned for the selected target by this gate

## Evidence reviewed

- [Post-experimental ResultDataset scope review](../roadmap/post_exp_resultdataset_scope_review.md)
- [Live CalculiX run-gate validation for v0.1.4-rc1](../validation/live_calculix_run_gate_validation_v0_1_4rc1.md)
- [FEASpec CalculiX result write GUI closure review](../experimental/feaspec_calculix_result_write_gui_closure_review.md)
- Git history and diff summary from `v0.1.4-rc1` through current `develop`

## Change classification

Feature-level additions:

- FEASpec IR/model/validator and bridge layers.
- CalculiX case planning, no-run `.inp` renderer, golden fixtures, exporter,
  CLI preview, and CLI write bundle paths.
- Installed-only CalculiX run gate implementation.
- Result import model and preview CLI.
- Metadata, status, `.dat`, and `.frd` scanner/parser layers.
- ResultDataset draft mapping, write plan, schema payload, library writer, and
  result import write CLI.
- ResultDataset write GUI view-model, dialog, output-directory chooser, writer
  integration, post-write polish, and closure review.

Validation state:

- OSW-VALID-004 classified live CalculiX validation as `skipped-missing`
  because `ccx` was missing.
- No live solver execution occurred.
- Issues `#6` through `#11` remain open for prepared-machine optional
  validation.

Docs/test/QA state:

- Documentation now covers the post-release FEASpec/CalculiX ResultDataset
  line, live optional validation state, scope guardrails, risk register,
  release checklist, and decision log.
- Focused tests, unit tests, GUI evidence, Ruff, and release/scope/docs
  guardrails exist for the accumulated work.

Release-impacting user-visible changes:

- The accumulated work is a substantial experimental capability line beyond
  the public `v0.1.4-rc1` release tag.
- The work is not merely corrective release-candidate polish for the same
  `v0.1.4` prerelease boundary.

Non-release-runtime risks:

- Live optional validation remains environment-dependent.
- Version metadata still reports `0.1.4rc1` until a later metadata-alignment
  gate.
- External solvers remain optional and not bundled.

## Open validation

- `#6` Gmsh remains open.
- `#7` GNU Octave remains open.
- `#8` CalculiX `ccx` remains open; OSW-VALID-004 is `skipped-missing`
  because `ccx` was missing.
- `#9` OpenFOAM remains open.
- `#10` CoolProp / Cantera remains open.
- `#11` PyVista / meshio remains open.

## Decision

Selected decision: `v0.1.5-rc1`

## Rationale

`v0.1.5-rc1` is the correct next boundary because `develop` contains a large
post-`v0.1.4-rc1` experimental capability line rather than a small corrective
candidate polish set. The FEASpec/CalculiX sequence adds new model,
validation, bridge, export, run-gate, result-import, parser/scanner,
ResultDataset write, CLI, and GUI review-file workflows. That scope is
substantial enough to warrant a new minor prerelease candidate boundary.

The skipped-missing live CalculiX validation does not block the boundary
decision, but it keeps issue `#8` and the live optional validation track open.
The boundary decision is not a release, not a validation pass, and not metadata
alignment.

## What this gate does not do

- no version bump;
- no metadata alignment;
- no selected-target metadata alignment;
- no tag creation;
- no release edit;
- no release creation;
- no release publish;
- no asset build;
- no asset upload;
- no issue closure.

The selected target release tag does not exist as a result of this gate. The
selected target release assets do not exist as a result of this gate.

## Required next gates

If maintainers proceed with the selected boundary, the required next gates are:

1. `OSW-RELEASE-032_V0_1_5RC1_METADATA_ALIGNMENT`
2. final revalidation for the selected target
3. local annotated tag creation gate
4. tag-only push gate
5. asset build-from-tag gate
6. release draft, asset upload, publish, and post-public audit gates

Prepared-machine live optional validation may run before or after metadata
alignment, but it remains separate from this release-boundary decision.

## Risk notes

- Live optional validation remains environment-dependent.
- Issue `#8` remains open after skipped-missing evidence.
- The public release remains prerelease.
- The Windows portable ZIP remains unsigned.
- No MSI/code signing is currently provided.
- External solvers are optional and not bundled.
- There is no industrial certification claim.

## Next recommended action

`OSW-RELEASE-032_V0_1_5RC1_METADATA_ALIGNMENT`
