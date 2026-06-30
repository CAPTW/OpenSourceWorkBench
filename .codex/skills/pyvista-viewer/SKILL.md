---
name: pyvista-viewer
description: Guide optional PyVista visualization surfaces for ResultDataset and FigureDataset previews.
---

# PyVista Viewer

Use for optional visualization design. Keep imports guarded, provide fallback
messages when PyVista is unavailable, and never make visualization dependencies
mandatory for CLI smoke or unit tests. Visual outputs must state assumptions,
units, and validation limits.
