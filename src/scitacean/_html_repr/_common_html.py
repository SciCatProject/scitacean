# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 SciCat Project (https://github.com/SciCatProject/scitacean)
"""Common functions for HTML reprs."""

import html
from datetime import datetime
from typing import Any, List, Optional

from .._internal.dataclass_wrapper import dataclass_optional_args
from ..filesystem import RemotePath
from ..model import History, Lifecycle, Relationship, Technique
from ..pid import PID
from . import _resources


@dataclass_optional_args(kw_only=True, frozen=True, slots=True)
class Field:
    name: str
    value: Any
    type: type
    description: str
    read_only: bool
    required: bool
    error: Optional[str]
    main: bool


_TYPE_NAME = {
    str: "str",
    int: "int",
    bool: "bool",
    dict: "dict",
    datetime: "datetime",
    History: "History",
    Lifecycle: "Lifecycle",
    PID: "PID",
    RemotePath: "RemotePath",
    List[str]: "list[str]",
    List[PID]: "list[PID]",
    List[Relationship]: "list[Relationship]",
    List[Technique]: "list[Technique]",
    List[dict]: "list[dict]",  # type: ignore[type-arg]
}


def format_value(val: Any) -> str:
    """Return a str repr for a field value."""
    if val is None:
        return '<span class="cean-empty-field">None</span>'
    if isinstance(val, datetime):
        return val.strftime("%Y-%m-%d %H:%M:%S%z")
    return html.escape(str(val))


def format_type(typ: Any) -> str:
    """Return a concise str repr for a type."""
    # Types are strings model.py because of
    # from __future__ import annotations
    if isinstance(typ, str) and typ.startswith("Optional["):
        typ = typ[9:-1]
    try:
        return _TYPE_NAME[typ]
    except KeyError:
        return html.escape(str(typ))


def format_field_flag(field: Field) -> str:
    """Return HTML markup for field flags."""
    flags = ""
    if field.read_only:
        flags += f'<div class="cean-lock">{_resources.image("lock.svg")}</div>'
    if field.required:
        flags += '<div style="color: var(--jp-error-color0)">*</div>'
    return flags
