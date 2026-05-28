from __future__ import annotations

from osw.plugins.examples import builtin_mscript_preview_plugin_manifest
from osw.plugins.manifest import PluginDomain, PluginType


def test_builtin_mscript_preview_plugin_manifest_validates() -> None:
    manifest = builtin_mscript_preview_plugin_manifest()

    assert manifest.id == "osw.mscript_preview"
    assert manifest.name == "MATLAB/Octave Script Preview Importer"
    assert manifest.type is PluginType.SCRIPT_IMPORTER
    assert manifest.domain == PluginDomain.MATH.value
    assert manifest.input_formats == ("m", "mat")
    assert "script_preview" in manifest.output_formats
    assert "m_file_preview" in manifest.capabilities
    assert "safety_scan" in manifest.capabilities
    assert "plot_hint_detection" in manifest.capabilities
    assert manifest.executable_names == ("octave", "octave-cli")
    assert "octave_execution" in manifest.capabilities
    assert "isolated_workspace" in manifest.capabilities
    assert "figure_dataset" in manifest.capabilities
    assert "figure_dataset" in manifest.output_formats
    assert "workspace_summary" in manifest.output_formats
    assert "mat_file_import" in manifest.capabilities
    assert "workspace_variable_summary" in manifest.capabilities
    assert "csv_export" in manifest.capabilities
    assert "boundary_curve_export" in manifest.capabilities
    assert "mat_variable_to_boundary_curve" in manifest.capabilities
    assert "workspace_variable_to_boundary_curve" in manifest.capabilities
    assert "csv_to_boundary_curve" in manifest.capabilities
    assert "boundary_curve" in manifest.output_formats
    assert "curve_json" in manifest.output_formats
    assert "scipy" in manifest.optional_requires
    assert "png" in manifest.output_formats
    assert "svg" in manifest.output_formats
    assert "pdf" in manifest.output_formats
    assert not [
        diagnostic
        for diagnostic in manifest.validate()
        if diagnostic.severity.value == "error"
    ]
