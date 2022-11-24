# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2022 Scitacean contributors (https://github.com/SciCatProject/scitacean)
# @author Jan-Lukas Wynen
"""Main dataset structure."""

from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Union

from ._dataset_fields import DatasetFields
from .file import File
from .model import DerivedDataset, OrigDatablock, RawDataset


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
        return len(self._files)

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
        yield from self._files

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
        return Dataset(_files=self._files, _read_only=read_only, **kwargs)

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
        datablock = OrigDatablock(
            size=self.size,
            dataFileList=[file.make_model() for file in self.files],
            datasetId=self.pid,
            ownerGroup=self.owner_group,
            accessGroups=self.access_groups,
            instrumentGroup=self.instrument_group,
        )
        return SciCatModels(
            dataset=self.make_dataset_model(), orig_datablocks=[datablock]
        )

    def __eq__(self, other: Dataset) -> bool:
        if not isinstance(other, Dataset):
            return False
        for field in Dataset.fields():
            if getattr(self, field.name) != getattr(other, field.name):
                print(
                    field.name,
                    ":",
                    getattr(self, field.name),
                    getattr(other, field.name),
                )
        eq = all(
            getattr(self, field.name) == getattr(other, field.name)
            for field in Dataset.fields()
        )
        print("equal?", eq)
        return eq


@dataclass
class SciCatModels:
    dataset: Union[DerivedDataset, RawDataset]
    orig_datablocks: Optional[List[OrigDatablock]]


#
# import dataclasses
# from collections import namedtuple
# import html
# from pathlib import Path
# import typing
# from uuid import uuid4
#
# from pyscicat.model import DerivedDataset, OrigDatablock, RawDataset
#
# from .file import File
# from .pid import PID
# from ._dataset_fields import DatasetFields
#
# SciCatModels = namedtuple("SciCatModels", ["dataset", "datablock"])
#
#
# # TODO handle orig vs non-orig datablocks
# # TODO add derive method
# class Dataset(DatasetFields):
#     """Store metadata and links to files.
#
#     ``Dataset`` has a large number of attributes that map onto the fields
#     in a SciCat dataset.
#     See also :class:`scitacean._dataset_fields.DatasetFields` for a complete list.
#     For the time being, see also :class:`pyscicat.model.DerivedDataset` and
#     :class:`pyscicat.model.RawDataset` for which fields are required by which
#     dataset type.
#     """
#
#     # If self._datablock is None, the dataset does not exist on remote
#     def __init__(
#         self,
#         *,
#         files: List[File],
#         datablock: Optional[OrigDatablock],
#         meta: Dict[str, Any],
#         pid: Optional[Union[PID, str]],
#         **kwargs,
#     ):
#         """Use :meth:`Dataset.new` instead."""
#         super().__init__(**kwargs)
#         self._files = files
#         self._datablock = datablock
#         self._meta = dict(meta)
#         self.pid = pid
#
#     @classmethod
#     def new(
#         cls,
#         *,
#         model: Optional[Union[DerivedDataset, RawDataset]] = None,
#         meta: Optional[Dict[str, Any]] = None,
#         **kwargs,
#     ) -> Dataset:
#         """Create a new Dataset.
#
#         The dataset has no files and is not linked or uploaded to SciCat.
#
#         Parameters
#         ----------
#         model:
#             pydantic model of the dataset.
#             Contents are incorporated into the new Dataset.
#         meta:
#             dict of scientific metadata.
#         kwargs:
#             Merged with ``model`` to fill the dataset fields.
#             Items in ``kwargs`` override items of the same key in ``model``.
#
#         Returns
#         -------
#         :
#             A new dataset.
#         """
#         # TODO some model fields are ignores, e.g. size
#         model_dict = cls._map_model_to_field_dict(model) if model is not None else {}
#         model_dict.update(kwargs)
#         model_dict["pid"] = model.pid if model is not None else None
#         meta = {} if meta is None else dict(meta)
#         if model is not None and model.scientificMetadata:
#             meta.update(model.scientificMetadata)
#             model.scientificMetadata = None
#         return Dataset(files=[], datablock=None, meta=meta, **model_dict)
#
#     @classmethod
#     def from_models(
#         cls,
#         *,
#         dataset_model: Union[DerivedDataset, RawDataset],
#         orig_datablock_models: List[OrigDatablock],
#     ):
#         """Create a new dataset from fully filled in models.
#
#         Parameters
#         ----------
#         dataset_model:
#             Fields, including scientific metadata are filled from this model.
#         orig_datablock_models:
#             File links are populated from this model.
#
#         Returns
#         -------
#         :
#             A new dataset.
#         """
#         if len(orig_datablock_models) != 1:
#             raise NotImplementedError(
#                 f"Got {len(orig_datablock_models)} original datablocks for "
#        f"dataset {dataset_model.pid} but only support for one is implemented."
#             )
#         dblock = orig_datablock_models[0]
#
#         meta = dataset_model.scientificMetadata
#         if meta is None:
#             meta = {}
#         return Dataset(
#             files=[
#                 File.from_scicat(file, source_folder=dataset_model.sourceFolder)
#                 for file in dblock.dataFileList
#             ],
#             datablock=dblock,
#             meta=meta,
#             pid=dataset_model.pid,
#             **{
#                 k: v
#                 for k, v in cls._map_model_to_field_dict(dataset_model).items()
#                 if k != "scientificMetadata"
#             },
#         )
#
#     @property
#     def meta(self) -> Dict[str, Any]:
#         """Dictionary of scientific metadata."""
#         return self._meta
#
#     @property
#     def pid(self) -> Optional[PID]:
#         """ID of the dataset."""
#         return self._pid
#
#     @pid.setter
#     def pid(self, pid: Optional[Union[PID, str]]):
#         """Set the ID of the dataset."""
#         self._pid = pid if isinstance(pid, PID) or pid is None else PID.parse(pid)
#
#


