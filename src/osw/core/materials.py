"""Material contracts for OSW projects."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .units import Quantity
from .validation import ValidationReport


@dataclass(frozen=True)
class IsotropicElastic:
    young_modulus: Quantity
    poisson_ratio: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": "isotropic_elastic",
            "young_modulus": self.young_modulus.to_dict(),
            "poisson_ratio": self.poisson_ratio,
        }

    @classmethod
    def from_dict(cls, data: object) -> IsotropicElastic:
        if not isinstance(data, dict):
            msg = "Elastic material data must be a mapping."
            raise ValueError(msg)
        return cls(
            young_modulus=Quantity.from_dict(data.get("young_modulus")),
            poisson_ratio=float(data.get("poisson_ratio", 0.0)),
        )

    def validate(self, *, path: str) -> ValidationReport:
        report = ValidationReport()
        if self.young_modulus.value <= 0:
            report.add_error(f"{path}.young_modulus", "Young modulus must be positive.")
        if not (-1.0 < self.poisson_ratio < 0.5):
            report.add_error(
                f"{path}.poisson_ratio",
                "Poisson ratio must be greater than -1.0 and less than 0.5.",
            )
        return report


IsotropicElasticProperties = IsotropicElastic


@dataclass(frozen=True)
class ThermalProperties:
    conductivity: Quantity | None = None
    specific_heat: Quantity | None = None

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {}
        if self.conductivity is not None:
            data["conductivity"] = self.conductivity.to_dict()
        if self.specific_heat is not None:
            data["specific_heat"] = self.specific_heat.to_dict()
        return data

    @classmethod
    def from_dict(cls, data: object) -> ThermalProperties:
        if data is None:
            return cls()
        if not isinstance(data, dict):
            msg = "Thermal material data must be a mapping."
            raise ValueError(msg)
        return cls(
            conductivity=(
                Quantity.from_dict(data["conductivity"]) if data.get("conductivity") else None
            ),
            specific_heat=(
                Quantity.from_dict(data["specific_heat"]) if data.get("specific_heat") else None
            ),
        )


@dataclass(frozen=True)
class FluidProperties:
    dynamic_viscosity: Quantity | None = None

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {}
        if self.dynamic_viscosity is not None:
            data["dynamic_viscosity"] = self.dynamic_viscosity.to_dict()
        return data

    @classmethod
    def from_dict(cls, data: object) -> FluidProperties:
        if data is None:
            return cls()
        if not isinstance(data, dict):
            msg = "Fluid material data must be a mapping."
            raise ValueError(msg)
        return cls(
            dynamic_viscosity=(
                Quantity.from_dict(data["dynamic_viscosity"])
                if data.get("dynamic_viscosity")
                else None
            )
        )


@dataclass(frozen=True)
class Material:
    material_id: str
    name: str
    density: Quantity | None = None
    elastic: IsotropicElastic | None = None
    thermal: ThermalProperties | None = None
    fluid: FluidProperties | None = None
    library: str = "project"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "material_id": self.material_id,
            "name": self.name,
            "metadata": dict(self.metadata),
        }
        if self.density is not None:
            data["density"] = self.density.to_dict()
        if self.elastic is not None:
            data["elastic"] = self.elastic.to_dict()
        if self.thermal is not None:
            data["thermal"] = self.thermal.to_dict()
        if self.fluid is not None:
            data["fluid"] = self.fluid.to_dict()
        if self.library:
            data["library"] = self.library
        return data

    @classmethod
    def from_dict(cls, data: object) -> Material:
        if not isinstance(data, dict):
            msg = "Material entry must be a mapping."
            raise ValueError(msg)
        return cls(
            material_id=str(data.get("material_id", "")),
            name=str(data.get("name", "")),
            density=Quantity.from_dict(data["density"]) if data.get("density") else None,
            elastic=IsotropicElastic.from_dict(data["elastic"]) if data.get("elastic") else None,
            thermal=ThermalProperties.from_dict(data["thermal"]) if data.get("thermal") else None,
            fluid=FluidProperties.from_dict(data["fluid"]) if data.get("fluid") else None,
            library=str(data.get("library", "project")),
            metadata=dict(data.get("metadata", {})),
        )

    def validate(self, *, path: str = "materials[]") -> ValidationReport:
        report = ValidationReport()
        if not self.material_id:
            report.add_error(f"{path}.material_id", "Material id is required.")
        if not self.name:
            report.add_error(f"{path}.name", "Material name is required.")
        if self.density is not None and self.density.value <= 0:
            report.add_error(f"{path}.density", "Material density must be positive.")
        if self.elastic is not None:
            report.extend(self.elastic.validate(path=f"{path}.elastic"))
        return report


@dataclass(frozen=True)
class MaterialDB:
    materials: list[Material] = field(default_factory=list)
    name: str = "builtin"

    def to_list(self) -> list[dict[str, Any]]:
        return [material.to_dict() for material in self.materials]

    @classmethod
    def from_list(cls, data: object) -> MaterialDB:
        if data is None:
            return cls()
        if not isinstance(data, list):
            msg = "Material database must be a list."
            raise ValueError(msg)
        return cls([Material.from_dict(item) for item in data])

    def get(self, material_id: str) -> Material | None:
        for material in self.materials:
            if material.material_id == material_id or material.name == material_id:
                return material
        return None

    def validate(self, *, path: str = "materials") -> ValidationReport:
        report = ValidationReport()
        seen: set[str] = set()
        for index, material in enumerate(self.materials):
            item_path = f"{path}[{index}]"
            report.extend(material.validate(path=item_path))
            if material.material_id:
                if material.material_id in seen:
                    report.add_error(item_path, f"Duplicate material id: {material.material_id}")
                seen.add(material.material_id)
        return report


MaterialLibrary = MaterialDB


def builtin_materials() -> MaterialLibrary:
    """Return the small built-in material library used by the GUI demo."""

    return MaterialLibrary(
        [
            Material(
                material_id="aluminum-6061",
                name="Aluminum 6061",
                density=Quantity(2700.0, "kg/m^3"),
                elastic=IsotropicElastic(
                    young_modulus=Quantity(68.9e9, "Pa"),
                    poisson_ratio=0.33,
                ),
                thermal=ThermalProperties(
                    conductivity=Quantity(167.0, "W/m/K"),
                    specific_heat=Quantity(896.0, "J/kg/K"),
                ),
                library="builtin",
            ),
            Material(
                material_id="steel-aisi-304",
                name="Steel AISI 304",
                density=Quantity(8000.0, "kg/m^3"),
                elastic=IsotropicElastic(
                    young_modulus=Quantity(193.0e9, "Pa"),
                    poisson_ratio=0.29,
                ),
                library="builtin",
            ),
            Material(
                material_id="copper",
                name="Copper",
                density=Quantity(8960.0, "kg/m^3"),
                thermal=ThermalProperties(conductivity=Quantity(401.0, "W/m/K")),
                library="builtin",
            ),
            Material(
                material_id="air",
                name="Air",
                density=Quantity(1.225, "kg/m^3"),
                fluid=FluidProperties(dynamic_viscosity=Quantity(1.81e-5, "Pa*s")),
                library="builtin",
            ),
            Material(
                material_id="water",
                name="Water",
                density=Quantity(997.0, "kg/m^3"),
                fluid=FluidProperties(dynamic_viscosity=Quantity(8.9e-4, "Pa*s")),
                library="builtin",
            ),
        ],
        name="builtin",
    )
