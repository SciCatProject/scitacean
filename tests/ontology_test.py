from scitacean import ontology


def test_can_load_expands_technique_ontology() -> None:
    techniques = ontology.expands_techniques()
    assert len(techniques) > 0
    assert all(isinstance(key, str) for key in techniques.keys())
    assert all(isinstance(value, str) for value in techniques.values())
