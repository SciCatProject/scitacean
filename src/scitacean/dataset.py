# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2022 Scitacean contributors (https://github.com/SciCatProject/scitacean)
# @author Jan-Lukas Wynen

from __future__ import annotations

import dataclasses
from collections import namedtuple
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from uuid import uuid4

from pyscicat.client import ScicatCommError
from pyscicat.model import DerivedDataset, OrigDatablock, RawDataset

from .client import Client
from .file import File
from .typing import Uploader
from ._dataset_fields import DatasetFields


SciCatModels = namedtuple("SciCatModels", ["dataset", "datablock"])


# TODO handle orig vs non-orig datablocks
# TODO add derive method
class Dataset(DatasetFields):
    # If self._datablock is None, the dataset does not exist on remote
    def __init__(
        self,
        *,
        files: List[File],
        datablock: Optional[OrigDatablock],
        meta: Dict[str, Any],
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._files = files
        self._datablock = datablock
        self._meta = dict(meta)

    @classmethod
    def new(
        cls,
        *,
        model: Optional[Union[DerivedDataset, RawDataset]] = None,
        meta: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dataset:
        # TODO some model fields are ignores, e.g. size
        model_dict = cls._map_model_to_field_dict(model) if model is not None else {}
        model_dict.update(kwargs)
        meta = {} if meta is None else dict(meta)
        if model.scientificMetadata:
            meta.update(model.scientificMetadata)
            model.scientificMetadata = None
        return Dataset(files=[], datablock=None, meta=meta, **model_dict)

    @classmethod
    def from_scicat(cls, client: Client, pid: str) -> Dataset:
        model = client.get_dataset_model(pid)
        dblock = client.get_orig_datablock(pid)
        meta = model.scientificMetadata
        if meta is None:
            meta = {}
        model.scientificMetadata = None
        return Dataset(
            files=[
                File.from_scicat(file, source_folder=model.sourceFolder)
                for file in dblock.dataFileList
            ],
            datablock=dblock,
            meta=meta,
            **cls._map_model_to_field_dict(model),
        )

    @property
    def meta(self) -> Dict[str, Any]:
        return self._meta

    @property
    def size(self) -> int:
        return sum(file.size for file in self.files)

    @property
    def files(self) -> Tuple[File, ...]:
        return tuple(self._files)

    def add_files(self, *files: File):
        self._files.extend(files)

    def add_local_files(
        self,
        *paths: Union[str, Path],
        base_path: Union[str, Path] = "",
    ):
        self.add_files(*(File.from_local(path, base_path=base_path) for path in paths))

    def assign_new_pid(self):
        self.pid = str(uuid4())

    def make_scicat_models(self) -> SciCatModels:
        if self.pid is None:
            raise ValueError(
                "The dataset PID must be set before creating SciCat models."
            )
        total_size = sum(file.model.size for file in self.files)
        datablock = OrigDatablock(
            size=total_size,
            dataFileList=[file.model for file in self.files],
            datasetId=self.pid,
            ownerGroup=self.owner_group,
            accessGroups=self.access_groups,
        )
        try:
            model = self._map_to_model(
                number_of_files=len(self.files) or None,
                number_of_files_archived=None,
                packed_size=None,
                size=total_size or None,
                scientific_metadata=self.meta or None,
            )
        except KeyError as err:
            raise TypeError(
                f"Field {err} is not allowed in {self.dataset_type} datasets"
            ) from None
        return SciCatModels(dataset=model, datablock=datablock)

    def prepare_as_new(self):
        dset = Dataset(
            files=self._files,
            datablock=self._datablock,
            meta=self._meta,
            **dataclasses.asdict(self),
        )
        dset.assign_new_pid()
        return dset

    def upload_new_dataset_now(self, client: Client, uploader: Uploader) -> Dataset:
        dset = self.prepare_as_new()
        with uploader.connect_for_upload(dset.pid) as con:
            dset.source_folder = con.source_dir
            for file in dset.files:
                file.source_folder = dset.source_folder
                con.upload_file(local=file.local_path, remote=file.remote_access_path)

            models = dset.make_scicat_models()
            try:
                dataset_id = client.create_dataset_model(models.dataset)
            except ScicatCommError:
                for file in dset.files:
                    con.revert_upload(
                        local=file.local_path, remote=file.remote_access_path
                    )
                raise

        models.datablock.datasetId = dataset_id
        try:
            client.create_orig_datablock(models.datablock)
        except ScicatCommError as exc:
            raise RuntimeError(
                f"Failed to upload original datablocks for SciCat dataset {dset.pid}:"
                f"\n{exc.args}\nThe dataset and data files were successfully uploaded "
                "but are not linked with each other. Please fix the dataset manually!"
            ) from exc

        return dset
