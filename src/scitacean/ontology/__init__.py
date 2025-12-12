"""Tools for working with ontologies."""

import bz2
import importlib.resources
import json
from functools import cache

from ..model import Technique


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
        All labels are lowercase and contain no leading or trailing whitespace.
    """
    return _load_ontology("expands_techniques")  # type: ignore[return-value]


def find_technique(label: str) -> Technique:
    """Find the IRI for a given technique label and construct a Technique model.

    Parameters
    ----------
    label:
        Technique label from the
        `ExPaNDS experimental techniques ontology <https://expands-eu.github.io/ExPaNDS-experimental-techniques-ontology/index-en.html>`_.
        The label is first converted to lowercase and leading and trailing whitespace
        is removed.

    Returns
    -------
    :
        The loaded technique.

    Raises
    ------
    ValueError
        If the label is not found in the ontology.
    """
    try:
        iri = expands_techniques()[label.lower().strip()]
    except KeyError:
        raise ValueError(
            f"Unknown technique label: '{label}'\n"
            "See the ExPaNDS experimental technique ontology for allowed labels at "
            "https://expands-eu.github.io/ExPaNDS-experimental-techniques-ontology/index-en.html"
        ) from None
    return Technique(pid=iri, name=label)


__all__ = ["expands_techniques", "find_technique"]
