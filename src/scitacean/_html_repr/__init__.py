# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 SciCat Project (https://github.com/SciCatProject/scitacean)
"""HTML representations for Jupyter."""

import html
from datetime import datetime
from typing import Any, List

from ..dataset import Dataset
from ..filesystem import RemotePath
from ..model import DatasetLifecycle, Technique
from ..pid import PID
from . import resources


def dataset_html_repr(dset: Dataset) -> str:
    template = resources.dataset_repr_template()
    style_sheet = resources.dataset_style()
    rows = "\n".join(
        _format_field(dset, field)
        for field in sorted(Dataset.fields(), key=lambda f: not f.required(dset.type))
    )
    return template.substitute(style_sheet=style_sheet, rows=rows)


def _format_field(dset: Dataset, field: Dataset.Field) -> str:
    name = field.name
    required = (
        '<div style="color: var(--jp-error-color0)">*</div>'
        if field.required(dset.type)
        else ""
    )
    value = html.escape(str(getattr(dset, field.name)))
    typ = _format_type(field.type)
    description = html.escape(field.description)

    template = resources.dataset_field_repr_template()
    return template.substitute(
        name=name, required=required, type=typ, value=value, description=description
    )


_TYPE_NAME = {
    str: "str",
    int: "int",
    bool: "bool",
    datetime: "datetime",
    PID: "PID",
    DatasetLifecycle: "DatasetLifecycle",
    RemotePath: "RemotePath",
    List[str]: "list[str]",
    List[PID]: "list[PID]",
    List[Technique]: "list[Technique]",
    List[dict]: "list[dict]",  # type: ignore[type-arg]
    dict: "dict",
}


def _format_type(typ: Any) -> str:
    try:
        return _TYPE_NAME[typ]
    except KeyError:
        return html.escape(str(typ))
