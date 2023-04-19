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


def _split_download_and_upload(spec: Spec) -> (Optional[Spec], Spec):
    download = Spec(
        name="Download" + spec.name,
        fields={key: field for key, field in spec.fields.items() if field.download},
    )
    upload = Spec(
        name="Upload" + spec.name,
        fields={key: field for key, field in spec.fields.items() if field.upload},
    )
    if not upload.fields:
        upload = None
    return _UpDownSpec(upload=upload, download=download)


def _collect_models(specs: Dict[str, Spec]) -> Dict[str, Spec]:
    res = {}
    for spec in specs.values():
        up_down = _split_download_and_upload(spec)
        res[up_down.download.name] = up_down.download
        if up_down.upload is not None:
            res[up_down.upload.name] = up_down.upload
    return res


def generate_models(specs: Dict[str, Spec]) -> str:
    # TODO special case dataset
    # TODO model names in fields (might need to be changed in spec package)
    # TODO validations
    model_specs = _collect_models(specs)
    return _template().render(banner=BANNER, models=model_specs)
