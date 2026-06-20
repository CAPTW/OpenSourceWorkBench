# Post-experimental ResultDataset scope review

## Status

`completed-with-open-validation`

This review records the state after the FEASpec/CalculiX ResultDataset write
GUI line and the OSW-VALID-004 live CalculiX run-gate check. It is a
docs/tests-only scope review. It does not add runtime source behavior, execute
solvers, close issues, or mutate release, tag, or asset state.

## Release context

- Public release: `v0.1.4-rc1`
- Public release URL:
  https://github.com/CAPTW/OpenSourceWorkBench/releases/tag/v0.1.4-rc1
- Release tag target: `f1683b441ab308fd65318ef6de3f1282549946a1`
- Current metadata and CLI version: `0.1.4rc1`
- `develop` is newer than the public release tag because it now contains
  substantial post-release FEASpec and ResultDataset experimental work.
- No release, tag, or asset mutation is performed by this review.

## Completed FEASpec/ResultDataset scope

The completed post-release experimental line now includes:

- FEASpec models, examples, benchmark seeds, validator reports, and
  FEASpec-to-ProjectSchema bridge planning/implementation.
- CalculiX case planning, case-plan model, deterministic no-run `.inp`
  rendering, controlled golden fixtures, no-run exporter, CLI preview, and
  CLI write bundle paths.
- Installed-only CalculiX run gate implementation with explicit
  execute/confirmation/README gates.
- FEASpec CalculiX result import model and preview CLI.
- Result artifact metadata scanning, `.sta`/`.cvg` status scanning, `.dat`
  section scanning and bounded minimal parsing, and `.frd` block/reference
  scanning.
- ResultDataset draft mapping, write design, write plan, schema payload, and
  library writer.
- Result import write CLI.
- ResultDataset write GUI flow through view-model, dialog, output-directory
  selection, writer integration, post-write polish, and ResultDataset write GUI
  closure.

This completed scope is review-file persistence and inspection workflow
evidence. It is not live solver validation, a certification claim, or a signal
that optional solver validation issues should be closed.

## Validation status

`OSW-VALID-004_LIVE_CALCULIX_RUN_GATE_VALIDATION_IF_INSTALLED` ran after the GUI
write closure.

- Result: `skipped-missing`
- CalculiX `ccx` was not discovered on this machine.
- No installed-only run gate was executed.
- No solver execution occurred.
- Issue `#8` remains open.

The skipped-missing result is useful environment evidence only. It is not a
pass, not a fail, and not a live CalculiX validation success.

## Open optional validation

Issues `#6` through `#11` remain the open live optional validation track:

- `#6` Gmsh
- `#7` GNU Octave
- `#8` CalculiX `ccx`
- `#9` OpenFOAM
- `#10` CoolProp / Cantera
- `#11` PyVista / meshio

These issues require prepared machines with the relevant optional executable or
package already installed. This review does not install dependencies or run
validation.

## Safety boundaries preserved

- no bundled solvers;
- no solver install;
- no dependency install;
- no solver execution;
- no certification claims;
- no ProjectSchema mutation;
- no VLM API or provider credentials;
- no release mutation;
- no tag mutation;
- no asset upload or deletion;
- no issue creation, comment, or closure.

## Release boundary implications

`develop` contains substantial post-`v0.1.4-rc1` work while version metadata
still reports `0.1.4rc1`. The public release tag remains fixed at
`f1683b441ab308fd65318ef6de3f1282549946a1`.

A future release-boundary decision is required before publishing any new
release assets. That decision should decide whether the accumulated
post-release FEASpec/ResultDataset work remains on the current development
line, moves to a new prerelease boundary, or waits for more prepared-machine
validation evidence.

## Recommended next paths

- Prepared-machine live optional validation for issues `#6` through `#11`,
  especially a rerun of OSW-VALID-004 with `ccx` already installed.
- A release-boundary decision gate before any new version metadata, tag,
  release asset, or GitHub Release work.
- Future parser or visualization extensions only through separate planned
  gates with explicit scope and QA.

## Non-goals

- no issue closure;
- no release edit;
- no release creation or publish;
- no asset upload or deletion;
- no tag creation or push;
- no version bump;
- no runtime source changes;
- no live validation claim;
- no solver installation or execution.

## Next recommended action

- `OSW-PLAN-008_POST_EXP_RELEASE_BOUNDARY_DECISION`
- or rerun `OSW-VALID-004_LIVE_CALCULIX_RUN_GATE_VALIDATION_IF_INSTALLED` on a
  prepared machine with `ccx` already installed.

Follow-up release-boundary decision:
[Post-experimental release-boundary decision](../release/post_exp_release_boundary_decision.md)
selects `v0.1.5-rc1` as the next prerelease boundary because `develop`
contains substantial post-`v0.1.4-rc1` experimental capability. The decision
does not bump metadata, create a tag, build assets, edit a release, or close
issues.
