# Next experimental line selection

## Status

`completed`

This planning-only gate selects the next experimental line after the
`v0.1.5-rc1` release flow, post-public audits, release-body cleanup,
maintenance hardening, and prepared-machine optional validation discovery.
It does not implement the selected line.

## Current baseline

- Current public release: `v0.1.5-rc1`
- Release state: public prerelease, not draft
- Release URL: https://github.com/CAPTW/OpenSourceWorkBench/releases/tag/v0.1.5-rc1
- Release flow: closed
- Fresh post-public audit: passed
- Release body note: corrected
- Maintenance hardening: complete
- Live optional validation: `skipped-missing` in OSW-VALID-005 on this
  machine because the target optional solver and science stacks were absent.

## Open validation

- `#6` Gmsh validation remains open.
- `#7` GNU Octave validation remains open.
- `#8` CalculiX `ccx` validation remains open.
- `#9` OpenFOAM validation remains open.
- `#10` CoolProp / Cantera validation remains open.
- `#11` PyVista / meshio validation remains open.
- OSW-VALID-005 classified all `#6` through `#11` targets as
  `skipped-missing`.

## Candidate lines

- Prepared-machine validation retry planning
- FEASpec / VFEA workflow expansion
- ResultDataset parser extension planning
- ProjectSchema integration hardening
- Plugin ecosystem / optional solver manifest UX
- Maintenance / monitoring continuation
- Pause active experimental work

## Decision

Selected line: `Plugin ecosystem / optional solver manifest UX`

## Rationale

The release flow is closed, the fresh public asset audit passed, and release
body wording has been corrected. The latest prepared-machine validation pass
did not find any target optional solver or science stack, so another immediate
validation retry on the same environment would only repeat `skipped-missing`
evidence.

The selected line addresses the clearest product gap exposed by that evidence:
users and maintainers need better optional dependency discovery, plugin
manifest guidance, health status, and installation hint design. This work can
improve diagnostics and prepared-machine readiness while preserving the OSW
rule that external solvers remain optional, unbundled, and never installed by
default.

Skipped-missing live validation does not block this planning line because the
selected work is about manifest and health UX design, not claiming installed
solver capability. It also does not provide issue-closure evidence for issues
`#6` through `#11`.

## Non-actions

- No source implementation was performed.
- No release edit was performed.
- No issue mutation was performed.
- No solver execution was performed.
- No dependency install was performed.
- No version bump was performed.

## Next recommended gate

`OSW-EXP-055_OPTIONAL_SOLVER_MANIFEST_UX_DESIGN`

The next gate should remain design-scoped: define optional solver/plugin
manifest fields, health statuses, missing-dependency explanations, and UX
guardrails without installing dependencies, bundling solvers, executing
solvers, editing releases, or closing validation issues.

## Design follow-up

The follow-up
[optional solver manifest UX design](../experimental/optional_solver_manifest_ux_design.md)
defines the initial design-only contract for stack manifests, health states,
future CLI/GUI surfaces, plugin-provided manifest trust boundaries, validation
relationships, and safety/privacy limits. It keeps implementation split into
later gates for manifest schema models, discovery service design, CLI doctor
preview, and GUI health panel design.

The next follow-up
[optional solver manifest schema model](../experimental/optional_solver_manifest_schema_model.md)
implements only the typed declarative schema/model layer, JSON helpers,
structural diagnostics, and built-in manifest records. It still does not
implement discovery, CLI commands, GUI panels, health-check execution, solver
execution, dependency installation, issue mutation, or release mutation.

## Guardrails

- External solvers are not bundled.
- No certification claim is made.
- Live validation remains environment-dependent.
- Optional solver manifest UX must not become solver installation,
  automatic execution, validation pass evidence, or issue closure evidence.
