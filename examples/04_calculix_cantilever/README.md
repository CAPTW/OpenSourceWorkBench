# Tutorial 04: CalculiX Cantilever

## Goal

Prepare a small linear static cantilever input deck and connect the result
summary to OSW report and validation surfaces.

## Prerequisites

- Base OSW development install for input deck generation.
- A small mesh represented as `MeshData` or imported through the mesh tutorial.
- One isotropic elastic material with explicit units.
- Optional `ccx` executable only if the user chooses to run CalculiX outside the
  GUI workflow.

OSW v0.1 keeps CalculiX bounded to linear static educational handoff and result
summary parsing.

## Steps

1. Import or create a small cantilever mesh.
2. Define an isotropic elastic material, a fixed node set, and a force or
   pressure load.
3. Generate the `.inp` deck through the CalculiX input deck generator.
4. Review validation warnings for missing material, missing boundary condition,
   unsupported cell type, or missing load.
5. Optionally run `ccx` outside the GUI through the reviewed runner boundary and
   keep runtime outputs out of the repository unless they are curated fixtures.
6. Parse a small `.dat` result summary and include max displacement, max stress,
   assumptions, and validation notes in the report.

## Expected Output

- A deterministic CalculiX `.inp` deck for a linear static cantilever.
- Clear validation messages when material, boundary conditions, or supported
  element types are missing.
- Optional run artifacts tracked as `.dat`, `.frd`, `.sta`, and logs when the
  backend runner is explicitly used.
- Cantilever validation can compare max displacement against `F L^3 / 3 E I`
  within the documented tolerance.

## Troubleshooting

- `Unsupported CalculiX element cell type`: export or convert to supported
  line, triangle, quad, tetra, hexahedron, wedge, or pyramid cells.
- Missing material errors require an isotropic elastic material with Young's
  modulus and Poisson ratio.
- Missing support or load warnings mean the case is not ready for a meaningful
  linear static handoff.
- `ccx` is optional. A missing executable diagnostic is acceptable for this
  tutorial unless the user explicitly wants to run the external solver.
