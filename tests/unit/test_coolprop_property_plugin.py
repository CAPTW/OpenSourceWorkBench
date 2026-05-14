from __future__ import annotations

import json
from pathlib import Path

import pytest

from osw.plugins.base import PropertyModelPlugin
from osw.plugins.manifest import PluginType
from osw.solvers.coolprop.property_plugin import (
    CoolPropDependencyError,
    CoolPropPropertyPlugin,
    CoolPropStateInput,
)


class FakeCoolPropBackend:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, float, str, float, str]] = []

    def props_si(
        self,
        output: str,
        input1_name: str,
        input1_value: float,
        input2_name: str,
        input2_value: float,
        fluid: str,
    ) -> float:
        self.calls.append((output, input1_name, input1_value, input2_name, input2_value, fluid))
        if output == "D":
            return 997.0 - 0.1 * (input2_value - 300.0)
        if output == "H":
            return 112650.0
        raise ValueError(f"unsupported fake output: {output}")


def test_coolprop_plugin_manifest_is_property_model() -> None:
    plugin = CoolPropPropertyPlugin(backend=FakeCoolPropBackend())
    manifest = plugin.manifest

    assert isinstance(plugin, PropertyModelPlugin)
    assert manifest.id == "osw.solvers.coolprop.property"
    assert manifest.type is PluginType.PROPERTY_MODEL
    assert manifest.optional_requires == ("CoolProp",)
    assert "property_calculation" in manifest.capabilities
    assert "sweep_table" in manifest.capabilities
    assert "csv_export" in manifest.capabilities


def test_coolprop_manifest_metadata_declares_safety_contract() -> None:
    plugin = CoolPropPropertyPlugin(backend=FakeCoolPropBackend())
    metadata = plugin.metadata()
    manifest_path = (
        Path(__file__).parents[2] / "src" / "osw" / "solvers" / "coolprop" / "osw-plugin.json"
    )
    manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))

    for surface in (metadata, manifest_data):
        assert surface["entry_point"] == (
            "osw.solvers.coolprop.property_plugin:CoolPropPropertyPlugin"
        )
        assert surface["adapter_class"] == "CoolPropPropertyPlugin"
        assert surface["preview_required"] is True
        assert surface["mutates_project"] is False
        assert surface["executes_external_process"] is False
        assert "CoolProp is optional" in surface["dependency_behavior"]
        assert any("not a process flowsheet simulator" in item for item in surface["limitations"])


def test_coolprop_example_documents_bounded_si_workflow() -> None:
    readme = Path(__file__).parents[2] / "examples" / "07_coolprop_property" / "README.md"
    text = readme.read_text(encoding="utf-8")

    assert "pressure_pa" in text
    assert "temperature_k" in text
    assert "SI units" in text
    assert "CoolProp is optional" in text
    assert "not a process flowsheet simulator" in text


def test_coolprop_missing_dependency_diagnostic_is_friendly() -> None:
    plugin = CoolPropPropertyPlugin(dependency_checker=lambda: False)
    report = plugin.dependency_report()

    assert report.has_errors
    assert "CoolProp is not installed" in report.summary()
    with pytest.raises(CoolPropDependencyError, match="CoolProp is not installed"):
        plugin.calculate_state(
            CoolPropStateInput(fluid="Water", pressure_pa=101325.0, temperature_k=300.0)
        )


def test_coolprop_property_calculation_uses_explicit_si_inputs() -> None:
    backend = FakeCoolPropBackend()
    plugin = CoolPropPropertyPlugin(backend=backend)
    state = CoolPropStateInput(
        fluid="Water",
        pressure_pa=101325.0,
        temperature_k=300.0,
        outputs=("D", "H"),
    )

    result = plugin.calculate_state(state)

    assert result.fluid == "Water"
    assert result.pressure_pa == 101325.0
    assert result.temperature_k == 300.0
    assert result.properties["D"].value == 997.0
    assert result.properties["D"].unit == "kg/m^3"
    assert backend.calls[0] == ("D", "P", 101325.0, "T", 300.0, "Water")
    assert result.to_table_preview().columns == (
        "fluid",
        "pressure_pa",
        "temperature_k",
        "property",
        "value",
        "unit",
    )


def test_coolprop_evaluate_returns_reportable_mapping() -> None:
    plugin = CoolPropPropertyPlugin(backend=FakeCoolPropBackend())

    payload = plugin.evaluate(
        {
            "fluid": "Water",
            "pressure_pa": 101325.0,
            "temperature_k": 300.0,
            "outputs": ["D"],
        }
    )

    assert payload["source"] == "CoolProp"
    assert payload["properties"]["D"]["unit"] == "kg/m^3"
    assert payload["plot_dataset_placeholder"]["kind"] == "property_point"
    assert "not a process flowsheet simulator" in " ".join(payload["limitations"])


def test_coolprop_sweep_table_exports_csv(tmp_path: Path) -> None:
    plugin = CoolPropPropertyPlugin(backend=FakeCoolPropBackend())

    table = plugin.sweep_table(
        fluid="Water",
        pressure_pa=101325.0,
        temperatures_k=(300.0, 310.0),
        outputs=("D",),
    )

    assert table.columns == ("fluid", "pressure_pa", "temperature_k", "D [kg/m^3]")
    assert table.rows == (
        ("Water", "101325", "300", "997"),
        ("Water", "101325", "310", "996"),
    )
    csv_path = table.export_csv(tmp_path / "coolprop_sweep.csv")
    assert csv_path.read_text(encoding="utf-8") == (
        "fluid,pressure_pa,temperature_k,D [kg/m^3]\n"
        "Water,101325,300,997\n"
        "Water,101325,310,996\n"
    )


def test_coolprop_real_water_density_optional() -> None:
    pytest.importorskip("CoolProp.CoolProp")
    plugin = CoolPropPropertyPlugin()

    result = plugin.calculate_state(
        CoolPropStateInput(
            fluid="Water",
            pressure_pa=101325.0,
            temperature_k=300.0,
            outputs=("D",),
        )
    )

    assert 990.0 < result.properties["D"].value < 1000.0
