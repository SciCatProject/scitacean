# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 SciCat Project (https://github.com/SciCatProject/scitacean)
"""HTML representations for attachments for Jupyter."""

from __future__ import annotations

import dataclasses
from typing import List

from ..model import Attachment, UploadAttachment
from . import _resources
from ._common_html import Field, format_field_flag, format_type, format_value


def attachment_html_repr(attachment: Attachment) -> str:
    template = _resources.attachment_repr_template()
    style_sheet = _resources.attachment_style()
    rows = "\n".join(_format_field(field) for field in _get_fields(attachment))
    thumbnail = attachment.thumbnail._repr_mimebundle_(include=("text/html",))[
        "text/html"
    ]
    return template.substitute(
        style_sheet=style_sheet,
        caption=format_value(attachment.caption),
        rows=rows,
        thumbnail=thumbnail,
    )


def _format_field(field: Field) -> str:
    name = field.name
    flag = format_field_flag(field)
    typ = _format_type(field.type)
    value = format_value(field.value)

    template = _resources.attachment_field_repr_template()
    return template.substitute(
        name=name,
        flag=flag,
        type=typ,
        value=value,
    )


# Types are strings in Attachment because of
# from __future__ import annotations
def _format_type(typ: str) -> str:
    if typ.startswith("Optional["):
        typ = typ[9:-1]
    return format_type(typ)


_EXCLUDED_FIELDS = {
    "caption",
    "thumbnail",
}


def _get_fields(attachment: Attachment) -> List[Field]:
    fields = [
        Field(
            name=_strip_leading_underscore(field.name),
            value=getattr(attachment, field.name),
            type=field.type,
            description="",
            read_only=_is_read_only(field.name),
            required=False,
            error=None,
            main=True,
        )
        for field in dataclasses.fields(attachment)
        if field.name not in _EXCLUDED_FIELDS
    ]
    return sorted(fields, key=lambda field: field.name)


def _strip_leading_underscore(s: str) -> str:
    return s[1:] if s.startswith("_") else s


def _is_read_only(field_name: str) -> bool:
    return field_name not in UploadAttachment.__fields__
