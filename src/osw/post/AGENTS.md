# Post-Processing Agent Rules

This directory owns result, figure, visualization, and report-facing adapters.

- Post-processing should consume structured ResultDataset and FigureDataset
  concepts rather than raw solver runtime directories.
- Matplotlib and PyVista integrations are optional and must use guarded imports.
- Reports and figures must include assumptions, units, validation status, and
  limitations when available.
- Do not claim industrial accuracy, compliance, or certification from demo
  outputs.
- Generated report outputs and visualization artifacts must not be committed
  unless they are curated examples or golden fixtures.
