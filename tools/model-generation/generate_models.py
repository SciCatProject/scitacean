# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 SciCat Project (https://github.com/SciCatProject/scitacean)
"""Generate pydantic models from specifications."""
import dataclasses
from pathlib import Path
from typing import Dict, Optional

from jinja2 import Environment, FileSystemLoader, Template
from spec import Spec
from templates import BANNER


@dataclasses.dataclass
class _UpDownSpec:
    upload: Optional[Spec]
    download: Spec


def quote(x):
    return f'"{x}"'


def _template() -> Template:
    environment = Environment(  # noqa: S701
        loader=FileSystemLoader(Path(__file__).resolve().parent / "templates/"),
    )
    environment.filters["quote"] = quote
    return environment.get_template("model.py.jinja")


def generate_models(specs: Dict[str, Spec]) -> str:
    # TODO special case dataset
    # TODO model names in fields (might need to be changed in spec package)
    # TODO pid fields
    return _template().render(banner=BANNER, specs=specs)
