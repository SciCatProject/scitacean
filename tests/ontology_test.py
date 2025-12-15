# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 SciCat Project (https://github.com/SciCatProject/scitacean)
import pytest

from scitacean import model, ontology


def test_can_load_expands_technique_ontology() -> None:
    techniques = ontology.expands_techniques()
    assert len(techniques) > 0

    # Check IRI
    assert all(iri.startswith("http") for iri in techniques.keys())

    # Check labels
    assert all(
        all(label.islower() for label in labels) for labels in techniques.values()
    )
    assert all(
        all(label.strip() == label for label in labels)
        for labels in techniques.values()
    )


def test_can_look_up_technique_by_label() -> None:
    technique = ontology.find_technique("small angle neutron scattering")
    expected = model.Technique(
        pid="http://purl.org/pan-science/PaNET/PaNET01189",
        name="small angle neutron scattering",
    )
    assert technique == expected


def test_can_look_up_technique_by_label_is_case_insensitive() -> None:
    technique = ontology.find_technique("Total Scattering")
    expected = model.Technique(
        pid="http://purl.org/pan-science/PaNET/PaNET01190",
        name="total scattering",
    )
    assert technique == expected


def test_can_look_up_technique_by_alternative_label() -> None:
    regular = ontology.find_technique("x-ray single crystal diffraction")
    alternative1 = ontology.find_technique("SXRD")
    alternative2 = ontology.find_technique("sxrd")
    alternative3 = ontology.find_technique("single crystal x-ray diffraction ")
    expected = model.Technique(
        pid="http://purl.org/pan-science/PaNET/PaNET01102",
        name="x-ray single crystal diffraction",
    )
    assert regular == expected
    assert alternative1 == expected
    assert alternative2 == expected
    assert alternative3 == expected


def test_can_look_up_technique_by_iri() -> None:
    technique = ontology.find_technique("http://purl.org/pan-science/PaNET/PaNET01239")
    expected = model.Technique(
        pid="http://purl.org/pan-science/PaNET/PaNET01239",
        name="neutron reflectometry",
    )
    assert technique == expected


def test_lookup_rejects_ambiguous_label() -> None:
    with pytest.raises(ValueError, match="multiple techniques"):
        ontology.find_technique("diffraction")
