# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 SciCat Project (https://github.com/SciCatProject/scitacean)
"""HTML representations for Jupyter."""

import html
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

import pydantic

from ..dataset import Dataset
from ..filesystem import RemotePath
from ..model import DatasetLifecycle, DatasetType, Technique
from ..pid import PID
from . import resources


def dataset_html_repr(dset: Dataset) -> str:
    template = resources.dataset_repr_template()
    style_sheet = resources.dataset_style()
    fields = _get_fields(dset)
    main_rows = "\n".join(_format_field(field) for field in fields if field.main)
    detail_rows = "\n".join(_format_field(field) for field in fields if not field.main)
    return template.substitute(
        style_sheet=style_sheet,
        dataset_type=_format_dataset_type(dset.type),
        file_info=_format_file_info(dset, archived=False),
        archived_file_info=_format_file_info(dset, archived=True),
        main_rows=main_rows,
        detail_rows=detail_rows,
        file_rows=_format_files(dset),
        metadata_rows=_format_metadata(dset),
    )


def _format_files(dset: Dataset) -> str:
    template = resources.files_repr_template()
    return "\n".join(
        template.substitute(
            local_path=(
                '<span class="cean-empty-field">None</span>'
                if not file.is_on_local
                else html.escape(str(file.local_path))
            ),
            remote_path=(
                '<span class="cean-empty-field">None</span>'
                if not file.is_on_remote
                else html.escape(str(file.remote_path))
            ),
            size=_human_readable_size(file.size),
        )
        for file in dset.files
    )


def _format_metadata(dset: Dataset) -> str:
    template = resources.metadata_template()
    return "\n".join(
        template.substitute(
            name=html.escape(str(name)),
            value=_format_metadata_value(value),
        )
        for name, value in dset.meta.items()
    )


def _format_metadata_value(value: Any) -> str:
    if _has_value_unit_encoding(value):
        if (unit := value.get("unit")) is not None:
            return f"{html.escape(str(value['value']))} [{html.escape(str(unit))}]"
        else:
            return html.escape(str(value["value"]))

    return html.escape(str(value))


# ESS uses these keys for all scientific metadata.
# If the metadata uses only these keys, format it more nicely.
# Otherwise, fall back to showing the item's str.
_VALUE_UNIT_KEYS = {"value", "unit", "valueSI", "unitSI"}


def _has_value_unit_encoding(meta_value: Any):
    if (
        isinstance(meta_value, dict)
        and "value" in meta_value
        and not (meta_value.keys() - _VALUE_UNIT_KEYS)
    ):
        return True
    return False


@dataclass
class Field:
    name: str
    value: Any
    type: type
    description: str
    read_only: bool
    required: bool
    error: Optional[str]
    main: bool


def _format_field(field: Field) -> str:
    def format_value(val) -> str:
        if isinstance(val, datetime):
            return val.strftime("%Y-%m-%d %H:%M:%S%z")
        return html.escape(str(val))

    name = field.name
    flag = _format_field_flag(field)
    value = (
        '<span class="cean-empty-field">None</span>'
        if field.value is None
        else format_value(field.value)
    )
    typ = _format_type(field.type)
    description = html.escape(field.description)
    row_highlight = _row_highlight_classes(field)

    template = resources.dataset_field_repr_template()
    return template.substitute(
        name=name,
        flag=flag,
        type=typ,
        value=value,
        description=description,
        extra_classes=row_highlight,
    )


_EXCLUDED_FIELDS = {
    "type",
    "number_of_files",
    "number_of_files_archived",
    "size",
    "packed_size",
    "meta",
}

_MAIN_FIELDS = {
    "pid",
    "source_folder",
    "name",
    "description",
    "creation_time",
    "proposal_id",
    "sample_id",
    "input_datasets",
}


def _get_fields(dset: Dataset) -> List[Field]:
    validation = _validate(dset)
    fields = [
        Field(
            name=field.name,
            value=getattr(dset, field.name, None),
            type=field.type,
            description=field.description,
            read_only=field.read_only,
            required=field.required(dset.type),
            error=_check_error(field, validation),
            main=field.name in _MAIN_FIELDS,
        )
        for field in dset.fields()
        if field.name not in _EXCLUDED_FIELDS
        and (field.used_by(dset.type) or getattr(dset, field.name, None) is not None)
    ]
    return sorted(
        sorted(fields, key=lambda field: field.name),
        key=lambda field: not field.required,
    )


def _check_error(field: Field, validation: Dict[str, str]) -> Optional[str]:
    if field.name in validation:
        # TODO validation uses model names (camelCase)
        return validation[field.name]
    return None


def _validate(dset: Dataset) -> Dict[str, str]:
    def single_elem(xs):
        (x,) = xs
        return x

    try:
        dset.validate()
        return {}
    except pydantic.ValidationError as e:
        return {single_elem(error["loc"]): error["msg"] for error in e.errors()}


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


def _format_field_flag(field: Field) -> str:
    flags = ""
    if field.read_only:
        flags += f'<div class="cean-lock">{resources.image("lock.svg")}</div>'
    if field.required:
        flags += '<div style="color: var(--jp-error-color0)">*</div>'
    return flags


def _format_dataset_type(dataset_type: DatasetType) -> str:
    return "Raw" if dataset_type == DatasetType.RAW else "Derived"


def _format_file_info(dset: Dataset, archived: bool) -> str:
    if archived:
        n_files = dset.number_of_files_archived
        if n_files == 0:
            # Don't show archived files if there aren't any.
            # But always show regular files.
            return ""
        size = dset.packed_size
        name = "archived: "
    else:
        n_files = dset.number_of_files
        size = dset.size
        name = ""

    return (
        f'{name} {n_files} <span class="cean-file-info-size">'
        f"({_human_readable_size(size)})</span>"
    )


def _human_readable_size(size_in_bytes: int) -> str:
    for power, prefix in ((4, "T"), (3, "G"), (2, "M"), (1, "k")):
        n = 1024**power
        if size_in_bytes >= n:
            return f"{size_in_bytes/n:.2f} {prefix}iB"
    return f"{size_in_bytes} B"


def _row_highlight_classes(field: Field) -> str:
    if field.required and field.value is None:
        return "cean-missing-value"
    if field.error:
        return "cean-error"
    return ""
