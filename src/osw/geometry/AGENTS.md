# Geometry Agent Rules

This directory owns standard/exported geometry preview contracts.

- Support only standard/exported formats in v0.1, such as STEP-facing preview
  workflows when dependencies are available.
- Do not implement native SolidWorks, CATIA, NX, Creo, or other commercial CAD
  direct import.
- Geometry importers must preview metadata and validation messages before
  mutating a project.
- Keep CAD-kernel dependencies optional and isolated behind adapter boundaries.
- User-facing text must clearly distinguish standard/exported file support from
  commercial native CAD support.
