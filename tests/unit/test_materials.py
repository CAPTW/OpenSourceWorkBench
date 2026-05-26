"""Material database tests for OSW core contracts."""

from __future__ import annotations

from osw.core.materials import IsotropicElastic, Material, MaterialDB, builtin_materials
from osw.core.units import Quantity


def test_material_supports_isotropic_elastic_fields() -> None:
    steel = Material(
        material_id="steel-a36",
        name="A36 steel",
        density=Quantity(7850.0, "kg/m^3"),
        elastic=IsotropicElastic(
            young_modulus=Quantity(200.0, "GPa"),
            poisson_ratio=0.29,
        ),
    )

    assert steel.elastic is not None
    assert steel.elastic.young_modulus.unit == "GPa"
    assert steel.elastic.poisson_ratio == 0.29
    assert not steel.validate().has_errors


def test_material_db_round_trips_materials_by_id() -> None:
    material = Material(
        material_id="aluminum-6061",
        name="Aluminum 6061",
        elastic=IsotropicElastic(young_modulus=Quantity(69.0, "GPa"), poisson_ratio=0.33),
    )

    material_db = MaterialDB([material])

    loaded = MaterialDB.from_list(material_db.to_list())

    assert loaded.get("aluminum-6061") == material


def test_builtin_material_library_contains_aluminum_6061() -> None:
    library = builtin_materials()
    material = library.get("aluminum-6061")

    assert material is not None
    assert material.name == "Aluminum 6061"
    assert library.get("Aluminum 6061") == material


def test_material_validation_rejects_invalid_poisson_ratio() -> None:
    material = Material(
        material_id="bad",
        name="Bad material",
        elastic=IsotropicElastic(young_modulus=Quantity(1.0, "Pa"), poisson_ratio=0.75),
    )

    report = material.validate()

    assert report.has_errors
    assert "Poisson ratio" in report.messages[0].message


def test_material_validation_rejects_invalid_density() -> None:
    material = Material(
        material_id="bad-density",
        name="Bad density",
        density=Quantity(-1.0, "kg/m^3"),
    )

    report = material.validate()

    assert report.has_errors
    assert any("density must be positive" in item.message for item in report.messages)
