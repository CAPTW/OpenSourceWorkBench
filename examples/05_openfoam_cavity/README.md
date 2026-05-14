# Tutorial 05: OpenFOAM Cavity And Duct Templates

## Goal

Generate bounded OpenFOAM template case files for the cavity and duct demos
without turning OSW into a full OpenFOAM case editor.

## Prerequisites

- Base OSW development install for template generation.
- Optional OpenFOAM installation only if the user chooses to run the generated
  case outside OSW.
- A scratch output directory outside the repository for generated case
  directories.

Template generation does not execute OpenFOAM.

## Steps

1. Generate a lid-driven cavity case:

   ```python
   from pathlib import Path

   from osw.solvers.openfoam.case_generator import (
       OpenFoamCavityConfig,
       generate_cavity_case,
   )

   generated = generate_cavity_case(
       OpenFoamCavityConfig(case_name="cavity"),
       Path("scratch/openfoam"),
   )
   print(generated.relative_paths)
   ```

2. For the duct tutorial, generate an internal duct case with inlet velocity,
   outlet pressure, and wall no-slip settings:

   ```python
   from pathlib import Path

   from osw.solvers.openfoam.case_generator import (
       OpenFoamDuctConfig,
       generate_duct_case,
   )

   generated = generate_duct_case(
       OpenFoamDuctConfig(case_name="duct", solver="simpleFoam"),
       Path("scratch/openfoam"),
   )
   print(generated.relative_paths)
   ```

3. Review generated `0`, `constant`, and `system` files before any external
   execution.
4. Record case parameters, patch names, warnings, and generated file list in
   the HTML report.

## Expected Output

- Cavity files: `0/U`, `0/p`, `constant/transportProperties`, and standard
  `system` dictionaries including `blockMeshDict`.
- Duct files: inlet, outlet, walls, front/back patch settings and solver choice
  placeholder for `icoFoam` or `simpleFoam`.
- Warnings for missing or invalid boundary and patch names.
- A residual parser interface placeholder for later result import.

## Troubleshooting

- Invalid `case_name`: use letters, numbers, underscores, or hyphens.
- Missing patch names fall back to template defaults with warnings; review those
  warnings before running externally.
- OpenFOAM is optional. If it is missing, keep the generated case as the
  tutorial output.
- Generated OpenFOAM runtime directories, processor folders, and logs should
  not be committed unless curated as small fixtures.
