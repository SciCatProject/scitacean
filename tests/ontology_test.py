from scitacean import ontology


def test_can_load_expands_technique_ontology() -> None:
    techniques = ontology.expands_techniques()
    assert len(techniques) > 0
    assert all(key.islower() for key in techniques.keys())
    assert all(key.strip() == key for key in techniques.keys())
    assert all(isinstance(value, str) for value in techniques.values())
