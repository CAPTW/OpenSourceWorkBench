# Plugin Agent Rules

This directory owns plugin/add-in contracts.

- Plugins must declare manifest metadata before behavior is wired in: id, name,
  version, type, entry point, capabilities, supported formats, optional extras,
  safety flags, and known limitations.
- Importing a plugin must not launch processes, mutate projects, write files,
  or require heavy optional dependencies unless that plugin is explicitly used.
- Importer plugins are preview-first and must summarize what will change before
  project mutation.
- Solver plugins may prepare cases and import results, but external execution
  requires a reviewed runner contract.
- Keep plugin contracts narrow enough for importers, solvers, scripts,
  post-processing, and reports to evolve independently.
- Do not add proprietary native CAD, Simulink, `.mlapp`, or industrial
  certification claims through plugin metadata.
