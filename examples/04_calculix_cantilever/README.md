# Tutorial 04: CalculiX Cantilever

## Goal

Prepare a small linear static cantilever input deck for review. This tutorial
does not run `ccx`.

## Prerequisites

- Base OSW development install for input deck generation.
- A small mesh represented as `MeshData` or imported through the mesh tutorial.
- One isotropic elastic material with explicit units.

OSW v0.1 keeps this step bounded to linear static input deck generation.

## Steps

1. Import or create a small cantilever mesh.
2. Define an isotropic elastic material, a fixed node set, and a force or
   pressure load.
3. Generate the `.inp` deck through the CalculiX input deck generator.
4. Review validation warnings for missing material, missing boundary condition,
   unsupported cell type, or missing load.
5. Write the reviewed `.inp` deck to `artifacts/calculix` or another explicit
   output directory.
6. Keep runtime solver outputs out of the repository; solver execution and
   result parsing are owned by later functional steps.

## Expected Output

- A deterministic CalculiX `.inp` deck for a linear static cantilever.
- Clear validation messages when material, boundary conditions, or supported
  element types are missing.
- Cantilever validation can compare max displacement against `F L^3 / 3 E I`
  within the documented tolerance once a later runner/parser step supplies
  reviewed result data.

## Troubleshooting

- `Unsupported CalculiX element cell type`: export or convert to supported
  line, triangle, quad, tetra, hexahedron, wedge, or pyramid cells.
- Missing material errors require an isotropic elastic material with Young's
  modulus and Poisson ratio.
- Missing support or load warnings mean the case is not ready for a meaningful
  linear static handoff.
- `ccx` is optional. A missing executable diagnostic is acceptable for this
  tutorial unless the user explicitly wants to run the external solver.
