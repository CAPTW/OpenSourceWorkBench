# CalculiX Input Deck

`OSW-FUNC-013_CALCULIX_INPUT_DECK` adds a prepare-only CalculiX linear static
input deck writer. It generates deterministic `.inp` text from explicit
ProjectSchema, MeshModel, material, set, boundary, and load data.

## Scope

The v0.1 adapter supports:

- linear static analysis only;
- isotropic elastic materials;
- node and element writing for simple tetrahedral and hexahedral mesh blocks;
- node sets, element sets, and surface placeholders;
- fixed support boundary conditions;
- nodal force loads and pressure placeholders;
- readiness diagnostics for missing material, missing mesh topology, missing
  target sets, unsupported element types, and unmapped CFD-style boundaries.

The adapter does not run `ccx`, parse results, implement nonlinear contact,
plasticity, modal, thermal, or coupled analyses.

## Project Handoff

ProjectSchema may reference full mesh topology through solver settings or mesh
metadata:

```json
{
  "mesh_model_path": "cantilever_mesh.json",
  "node_sets": [{"name": "FIXED", "node_ids": [1, 4, 5, 8]}]
}
```

`MeshRef` summaries with counts only are not enough for input deck generation;
the writer requires full point and cell connectivity data.

## CLI

```powershell
python -m osw.cli calculix-write-inp --demo cantilever --out artifacts\calculix\cantilever.inp
python -m osw.cli calculix-deck-preview tests\fixtures\calculix\cantilever_project.json
python -m osw.cli calculix-validate-project tests\fixtures\calculix\cantilever_project.json
```

These commands do not require CalculiX installed and do not run `ccx`.

## GUI

The `CalculixDeckDialog` shows readiness diagnostics and deck text. Its write
button writes the reviewed `.inp` file only. There is no `ccx` run button in
this step.

## Security Rules

- Deck generation does not call `ExternalCommandRunner`.
- GUI code does not launch subprocesses.
- Plugin health can report a missing `ccx` executable as a warning, but deck
  generation itself does not require the executable.
- Generated runtime decks belong under `artifacts/calculix` or temporary test
  directories and should not be committed unless intentionally curated.

## Next Step

Next functional step: `OSW-FUNC-014_CALCULIX_RUNNER_BINDING`.
