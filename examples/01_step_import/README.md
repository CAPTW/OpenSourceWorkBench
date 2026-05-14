# Tutorial 01: STEP Import Preview

## Goal

Preview standard/exported geometry metadata before mutating an OSW project. The
demo teaches the import step for the v0.1 path:

```text
Import -> Configure -> Run or prepare -> Result -> Report
```

## Prerequisites

- Base OSW development install.
- A small exported geometry file, preferably STEP, ASCII STL, or OBJ.
- No commercial CAD software is required.
- STEP, IGES, and BREP currently use metadata-only bridge stubs until an
  optional CAD kernel integration is reviewed.

OSW v0.1 does not support native commercial CAD direct import. Export STEP or
STL from the source CAD tool before importing into OSW.

## Steps

1. Place a small exported geometry file in this directory or another local
   scratch path.
2. Preview the file without changing a project:

   ```python
   from pathlib import Path

   from osw.geometry.cad_importer_base import import_preview

   model = import_preview(Path("part.stl"))
   print(model.to_dict())
   ```

3. Check the preview for format, body count, bounding box, metadata, and
   warnings.
4. Record the preview summary in the project report or project metadata only
   after the user accepts the imported geometry.

## Expected Output

- STL previews list surface-mesh body metadata and an axis-aligned bounding box.
- OBJ previews list vertex and face metadata and a bounding box.
- STEP, IGES, and BREP stubs return a bounded preview message rather than a
  native CAD conversion.
- Files from unsupported proprietary CAD formats are not imported; OSW asks the
  user to export a standard STEP or STL file.

## Troubleshooting

- `Geometry file does not exist`: check the path passed to `import_preview`.
- `Unsupported geometry format`: export one of `.step`, `.stp`, `.stl`, `.obj`,
  `.iges`, `.igs`, or `.brep`.
- `STL preview currently supports ASCII STL`: export ASCII STL or use OBJ/STEP
  for the preview.
- If a CAD kernel is missing, use the metadata stub output in the report and
  keep the workflow preview-first.
