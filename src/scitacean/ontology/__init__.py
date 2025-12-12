"""Tools for working with ontologies."""

import bz2
import importlib.resources
import json
from functools import cache


def _load_ontology(name: str) -> object:
    with (
        importlib.resources.files("scitacean.ontology")
        .joinpath(f"{name}.json.bz2")
        .open("rb") as raw_f
    ):
        with bz2.open(raw_f, "rb") as f:
            return json.loads(f.read())


@cache
def expands_techniques() -> dict[str, str]:
    """Load the ExPaNDS experimental techniques ontology.

    Returns
    -------
    :
        A dict mapping from technique labels to ids (IRIs).
    """
    return _load_ontology("expands_techniques")  # type: ignore[return-value]
