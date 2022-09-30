# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2022 Scitacean contributors (https://github.com/SciCatProject/scitacean)
# @author Jan-Lukas Wynen

from __future__ import annotations
from pathlib import Path
from typing import List, Optional, Tuple, Union
from uuid import uuid4

from pyscicat.client import ScicatCommError
from pyscicat.model import (
    DerivedDataset,
    DatasetType,
    OrigDatablock,
)

from .client import Client
from .file import File
from .metadata import ScientificMetadata
from ._utils import wrap_model


# TODO handle orig vs non-orig datablocks
# TODO add derive method
@wrap_model(DerivedDataset, "model", exclude=("numberOfFiles", "size", "type"))
class Dataset:
    # TODO support RawDataset
    def __init__(
        self,
        *,
        model: DerivedDataset,
        files: List[File],
        datablock: Optional[OrigDatablock],
    ):
        self._model = model
        self._files = files
        self._datablock = datablock

    @classmethod
    def new(cls, model: Optional[DerivedDataset] = None, **kwargs) -> Dataset:
        model_dict = model.dict(exclude_none=True) if model is not None else {}
        model_dict.update(kwargs)
        model_dict.setdefault("sourceFolder", "<PLACEHOLDER>")
        return Dataset(model=DerivedDataset(**model_dict), files=[], datablock=None)

    @classmethod
    def from_scicat(cls, client: Client, pid: str) -> Dataset:
        model = client.get_dataset(pid)
        dblock = client.get_orig_datablock(pid)
        return Dataset(
            model=model,
            files=[
                File.from_scicat(file, model.sourceFolder)
                for file in dblock.dataFileList
            ],
            datablock=dblock,
        )

    @property
    def model(self) -> DerivedDataset:
        return self._model

    @property
    def datablock(self) -> Optional[OrigDatablock]:
        return self._datablock

    @property
    def meta(self):
        return ScientificMetadata(self.model)

    @property
    def dataset_type(self) -> DatasetType:
        return self._model.type

    @property
    def files(self) -> Tuple[File, ...]:
        return tuple(self._files)

    def add_files(self, *files: File):
        self._files.extend(files)

    def add_local_files(
        self, *paths: Union[str, Path], relative_to: Union[str, Path] = ""
    ):
        self.add_files(
            *(File.from_local(path, relative_to=relative_to) for path in paths)
        )

    def prepare_as_new(self) -> Dataset:
        files = list(map(File.with_model_from_local_file, self._files))
        total_size = sum(file.model.size for file in files)
        dataset_id = str(uuid4())
        datablock = OrigDatablock(
            size=total_size,
            dataFileList=[file.model for file in files],
            datasetId=dataset_id,
            ownerGroup=self.model.ownerGroup,
            accessGroups=self.model.accessGroups,
        )
        model = DerivedDataset(
            **{
                **self.model.dict(exclude_none=True),
                "pid": dataset_id,
                "numberOfFiles": len(files),
                "numberOfFilesArchived": None,
                "size": total_size,
                "sourceFolder": "<PLACEHOLDER>",
            }
        )
        return Dataset(model=model, files=files, datablock=datablock)

    def upload_new_dataset_now(self, client: Client, uploader_factory):
        if self._datablock is None:
            dset = self.prepare_as_new()
        else:
            dset = self
        uploader = uploader_factory(dataset_id=dset.pid)
        dset.sourceFolder = str(uploader.remote_upload_path)
        for file in dset.files:
            file.source_folder = dset.sourceFolder
            uploader.put(local=file.local_path, remote=file.remote_access_path)

        try:
            dataset_id = client.create_dataset(dset.model)
        except ScicatCommError:
            for file in dset.files:
                uploader.revert_put(
                    local=file.local_path, remote=file.remote_access_path
                )
            raise

        dset.datablock.datasetId = dataset_id
        try:
            client.create_orig_datablock(dset.datablock)
        except ScicatCommError as exc:
            raise RuntimeError(
                f"Failed to upload original datablocks for SciCat dataset {dset.pid}:"
                f"\n{exc.args}\nThe dataset and data files were successfully uploaded "
                "but are not linked with each other. Please fix the dataset manually!"
            ) from exc

        return dset
