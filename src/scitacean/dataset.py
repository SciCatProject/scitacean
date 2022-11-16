# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2022 Scitacean contributors (https://github.com/SciCatProject/scitacean)
# @author Jan-Lukas Wynen
"""Main dataset structure."""

from __future__ import annotations

import dataclasses
from collections import namedtuple
import html
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import typing
from uuid import uuid4

from pyscicat.model import DerivedDataset, OrigDatablock, RawDataset

from .file import File
from .pid import PID
from ._dataset_fields import DatasetFields

SciCatModels = namedtuple("SciCatModels", ["dataset", "datablock"])


# TODO handle orig vs non-orig datablocks
# TODO add derive method
class Dataset(DatasetFields):
    """Store metadata and links to files.

    ``Dataset`` has a large number of attributes that map onto the fields
    in a SciCat dataset.
    See also :class:`scitacean._dataset_fields.DatasetFields` for a complete list.
    For the time being, see also :class:`pyscicat.model.DerivedDataset` and
    :class:`pyscicat.model.RawDataset` for which fields are required by which
    dataset type.
    """

    # If self._datablock is None, the dataset does not exist on remote
    def __init__(
        self,
        *,
        files: List[File],
        datablock: Optional[OrigDatablock],
        meta: Dict[str, Any],
        pid: Optional[Union[PID, str]],
        **kwargs,
    ):
        """Use :meth:`Dataset.new` instead."""
        super().__init__(**kwargs)
        self._files = files
        self._datablock = datablock
        self._meta = dict(meta)
        self.pid = pid

    @classmethod
    def new(
        cls,
        *,
        model: Optional[Union[DerivedDataset, RawDataset]] = None,
        meta: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dataset:
        """Create a new Dataset.

        The dataset has no files and is not linked or uploaded to SciCat.

        Parameters
        ----------
        model:
            pydantic model of the dataset.
            Contents are incorporated into the new Dataset.
        meta:
            dict of scientific metadata.
        kwargs:
            Merged with ``model`` to fill the dataset fields.
            Items in ``kwargs`` override items of the same key in ``model``.

        Returns
        -------
        :
            A new dataset.
        """
        # TODO some model fields are ignores, e.g. size
        model_dict = cls._map_model_to_field_dict(model) if model is not None else {}
        model_dict.update(kwargs)
        model_dict["pid"] = model.pid if model is not None else None
        meta = {} if meta is None else dict(meta)
        if model is not None and model.scientificMetadata:
            meta.update(model.scientificMetadata)
            model.scientificMetadata = None
        return Dataset(files=[], datablock=None, meta=meta, **model_dict)

    @classmethod
    def from_models(
        cls,
        *,
        dataset_model: Union[DerivedDataset, RawDataset],
        orig_datablock_models: List[OrigDatablock],
    ):
        """Create a new dataset from fully filled in models.

        Parameters
        ----------
        dataset_model:
            Fields, including scientific metadata are filled from this model.
        orig_datablock_models:
            File links are populated from this model.

        Returns
        -------
        :
            A new dataset.
        """
        if len(orig_datablock_models) != 1:
            raise NotImplementedError(
                f"Got {len(orig_datablock_models)} original datablocks for "
                f"dataset {dataset_model.pid} but only support for one is implemented."
            )
        dblock = orig_datablock_models[0]

        meta = dataset_model.scientificMetadata
        if meta is None:
            meta = {}
        return Dataset(
            files=[
                File.from_scicat(file, source_folder=dataset_model.sourceFolder)
                for file in dblock.dataFileList
            ],
            datablock=dblock,
            meta=meta,
            pid=dataset_model.pid,
            **{
                k: v
                for k, v in cls._map_model_to_field_dict(dataset_model).items()
                if k != "scientificMetadata"
            },
        )

    @property
    def meta(self) -> Dict[str, Any]:
        """Dictionary of scientific metadata."""
        return self._meta

    @property
    def pid(self) -> Optional[PID]:
        """ID of the dataset."""
        return self._pid

    @pid.setter
    def pid(self, pid: Optional[Union[PID, str]]):
        """Set the ID of the dataset."""
        self._pid = pid if isinstance(pid, PID) or pid is None else PID.parse(pid)

    @property
    def size(self) -> int:
        """Combined size of all files."""
        return sum(file.size for file in self.files)

    @property
    def files(self) -> Tuple[File, ...]:
        """Currently linked files."""
        return tuple(self._files)

    def add_files(self, *files: File):
        """Add files to the dataset."""
        self._files.extend(files)

    def add_local_files(
        self,
        *paths: Union[str, Path],
        base_path: Union[str, Path] = "",
    ):
        """Add files on the local file system to the dataset.

        Parameters
        ----------
        paths:
            Local paths to the files.
        base_path:
            The remote paths will be set up according to
            ``remote = [path.relative_to(base_path) for path in paths]``.
        """
        self.add_files(*(File.from_local(path, base_path=base_path) for path in paths))

    def make_scicat_models(self) -> SciCatModels:
        """Build models to send to SciCat.

        Creates both a model for that dataset and orig datablocks.

        Returns
        -------
        :
            Created models.
        """
        if self.pid is None:
            raise ValueError(
                "The dataset PID must be set before creating SciCat models."
            )
        total_size = sum(file.model.size for file in self.files)
        datablock = OrigDatablock(
            size=total_size,
            dataFileList=[file.model for file in self.files],
            datasetId=str(self.pid),
            ownerGroup=self.owner_group,
            accessGroups=self.access_groups,
        )
        try:
            model = self._map_to_model(
                number_of_files=len(self.files) or None,
                number_of_files_archived=None,
                packed_size=None,
                pid=str(self.pid) if self.pid is not None else None,
                size=total_size or None,
                scientific_metadata=self.meta or None,
            )
        except KeyError as err:
            raise TypeError(
                f"Field {err} is not allowed in {self.dataset_type} datasets"
            ) from None
        return SciCatModels(dataset=model, datablock=datablock)

    def prepare_as_new(self):
        """Return a copy of this dataset that looks like a new dataset."""
        dset = Dataset(
            files=self._files,
            datablock=self._datablock,
            meta=self._meta,
            pid=PID(pid=str(uuid4()), prefix=None),
            **dataclasses.asdict(self),
        )
        dset.history = None
        dset.updated_at = None
        dset.updated_by = None
        return dset

    def _repr_html_(self):
        rows = "\n".join(
            _format_field(self, field) for field in dataclasses.fields(self)
        )
        return f"""<table>
        <tr>
            <th>Name</th><th>Required</th><th>Type</th><th>Value</th><th>Description</th>
        </tr>
        {rows}
    </table>"""


def _format_field(dset, field) -> str:
    name = field.name
    required = "*" if not _is_optional(field.type) else ""
    value = html.escape(str(getattr(dset, field.name)))
    typ = _format_type(field.type)
    description = html.escape("N/A")
    return (
        "<tr><td>"
        + "</td><td>".join((name, required, typ, value, description))
        + "</tr></td>"
    )


def _format_type(typ) -> str:
    if _is_optional(typ):
        typ = next(iter(arg for arg in typing.get_args(typ) if not _is_none_type(arg)))

    if typ == str:
        return "str"
    if typ == bool:
        return "bool"
    if typ == List[str]:
        return "list[str]"
    return html.escape(str(typ))


def _is_none_type(x) -> bool:
    # We want to actually compare types but flake8 doesn't like it.
    return x == type(None)  # noqa: [E721]


def _is_optional(typ):
    return typing.get_origin(typ) == Union and type(None) in typing.get_args(typ)
