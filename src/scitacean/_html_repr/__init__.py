# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 SciCat Project (https://github.com/SciCatProject/scitacean)
"""HTML representations for Jupyter."""

import html
from datetime import datetime
from typing import Any, List

from ..dataset import Dataset
from ..model import DatasetLifecycle
from ..pid import PID


def dataset_html_repr(dset: Dataset) -> str:

    rows = "\n".join(
        _format_field(dset, field)
        for field in sorted(Dataset.fields(), key=lambda f: not f.required(dset.type))
    )
    return f"""<table>
        <tr>
            <th>Name</th><th></th><th>Type</th><th>Value</th><th>Description</th>
        </tr>
        {rows}
    </table>"""


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
    return (
        "<tr><td>"
        + "</td><td>".join((name, required, typ, value, description))
        + "</tr></td>"
    )


def _format_type(typ: Any) -> str:
    try:
        return {
            str: "str",
            int: "int",
            bool: "bool",
            datetime: "datetime",
            PID: "PID",
            DatasetLifecycle: "DatasetLifecycle",
            List[str]: "list[str]",
            List[dict]: "list[dict]",  # type: ignore[type-arg]
        }[typ]
    except KeyError:
        return html.escape(str(typ))
