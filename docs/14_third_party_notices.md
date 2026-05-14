# Third-Party Notices Draft

This draft supports OSW v0.1 source-distribution review. It distinguishes the
OpenSolver Workbench repository source from optional runtime tools and optional
Python dependencies that users may install locally.

This document is not legal advice and does not assert that every redistribution
obligation is finally resolved. Maintainers should review dependency licenses,
binary redistribution terms, source-offer requirements, notices, and platform
packaging choices before publishing source, wheel, or standalone artifacts.

## Distribution Boundary

- OSW repository source is licensed as `GPL-3.0-or-later`.
- v0.1 release artifacts do not bundle external solver binaries by default.
- CalculiX, OpenFOAM tools, Gmsh, GNU Octave, SU2, and similar executables are
  optional user-installed runtime tools unless a future packaging review
  explicitly approves redistribution.
- Cantera, CoolProp, PySide6, meshio, PyVista, SciPy, hdf5storage, and related
  libraries are optional Python dependencies or optional extras unless the
  release artifact explicitly includes them.
- Plugin manifests should document the plugin license, dependency expectations,
  optional executable requirements, and user-visible limitations.

## Notice Review Areas

| Category | v0.1 use | Distribution expectation | Review notes |
| --- | --- | --- | --- |
| PySide6 / Qt | Optional GUI shell. | Optional Python extra; not required by base CLI/unit tests. | Review Qt/PySide package license terms before any bundled desktop artifact. |
| PyVista / VTK | Optional visualization and contour placeholders. | Optional Python extra. | Review VTK/PyVista notices if wheels are redistributed. |
| meshio | Standard mesh import/export surface. | Optional Python extra. | Keep mesh fixtures curated and small. |
| Gmsh | Optional meshing template integration and executable/SDK availability. | Optional local dependency; no bundled Gmsh binary by default. | Review SDK/binary redistribution separately if packaging changes. |
| CalculiX | Optional linear static demo runner and input/result handoff. | Optional local external solver; no bundled `ccx` binary by default. | Source and binary redistribution obligations require maintainer review. |
| OpenFOAM | Cavity and duct template examples. | Optional local external solver; no bundled OpenFOAM tools by default. | Do not imply full OpenFOAM UI or broad solver coverage. |
| GNU Octave | Optional `.m` execution path after preview and user trigger. | Optional local external executable; no bundled Octave binary by default. | `.m` workflows remain preview-first and untrusted until reviewed. |
| SciPy | Optional `.mat` and script-data support. | Optional Python extra for script workflows. | Review transitive notices if redistributed in artifacts. |
| hdf5storage / MAT v7.3 reader | Optional MAT v7.3 reader support. | Optional Python extra. | Keep missing dependency diagnostics explicit. |
| Cantera | Optional 0D reactor demo. | Optional Python dependency or environment package. | Mechanism files and bundled data require separate source/license review. |
| CoolProp | Optional property calculator demo. | Optional Python dependency or environment package. | Property references are educational and not process-simulator claims. |

## Artifact Policy

- Source distributions and wheels should include repository source, docs, tests,
  curated fixtures, and license files only when packaging metadata is ready.
- Do not include generated solver runtime directories, external solver logs,
  uncontrolled reports, `dist/`, `build/`, `wheelhouse/`, or solver binaries.
- Standalone desktop packages require a separate dependency and redistribution
  review before publication.

## Plugin Notice Expectations

Plugin manifests should include a license field and dependency declarations so
users can review add-in terms before installation or activation. Manifest
validation must not execute plugin code, launch processes, perform network
checks, or import heavy optional dependencies merely to display metadata.

Third-party plugins remain responsible for their own license terms and notices.
OSW may report plugin metadata, but it does not certify third-party plugin
license compatibility.
