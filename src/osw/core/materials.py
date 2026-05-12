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


@dataclass(frozen=True)
class Material:
    material_id: str
    name: str
    density: Quantity | None = None
    elastic: IsotropicElastic | None = None
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
            if material.material_id == material_id:
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
