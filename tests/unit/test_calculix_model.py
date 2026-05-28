from __future__ import annotations

from pathlib import Path

from osw.solvers.calculix.model import (
    CalculiXBoundary,
    CalculiXDeckResult,
    CalculiXElement,
    CalculiXElementSet,
    CalculiXInputDeck,
    CalculiXLoad,
    CalculiXMaterial,
    CalculiXNode,
    CalculiXNodeSet,
    CalculiXStep,
    CalculiXSurfaceSet,
)


def test_calculix_material_serializes_round_trips() -> None:
    material = CalculiXMaterial(
        name="steel",
        elastic_modulus=210_000_000_000.0,
        poisson_ratio=0.3,
        density=7850.0,
        source_material_id="steel",
    )

    assert CalculiXMaterial.from_dict(material.to_dict()) == material


def test_calculix_sets_boundaries_and_loads_round_trip() -> None:
    node_set = CalculiXNodeSet("FIXED", (1, 2), role="support")
    element_set = CalculiXElementSet("EALL", (1,), role="domain")
    surface = CalculiXSurfaceSet("TOP", ((1, "S2"),), role="load")
    boundary = CalculiXBoundary("fixed", "FIXED", 1, 3, 0.0)
    load = CalculiXLoad("tip", "force", "TIP", components=(0.0, -100.0, 0.0))

    assert CalculiXNodeSet.from_dict(node_set.to_dict()) == node_set
    assert CalculiXElementSet.from_dict(element_set.to_dict()) == element_set
    assert CalculiXSurfaceSet.from_dict(surface.to_dict()) == surface
    assert CalculiXBoundary.from_dict(boundary.to_dict()) == boundary
    assert CalculiXLoad.from_dict(load.to_dict()) == load


def test_calculix_input_deck_serializes_to_plain_dict() -> None:
    deck = CalculiXInputDeck(
        heading="OSW CalculiX linear static deck: cantilever",
        nodes=(CalculiXNode(1, (0.0, 0.0, 0.0)),),
        elements=(CalculiXElement(1, "C3D8", (1, 2, 3, 4, 5, 6, 7, 8)),),
        materials=(CalculiXMaterial("steel", 210_000_000_000.0, 0.3),),
        node_sets=(CalculiXNodeSet("FIXED", (1,)),),
        element_sets=(CalculiXElementSet("EALL", (1,)),),
        boundaries=(CalculiXBoundary("fixed", "FIXED"),),
        loads=(CalculiXLoad("tip", "force", "TIP", components=(0.0, -100.0, 0.0)),),
        steps=(CalculiXStep("linear_static"),),
    )

    payload = deck.to_dict()
    restored = CalculiXInputDeck.from_dict(payload)

    assert payload["nodes"][0]["coordinates"] == [0.0, 0.0, 0.0]
    assert restored.heading == deck.heading
    assert restored.elements[0].node_ids == (1, 2, 3, 4, 5, 6, 7, 8)


def test_deck_result_paths_serialize_as_strings() -> None:
    result = CalculiXDeckResult(status="ok", output_path=Path("case.inp"))

    assert result.to_dict()["output_path"] == "case.inp"
    assert result.ok
