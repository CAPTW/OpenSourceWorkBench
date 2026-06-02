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
                "boundary_curve",
                "curve_json",
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
                "boundary_curve_export",
                "mat_variable_to_boundary_curve",
                "workspace_variable_to_boundary_curve",
                "csv_to_boundary_curve",
            ],
            "metadata": {
                "built_in": True,
                "preview_first": True,
                "safe_execution_requires_explicit_request": True,
            },
        }
    )


def builtin_gmsh_plugin_manifest() -> PluginManifest:
    """Return the data-only manifest for the Gmsh mesh generator bridge."""

    return PluginManifest.from_dict(
        {
            "id": "osw.gmsh",
            "name": "Gmsh Mesh Generator",
            "version": "0.1.0",
            "domain": "MESH",
            "type": "mesh_generator",
            "license": "GPL-compatible external tool",
            "description": (
                "Generates bounded primitive Gmsh .geo scripts and can run the "
                "local Gmsh executable through the OSW backend runner when "
                "explicitly requested."
            ),
            "input_formats": [
                "geo",
                "primitive_geometry",
                "step_placeholder",
            ],
            "output_formats": ["msh", "vtu"],
            "requires": [],
            "optional_requires": ["meshio"],
            "executable_names": ["gmsh"],
            "capabilities": [
                "primitive_geometry_meshing",
                "mesh_size_control",
                "physical_group_metadata",
                "meshio_conversion",
                "project_mesh_ref_binding",
            ],
            "metadata": {
                "built_in": True,
                "preview_first": True,
                "requires_explicit_execution_request": True,
                "no_native_commercial_cad_import": True,
            },
        }
    )


def builtin_calculix_plugin_manifest() -> PluginManifest:
    """Return the data-only manifest for CalculiX deck generation."""

    return PluginManifest.from_dict(
        {
            "id": "osw.calculix",
            "name": "CalculiX Linear Static Adapter",
            "version": "0.1.0",
            "domain": "CAE",
            "type": "solver_adapter",
            "license": "GPL-compatible external solver",
            "description": (
                "Prepares deterministic CalculiX linear static .inp decks from "
                "ProjectSchema and MeshModel data without running ccx."
            ),
            "input_formats": [
                "internal_project_schema",
                "mesh_model",
                "inp",
            ],
            "output_formats": [
                "inp",
                "dat",
                "frd",
                "vtk_placeholder",
            ],
            "requires": [],
            "optional_requires": [],
            "executable_names": ["ccx"],
            "capabilities": [
                "linear_static",
                "isotropic_elastic",
                "fixed_support",
                "nodal_force",
                "pressure_placeholder",
                "input_deck_generation",
            ],
            "metadata": {
                "built_in": True,
                "preview_first": True,
                "prepare_only": True,
                "no_solver_execution_during_deck_generation": True,
            },
        }
    )


def builtin_openfoam_plugin_manifest() -> PluginManifest:
    """Return the data-only manifest for OpenFOAM template binding."""

    return PluginManifest.from_dict(
        {
            "id": "osw.openfoam",
            "name": "OpenFOAM Template Adapter",
            "version": "0.1.0",
            "domain": "CFD",
            "type": "solver_adapter",
            "license": "GPL-compatible external solver",
            "description": (
                "Generates bounded cavity and duct OpenFOAM template cases, can "
                "run explicitly requested local solvers through the backend "
                "runner, and parses residual logs into reportable summaries."
            ),
            "input_formats": [
                "internal_project_schema",
                "openfoam_case",
            ],
            "output_formats": [
                "openfoam_case",
                "residual_summary",
                "vtk_placeholder",
            ],
            "requires": [],
            "optional_requires": [],
            "executable_names": ["blockMesh", "icoFoam", "simpleFoam"],
            "capabilities": [
                "cavity_template",
                "duct_template",
                "incompressible_placeholder",
                "residual_parser",
                "case_generation",
                "explicit_solver_run",
            ],
            "metadata": {
                "built_in": True,
                "preview_first": True,
                "template_based": True,
                "requires_explicit_execution_request": True,
                "no_full_openfoam_editor": True,
            },
        }
    )


def builtin_coolprop_plugin_manifest() -> PluginManifest:
    """Return the data-only manifest for CoolProp property calculations."""

    return PluginManifest.from_dict(
        {
            "id": "osw.coolprop",
            "name": "CoolProp Property Calculator",
            "version": "0.1.0",
            "domain": "CHM",
            "type": "property_model",
            "license": "MIT-compatible optional dependency",
            "description": (
                "Calculates bounded thermophysical property points and simple "
                "T/P sweeps through the optional CoolProp package when "
                "explicitly requested."
            ),
            "input_formats": ["internal_property_request"],
            "output_formats": ["property_table", "result_dataset", "csv"],
            "requires": [],
            "optional_requires": ["CoolProp"],
            "executable_names": [],
            "capabilities": [
                "thermophysical_properties",
                "property_sweep",
                "result_dataset_binding",
                "report_embedding",
            ],
            "metadata": {
                "built_in": True,
                "preview_first": True,
                "lazy_optional_dependency": True,
                "no_external_process": True,
                "not_process_flowsheet_simulator": True,
            },
        }
    )


def builtin_cantera_plugin_manifest() -> PluginManifest:
    """Return the data-only manifest for Cantera 0D reactor summaries."""

    return PluginManifest.from_dict(
        {
            "id": "osw.cantera",
            "name": "Cantera 0D Reactor Adapter",
            "version": "0.1.0",
            "domain": "CHM",
            "type": "solver_adapter",
            "license": "BSD-compatible optional dependency",
            "description": (
                "Runs bounded in-process Cantera 0D reactor calculations when "
                "explicitly requested and converts the time history to ResultDataset."
            ),
            "input_formats": ["internal_reactor_request", "cantera_mechanism"],
            "output_formats": ["reactor_time_history", "result_dataset", "csv"],
            "requires": [],
            "optional_requires": ["cantera"],
            "executable_names": [],
            "capabilities": [
                "zero_d_reactor",
                "species_time_history",
                "temperature_time_history",
                "result_dataset_binding",
                "report_embedding",
            ],
            "metadata": {
                "built_in": True,
                "preview_first": True,
                "lazy_optional_dependency": True,
                "no_external_process": True,
                "not_reacting_cfd": True,
            },
        }
    )


def builtin_plugin_manifests() -> tuple[PluginManifest, ...]:
    """Return built-in data-only plugin manifest records."""

    return (
        builtin_meshio_plugin_manifest(),
        builtin_mscript_preview_plugin_manifest(),
        builtin_gmsh_plugin_manifest(),
        builtin_calculix_plugin_manifest(),
        builtin_openfoam_plugin_manifest(),
        builtin_coolprop_plugin_manifest(),
        builtin_cantera_plugin_manifest(),
    )
