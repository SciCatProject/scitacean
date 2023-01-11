# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 SciCat Project (https://github.com/SciCatProject/scitacean)
"""Main dataset structure."""

from __future__ import annotations

import dataclasses
import html
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Generator, Iterable, List, Literal, Optional, Union

from ._dataset_fields import DatasetFields, fields_from_model
from .datablock import OrigDatablockProxy
from .file import File
from .model import (
    DatasetLifecycle,
    DatasetType,
    DerivedDataset,
    OrigDatablock,
    RawDataset,
)
from .pid import PID


class Dataset(DatasetFields):
    @classmethod
    def from_models(
        cls,
        *,
        dataset_model: Union[DerivedDataset, RawDataset],
        orig_datablock_models: Optional[List[OrigDatablock]],
    ) -> Dataset:
        """Create a new dataset from pydantic models.

        This function is mainly meant to be used with
        models that were downloaded from SciCat.
        :meth:`Dataset.__init__` should be preferred for other use cases.

        Parameters
        ----------
        dataset_model:
            Fields, including scientific metadata are filled from this model.
        orig_datablock_models:
            File links are populated from this model.
            All files are initialized to be on remote but not local.

        Returns
        -------
        :
            A new dataset.
        """
        args = fields_from_model(dataset_model)
        read_only_args = args.pop("_read_only")
        read_only_args["history"] = dataset_model.history
        return cls(
            type=dataset_model.type,
            creation_time=dataset_model.creationTime,
            _pid=dataset_model.pid,
            _orig_datablocks=[]
            if not orig_datablock_models
            else [
                OrigDatablockProxy.from_model(
                    dataset_model=dataset_model, orig_datablock_model=dblock
                )
                for dblock in orig_datablock_models
            ],
            _read_only=read_only_args,
            **args,
        )

    @classmethod
    def fields(
        cls,
        dataset_type: Optional[Union[DatasetType, Literal["derived", "raw"]]] = None,
        read_only: Optional[bool] = None,
    ) -> Generator[Dataset.Field, None, None]:
        """Iterator over dataset fields.

        This is similar to :func:`dataclasses.fields`.

        Parameters
        ----------
        dataset_type:
            If set, return only the fields for this dataset type.
            If unset, do not filter fields.
        read_only:
            If true or false, return only fields which are read-only
            or allow write-access, respectively.
            If unset, do not filter fields.

        Returns
        -------
        :
            Iterable over the fields of datasets.
        """
        it = iter(DatasetFields._FIELD_SPEC)
        if dataset_type is not None:
            attr = (
                "used_by_derived"
                if dataset_type == DatasetType.DERIVED
                else "used_by_raw"
            )
            it = filter(lambda field: getattr(field, attr), it)
        if read_only is not None:
            it = filter(lambda field: field.read_only == read_only, it)
        yield from it

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

    def add_files(self, *files: File, datablock: Union[int, str, PID] = -1) -> None:
        """Add files to the dataset."""
        self._get_or_add_orig_datablock(datablock).add_files(*files)

    def add_local_files(
        self,
        *paths: Union[str, Path],
        base_path: Union[str, Path] = "",
        datablock: Union[int, str, PID] = -1,
    ) -> None:
        """Add files on the local file system to the dataset.

        Parameters
        ----------
        paths:
            Local paths to the files.
        base_path:
            The remote paths will be set up according to

            ``remotes = [path.relative_to(base_path) for path in paths]``.
        datablock:
            Advanced feature, do not set unless you know what this is!

            Select the orig datablock to store the file in.
            If an ``int``, use the datablock with that index.
            If a ``str`` or ``PID``, use the datablock with that id;
            if there is none with matching id, raise ``KeyError``.
        """
        self.add_files(
            *(File.from_local(path, base_path=base_path) for path in paths),
            datablock=datablock,
        )

    def replace(
        self,
        *,
        _read_only: Optional[Dict[str, Any]] = None,
        _orig_datablocks: Optional[List[OrigDatablockProxy]] = None,
        **replacements: Any,
    ) -> Dataset:
        """Return a new dataset with replaced fields.

        Parameters starting with an underscore are for internal use.
        Using them may result in a broken dataset.

        Parameters
        ----------
        replacements:
            New field values.

        Returns
        -------
        :
            The new dataset has the same fields as the input but all fields given
            as keyword arguments are replaced by the given values.
        """
        _read_only = _read_only or {}

        def get_val(source: Dict[str, Any], name: str) -> Any:
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
            _orig_datablocks=deepcopy(
                _orig_datablocks
                if _orig_datablocks is not None
                else self._orig_datablocks
            ),
            _read_only=read_only,
            **kwargs,
        )

    def replace_files(self, *files: File) -> Dataset:
        """Return a new dataset with replaced files.

        For each argument, if the input dataset has a file with the
        same remote path, that file is replaced.
        Otherwise, a new file is added.
        Other existing files are kept in the returned dataset.

        Parameters
        ----------
        files:
            New files for the dataset.

        Returns
        -------
        :
            A new dataset with given files.
        """

        def new_or_old(old: File) -> File:
            for new in files:
                if old.remote_path == new.remote_path:
                    return new
            return old

        return self.replace(
            _orig_datablocks=[
                dataclasses.replace(dblock, init_files=map(new_or_old, dblock.files))
                for dblock in self._orig_datablocks
            ]
        )

    def make_datablock_models(self) -> DatablockModels:
        """Build models for all contained (orig) datablocks.

        Returns
        -------
        :
            Structure with datablock and orig datablock models.
        """
        if self.number_of_files == 0:
            return DatablockModels(orig_datablocks=None)
        return DatablockModels(
            orig_datablocks=[
                dblock.make_model(self) for dblock in self._orig_datablocks
            ]
        )

    def make_model(self) -> Union[DerivedDataset, RawDataset]:
        """Build a dataset model to send to SciCat.

        This triggers validation of the dataset.
        All fields must therefore be properly initialized for a dataset of type
        ``self.type`` before calling ``make_model``.

        Returns
        -------
        :
            Created model.
        """
        if self.type == DatasetType.DERIVED:
            return self._make_derived_model()
        return self._make_raw_model()

    def __eq__(self, other: object) -> bool:
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
        """Append a new orig datablock to the list of orig datablocks.

        Parameters
        ----------
        checksum_algorithm:
            Use this algorithm to compute checksums of files
            associated with this datablock.

        Returns
        -------
        :
            The newly added datablock.
        """
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

    def __str__(self) -> str:
        args = ", ".join(
            f"{name}={value}"
            for name, value in (
                (field.name, getattr(self, field.name)) for field in self.fields()
            )
            if value is not None
        )
        return f"Dataset({args})"

    def _repr_html_(self) -> str:
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


@dataclasses.dataclass
class DatablockModels:
    """Pydantic models for (orig) datablocks."""

    # TODO
    # datablocks: Optional[List[Datablock]]
    orig_datablocks: Optional[List[OrigDatablock]]
    """Orig datablocks"""
