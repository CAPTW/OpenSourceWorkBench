OpenSolver Workbench
Version: {version}
Tag: {tag}

Read this before running the portable ZIP.

This is an unsigned Windows portable build. It is not an MSI installer, it is
not code-signed, and it is not a stable production or industrial-certified
solver platform.

External solver executables are not bundled. Gmsh, GNU Octave, CalculiX ccx,
OpenFOAM tools, and other optional tools must be installed separately by the
user if a workflow needs them.

Optional Python/science dependencies may be missing from this portable build.
Commands should report clear diagnostics instead of pretending that optional
workflows succeeded.

Suggested first command:

  OpenSolverWorkbench.exe --help

If the GUI is available in this build, it may require a normal Windows desktop
environment. Headless or restricted environments can fail to launch the GUI.

Verify downloaded assets before use:

  - compare SHA256SUMS.txt with the downloaded files;
  - inspect release_asset_manifest.json for the tag, target commit, file sizes,
    and SHA256 hashes.

Report issues:

  https://github.com/CAPTW/OpenSourceWorkBench/issues
