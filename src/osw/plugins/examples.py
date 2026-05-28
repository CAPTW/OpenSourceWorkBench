"""Built-in manifest records for OSW preview bridges.

These helpers return data-only manifests. They do not import or execute plugin
implementations, optional dependencies, or external tools.
"""

from __future__ import annotations

from osw.plugins.manifest import PluginManifest


def builtin_meshio_plugin_manifest() -> PluginManifest:
    """Return the data-only manifest for the meshio import bridge."""

    return PluginManifest.from_dict(
        {
            "id": "osw.meshio",
            "name": "meshio Mesh Import Bridge",
            "version": "0.1.0",
            "domain": "MESH",
            "type": "mesh_importer",
            "license": "MIT-compatible dependency bridge",
            "description": (
                "Imports standard/exported mesh metadata through the optional "
                "meshio dependency without running external tools."
            ),
            "input_formats": [
                "msh",
                "inp",
                "bdf",
                "nas",
                "fem",
                "su2",
                "vtk",
                "vtu",
                "xdmf",
                "xmf",
                "cgns",
                "med",
            ],
            "output_formats": ["vtu", "vtk", "xdmf"],
            "requires": [],
            "optional_requires": ["meshio"],
            "executable_names": [],
            "capabilities": [
                "mesh_info",
                "mesh_conversion",
                "project_mesh_ref_binding",
            ],
            "metadata": {
                "built_in": True,
                "preview_first": True,
                "no_external_execution": True,
            },
        }
    )


def builtin_mscript_preview_plugin_manifest() -> PluginManifest:
    """Return the data-only manifest for previewing `.m` files."""

    return PluginManifest.from_dict(
        {
            "id": "osw.mscript_preview",
            "name": "MATLAB/Octave Script Preview Importer",
            "version": "0.1.0",
            "domain": "MATH",
            "type": "script_importer",
            "license": "GPL-compatible",
            "description": (
                "Reads MATLAB/Octave .m files as text and MATLAB .mat files as "
                "data previews without running scripts or launching MATLAB/Octave."
            ),
            "input_formats": ["m", "mat"],
            "output_formats": [
                "script_preview",
                "script_ref",
                "figure_dataset",
                "workspace_summary",
                "png",
                "svg",
                "pdf",
                "csv",
            ],
            "requires": [],
            "optional_requires": ["scipy", "hdf5storage", "h5py"],
            "executable_names": ["octave", "octave-cli"],
            "capabilities": [
                "m_file_preview",
                "function_signature_detection",
                "safety_scan",
                "plot_hint_detection",
                "project_script_ref_binding",
                "octave_execution",
                "timeout_policy",
                "stdout_stderr_capture",
                "isolated_workspace",
                "artifact_collection",
                "figure_artifact_collection",
                "figure_dataset",
                "png_svg_pdf_artifacts",
                "workspace_summary_placeholder",
                "report_embedding",
                "mat_file_import",
                "scipy_loadmat_v4_to_v72",
                "hdf5_mat_v73_optional",
                "workspace_variable_summary",
                "csv_export",
            ],
            "metadata": {
                "built_in": True,
                "preview_first": True,
                "safe_execution_requires_explicit_request": True,
            },
        }
    )


def builtin_plugin_manifests() -> tuple[PluginManifest, ...]:
    """Return built-in data-only plugin manifest records."""

    return (builtin_meshio_plugin_manifest(), builtin_mscript_preview_plugin_manifest())
