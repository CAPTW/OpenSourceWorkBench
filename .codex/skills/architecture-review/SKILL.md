---
name: architecture-review
description: Review OSW changes for dependency direction, GUI/solver separation, optional extras, and v0.1 scope boundaries.
---

# Architecture Review

Use before review or merge when code, docs, or harness changes may affect OSW
architecture.

Check:
- core stays independent of GUI, solver binaries, and heavy optional extras;
- GUI does not directly run solver subprocesses;
- plugins declare preview, validation, optional extras, and limitations;
- v0.1 scope does not expand into commercial native CAD, Simulink, full
  OpenFOAM UI, or certification claims.

Run `python tools/qa/check_architecture_boundaries.py` when available.