#     def prepare_as_new(self):
#         """Return a copy of this dataset that looks like a new dataset."""
#         dset = Dataset(
#             files=self._files,
#             datablock=self._datablock,
#             meta=self._meta,
#             pid=PID(pid=str(uuid4()), prefix=None),
#             **dataclasses.asdict(self),
#         )
#         dset.history = None
#         dset.updated_at = None
#         dset.updated_by = None
#         return dset
#
#     def _repr_html_(self):
#         rows = "\n".join(
#             _format_field(self, field) for field in dataclasses.fields(self)
#         )
#         return f"""<table>
#         <tr>
#             <th>Name</th><th>Required</th><th>Type</th><th>Value</th><th>Description</th>
#         </tr>
#         {rows}
#     </table>"""
#
#
# def _format_field(dset, field) -> str:
#     name = field.name
#     required = "*" if not _is_optional(field.type) else ""
#     value = html.escape(str(getattr(dset, field.name)))
#     typ = _format_type(field.type)
#     description = html.escape("N/A")
#     return (
#         "<tr><td>"
#         + "</td><td>".join((name, required, typ, value, description))
#         + "</tr></td>"
#     )
#
#
# def _format_type(typ) -> str:
#     if _is_optional(typ):
# typ = next(iter(arg for arg in typing.get_args(typ) if not _is_none_type(arg)))
#
#     if typ == str:
#         return "str"
#     if typ == bool:
#         return "bool"
#     if typ == List[str]:
#         return "list[str]"
#     return html.escape(str(typ))
#
#
# def _is_none_type(x) -> bool:
#     # We want to actually compare types but flake8 doesn't like it.
#     return x == type(None)  # noqa: [E721]
#
#
# def _is_optional(typ):
#     return typing.get_origin(typ) == Union and type(None) in typing.get_args(typ)
