# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 SciCat Project (https://github.com/SciCatProject/scitacean)
"""HTML representations for Jupyter."""

import html
from datetime import datetime
from typing import Any, Generator, List

from ..dataset import Dataset
from ..filesystem import RemotePath
from ..model import DatasetLifecycle, DatasetType, Technique
from ..pid import PID
from . import resources


def dataset_html_repr(dset: Dataset) -> str:
    template = resources.dataset_repr_template()
    style_sheet = resources.dataset_style()
    main_rows = "\n".join(
        _format_field(dset, field) for field in _get_field_specs(dset, detail=False)
    )
    detail_rows = "\n".join(
        _format_field(dset, field) for field in _get_field_specs(dset, detail=True)
    )
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
            value=html.escape(str(value)),
        )
        for name, value in dset.meta.items()
    )


def _format_field(dset: Dataset, field: Dataset.Field) -> str:
    name = field.name
    flag = _format_field_flag(field, dset)
    val = getattr(dset, field.name)
    value = (
        '<span class="cean-empty-field">None</span>'
        if val is None
        else html.escape(str(val))
    )
    typ = _format_type(field.type)
    description = html.escape(field.description)
    row_highlight = _row_highlight_classes(field, dset)

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
    "meta",  # TODO separate listing
    "source_folder",  # TODO show with files
}

_MAIN_FIELDS = (
    "pid",
    "name",
    "description",
    "creation_time",
    "proposal_id",
    "sample_id",
    "input_datasets",
)


def _get_field_specs(
    dset: Dataset, detail: bool
) -> Generator[Dataset.Field, None, None]:
    def type_filter(field: Dataset.Field) -> bool:
        if getattr(dset, field.name) is not None:
            return True
        if _used_by_dataset_type(field, dset):
            return True
        return False

    if detail:
        yield from sorted(
            filter(
                lambda f: f.name not in _MAIN_FIELDS
                and f.name not in _EXCLUDED_FIELDS
                and type_filter(f),
                Dataset.fields(),
            ),
            key=lambda f: not f.required(dset.type),
        )
    else:
        all_fields = {f.name: f for f in Dataset.fields()}
        yield from filter(type_filter, (all_fields[name] for name in _MAIN_FIELDS))


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


def _format_field_flag(field: Dataset.Field, dset: Dataset) -> str:
    if not _used_by_dataset_type(field, dset):
        return "!"
    if field.read_only:
        return "🔒"
    if field.required(dset.type):
        return '<div style="color: var(--jp-error-color0)">*</div>'
    return ""


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
        name = "archived files"
    else:
        n_files = dset.number_of_files
        size = dset.size
        name = "files"

    return f"{n_files} {name} {_human_readable_size(size)}"


def _human_readable_size(size_in_bytes: int) -> str:
    for power, prefix in ((4, "T"), (3, "G"), (2, "M"), (1, "k")):
        n = 1024**power
        if size_in_bytes >= n:
            return f"{size_in_bytes/n:.2f} {prefix}iB"
    return f"{size_in_bytes} B"


def _row_highlight_classes(field: Dataset.Field, dset: Dataset) -> str:
    value = getattr(dset, field.name)
    if field.required(dset.type) and value is None:
        return "cean-missing-value"
    if value is not None and not _used_by_dataset_type(field, dset):
        return "cean-forbidden-value"
    return ""


def _used_by_dataset_type(field: Dataset.Field, dset: Dataset) -> bool:
    return field.used_by_raw if dset.type == DatasetType.RAW else field.used_by_derived
