"""Download and parse the ExPaNDS experimental techniques ontology.

This script extracts a mapping from class labels to ids (IRI) from the ontology.
It saves the result to a given file as a bz2 compressed JSON file.

The bz2 format was chosen as it yielded the smallest file among the
algorithms available in the standard library.
"""
# ruff: noqa: T201

import argparse
import bz2
import json
from pathlib import Path
from typing import Any, TypeAlias

import httpx

SOURCE_URL = "https://expands-eu.github.io/ExPaNDS-experimental-techniques-ontology/ontology.jsonld"

# Prefix used for all ExPaNDS class IRIs:
IRI_PREFIX = "http://purl.org/pan-science/PaNET/"
# @type of classes:
CLASS_TYPE = "http://www.w3.org/2002/07/owl#Class"
# Key for class labels:
LABEL_KEY = "http://www.w3.org/2000/01/rdf-schema#label"

Ontology: TypeAlias = list[dict[str, Any]]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("out", type=Path, help="Output file")
    parser.add_argument(
        "--load",
        type=Path,
        default=None,
        help="Load ontology from file instead of downloading",
    )
    parser.add_argument(
        "--persist", type=Path, default=None, help="Save full ontology to file"
    )
    return parser.parse_args()


def download() -> Ontology:
    print(f"Downloading ontology from {SOURCE_URL}")
    response = httpx.get(SOURCE_URL)
    response.raise_for_status()
    return response.json()  # type: ignore[no-any-return]


def load(path: Path | None) -> Ontology:
    if path is None:
        return download()
    else:
        print(f"Loading ontology from {path}")
        return json.loads(path.read_text())  # type: ignore[no-any-return]


def maybe_save_ontology(ontology: Ontology, target: Path | None) -> None:
    if target is not None:
        print(f"Saving ontology to {target}")
        target.write_text(json.dumps(ontology, indent=2))


def filter_techniques(ontology: Ontology) -> Ontology:
    return [
        item
        for item in ontology
        if item.get("@type") == [CLASS_TYPE]
        and item.get("@id", "").startswith(IRI_PREFIX)
    ]


def get_label(item: dict[str, Any]) -> str:
    [entry] = item[LABEL_KEY]
    return entry["@value"]  # type: ignore[no-any-return]


def parse_to_dict(ontology: Ontology) -> dict[str, str]:
    return {get_label(item).lower().strip(): item["@id"] for item in ontology}


def write_result(mapping: dict[str, str], out: Path) -> None:
    serialized = json.dumps(mapping).encode("utf-8")
    # replace all suffixes with `.json.bz2`
    path = out.parent.joinpath(out.name.split(".", 1)[0] + ".json.bz2")
    print(f"Writing parsed data to {path}")
    with bz2.open(path, "wb") as f:
        f.write(serialized)


def main() -> None:
    args = parse_args()
    ontology = load(args.load)
    maybe_save_ontology(ontology, args.persist)
    labels_to_ids = parse_to_dict(filter_techniques(ontology))
    write_result(labels_to_ids, args.out)


if __name__ == "__main__":
    main()
