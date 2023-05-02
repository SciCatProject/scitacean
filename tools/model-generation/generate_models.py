# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 SciCat Project (https://github.com/SciCatProject/scitacean)
"""Generate pydantic models from specifications."""
from pathlib import Path
from typing import Dict

from jinja2 import Environment, FileSystemLoader, Template
from spec import Spec
from templates import BANNER


def quote(s: str) -> str:
    if '"' in s:
        return f"'{s}'"
    return f'"{s}"'


def _template() -> Template:
    environment = Environment(  # noqa: S701
        loader=FileSystemLoader(Path(__file__).resolve().parent / "templates/"),
    )
    environment.filters["quote"] = quote
    return environment.get_template("model.py.jinja")


def generate_models(specs: Dict[str, Spec]) -> str:
    specs = dict(specs)
    dset_spec = specs.pop("Dataset")
    return _template().render(banner=BANNER, specs=specs, dset_spec=dset_spec)
