# OpenSolver Workbench v0.1.5-rc1 candidate

## Status

Metadata aligned, tag/release/assets not created.

This gate aligns package and CLI metadata for the future `v0.1.5-rc1`
candidate only. It does not create a Git tag, create or edit a GitHub Release,
build assets, upload assets, execute solvers, or mutate issues.

## Current public release

`v0.1.4-rc1` remains the current public prerelease:

- release URL: https://github.com/CAPTW/OpenSourceWorkBench/releases/tag/v0.1.4-rc1
- release state: public prerelease, not draft
- release tag target: `f1683b441ab308fd65318ef6de3f1282549946a1`
- public assets: wheel, sdist, Windows portable ZIP, `SHA256SUMS.txt`, and
  `release_asset_manifest.json`

## Target

- Package version: `0.1.5rc1`
- Future tag: `v0.1.5-rc1`
- Future release title: `OpenSolver Workbench v0.1.5-rc1`

The future tag and release are intentionally absent after this metadata gate.

## Scope basis

The `v0.1.5-rc1` boundary is based on the post-experimental
ResultDataset/FEASpec capability line after the public `v0.1.4-rc1` tag:

- FEASpec model, validator, and ProjectSchema bridge work;
- CalculiX case planning, no-run `.inp` renderer, exporter, and CLI
  preview/write paths;
- installed-only CalculiX run-gate implementation;
- result import model and preview CLI;
- metadata, `.sta`/`.cvg`, `.dat`, and `.frd` scanners/parsers;
- ResultDataset draft mapping, write plan, schema payload, library writer,
  write CLI, and write GUI review-file persistence flow.

## Validation state

Issues `#6` through `#11` remain open as live optional validation work:

- `#6` Gmsh
- `#7` GNU Octave
- `#8` CalculiX `ccx`
- `#9` OpenFOAM
- `#10` CoolProp / Cantera
- `#11` PyVista / meshio

Issue `#8` remains `skipped-missing` because `ccx` was absent on the
OSW-VALID-004 machine. No live CalculiX pass is recorded by this metadata
alignment.

## Non-actions

- no tag in this gate;
- no release create/edit/publish;
- no asset build/upload;
- no issue closure;
- no solver execution;
- no dependency install or upgrade.

## Required next gates

1. `OSW-RELEASE-033_V0_1_5RC1_FINAL_REVALIDATION_NO_TAG`
2. local annotated tag creation
3. tag-only push gate
4. asset build from tag
5. release draft and asset upload gate
6. public release publish gate
7. post-public release audit

## Risks

- `v0.1.5-rc1` remains a prerelease candidate until later release gates pass.
- The Windows portable ZIP remains unsigned unless a later signing gate changes
  that.
- External solvers are not bundled.
- Live optional validation is environment-dependent.

## Do-not-claim notes

- `v0.1.5-rc1` is not a public release yet.
- No `v0.1.5-rc1` assets yet.
- No live CalculiX pass yet.
- No certification.
