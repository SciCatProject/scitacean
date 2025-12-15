# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 SciCat Project (https://github.com/SciCatProject/scitacean)
"""Tools for working with ontologies."""

import bz2
import importlib.resources
import json
import re
from functools import cache

from ..model import Technique


def _load_ontology(name: str) -> object:
    """Load an ontology from the package resources.

    Note that the ontology file was generated using a script in
    ``tools/ontologies`` in the Scitacean repository.
    """
    with (
        importlib.resources.files("scitacean.ontology")
        .joinpath(f"{name}.json.bz2")
        .open("rb") as raw_f
    ):
        with bz2.open(raw_f, "rb") as f:
            return json.loads(f.read())


@cache
def expands_techniques() -> dict[str, list[str]]:
    """Load the ExPaNDS experimental techniques ontology.

    Returns
    -------
    :
        A dict mapping from technique ids (IRIs) to labels.
        The first element of the list is the primary label.
        All labels are lowercase and contain no leading or trailing whitespace.
    """
    return _load_ontology("expands_techniques")  # type: ignore[return-value]


def find_technique(label_or_iri: str) -> Technique:
    """Construct a Technique model from an ontology label or IRI.

    The argument specifies a technique from the
    `ExPaNDS experimental techniques ontology <https://expands-eu.github.io/ExPaNDS-experimental-techniques-ontology/index-en.html>`_.

    Parameters
    ----------
    label_or_iri:
        One of:

        - Technique *label* from the ExPaNDS ontology. The input is first converted to
          lowercase and leading and trailing whitespace is removed.
        - Technique *IRI* from the ExPaNDS ontology. Must exactly match an IRI in
          the ontology.

    Returns
    -------
    :
        The loaded technique encoded as:

        .. code-block:: python

            Technique(name=label, pid=iri)

    Raises
    ------
    ValueError
        If the label or IRI is not found in the ontology.
    """
    if _is_iri(label_or_iri):
        return _lookup_iri(label_or_iri)
    return _lookup_label(label_or_iri)


def _lookup_label(label: str) -> Technique:
    label = label.strip().lower()
    for iri, labels in expands_techniques().items():
        if label in labels:
            return Technique(pid=iri, name=labels[0])
    raise ValueError(
        f"Unknown technique label: '{label}'\n"
        "See the ExPaNDS experimental technique ontology for allowed labels at "
        "https://expands-eu.github.io/ExPaNDS-experimental-techniques-ontology/index-en.html"
    )


def _lookup_iri(iri: str) -> Technique:
    try:
        label = expands_techniques()[iri][0]
    except KeyError:
        raise ValueError(
            f"Unknown technique IRI: '{iri}'\n"
            "See the ExPaNDS experimental technique ontology for allowed labels at "
            "https://expands-eu.github.io/ExPaNDS-experimental-techniques-ontology/index-en.html"
        ) from None
    return Technique(pid=iri, name=label)


_IRI_REGEX = re.compile(r"^https?://purl\.org/pan-science/PaNET/PaNET\d+$")


def _is_iri(iri: str) -> bool:
    return bool(_IRI_REGEX.match(iri))


__all__ = ["expands_techniques", "find_technique"]
