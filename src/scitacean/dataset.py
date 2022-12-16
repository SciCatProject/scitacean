# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2022 Scitacean contributors (https://github.com/SciCatProject/scitacean)
# @author Jan-Lukas Wynen
"""Main dataset structure."""

from __future__ import annotations

import html
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Union

from ._dataset_fields import DatasetFields
from .datablock import OrigDatablockProxy
from .file import File
from .model import DatasetLifecycle, DerivedDataset, OrigDatablock, RawDataset
from .pid import PID


class Dataset(DatasetFields):
    @property
    def history(self) -> List[Dataset]:
        # TODO convert elements to Dataset
        return self._fields["history"]

    @property
    def number_of_files(self) -> int:
        """Number of files in directly accessible storage in the dataset.

        This includes files on both the local and remote filesystems.

        Corresponds to OrigDatablocks.
        """
        return sum(map(lambda dblock: len(tuple(dblock.files)), self._orig_datablocks))

    @property
    def number_of_files_archived(self) -> int:
        """Total number of archived files in the dataset.

        Corresponds to Datablocks.
        """
        return 0

    @property
    def packed_size(self) -> int:
        """Total size of all datablock package files created for this dataset."""
        return 0

    @property
    def size(self) -> int:
        """Total size of files in directly accessible storage in the dataset.

        This includes files on both the local and remote filesystems.

        Corresponds to OrigDatablocks.
        """
        return sum(file.size for file in self.files)

    @property
    def files(self) -> Iterable[File]:
        """Files linked with the dataset."""
        for dblock in self._orig_datablocks:
            yield from dblock.files

    def add_files(self, *files: File, datablock: Union[int, str, PID] = -1):
        """Add files to the dataset."""
        self._get_or_add_orig_datablock(datablock).add_files(*files)

    def add_local_files(
        self,
        *paths: Union[str, Path],
        base_path: Union[str, Path] = "",
        datablock: Union[int, str, PID] = -1,
    ):
        """Add files on the local file system to the dataset.

        Parameters
        ----------
        paths:
            Local paths to the files.
        base_path:
            The remote paths will be set up according to
            ``remote = [path.relative_to(base_path) for path in paths]``.
        datablock:
            Select the orig datablock to store the file in.
            If an ``int``, use the datablock with that index.
            If a ``str`` or ``PID``, use the datablock with that id;
            if there is none with matching id, raise ``KeyError``.
        """
        self.add_files(
            *(File.from_local(path, base_path=base_path) for path in paths),
            datablock=datablock,
        )

    def replace(self, *, _read_only: Dict[str, Any] = None, **replacements) -> Dataset:
        """Return a new dataset with replaced fields.

        Returns
        -------
        :
            The new dataset has the same fields as the input but all fields given
            as keyword arguments are replaced by the given values.
        """
        _read_only = _read_only or {}

        def get_val(source, name):
            try:
                return source.pop(name)
            except KeyError:
                return getattr(self, name)

        read_only = {
            field.name: get_val(_read_only, field.name)
            for field in Dataset.fields(read_only=True)
        }
        kwargs = {
            **{
                field.name: get_val(replacements, field.name)
                for field in Dataset.fields(read_only=False)
            },
            "_pid": read_only.pop("pid"),
        }
        if replacements or _read_only:
            raise TypeError(
                f"Invalid arguments: {', '.join((*replacements, *_read_only))}"
            )
        return Dataset(
            _orig_datablocks=deepcopy(self._orig_datablocks),
            _read_only=read_only,
            **kwargs,
        )

    def make_models(self) -> SciCatModels:
        """Build models to send to SciCat.

        Creates model for both the dataset and datablocks.

        Returns
        -------
        :
            Created models.
        """
        if self.number_of_files == 0:
            return SciCatModels(dataset=self.make_dataset_model(), orig_datablocks=None)
        return SciCatModels(
            dataset=self.make_dataset_model(),
            orig_datablocks=[
                dblock.make_model(self) for dblock in self._orig_datablocks
            ],
        )

    def __eq__(self, other: Dataset) -> bool:
        if not isinstance(other, Dataset):
            return False
        eq = all(
            getattr(self, field.name) == getattr(other, field.name)
            for field in Dataset.fields()
        )
        return eq

    def add_orig_datablock(
        self, *, checksum_algorithm: Optional[str]
    ) -> OrigDatablockProxy:
        dblock = OrigDatablockProxy(checksum_algorithm=checksum_algorithm)
        self._orig_datablocks.append(dblock)
        return dblock

    def _lookup_orig_datablock(self, pid: PID) -> OrigDatablockProxy:
        try:
            return next(db for db in self._orig_datablocks if db.pid == pid)
        except StopIteration:
            raise KeyError(f"No OrigDatablock with id {PID}") from None

    def _get_or_add_orig_datablock(
        self, key: Union[int, str, PID]
    ) -> OrigDatablockProxy:
        if isinstance(key, (str, PID)):
            return self._lookup_orig_datablock(PID.parse(key))
        # The oth datablock is implicitly always there and created on demand.
        if key in (0, -1) and not self._orig_datablocks:
            return self.add_orig_datablock(
                checksum_algorithm=self._default_checksum_algorithm
            )
        return self._orig_datablocks[key]

    def _repr_html_(self):
        rows = "\n".join(
            _format_field(self, field)
            for field in sorted(
                Dataset.fields(), key=lambda f: not f.required(self.type)
            )
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


def _format_type(typ) -> str:
    try:
        return {
            str: "str",
            int: "int",
            bool: "bool",
            datetime: "datetime",
            PID: "PID",
            DatasetLifecycle: "DatasetLifecycle",
            List[str]: "list[str]",
            List[dict]: "list[dict]",
        }[typ]
    except KeyError:
        return html.escape(str(typ))


@dataclass
class SciCatModels:
    dataset: Union[DerivedDataset, RawDataset]
    orig_datablocks: Optional[List[OrigDatablock]]
