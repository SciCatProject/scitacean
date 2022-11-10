# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2022 Scitacean contributors (https://github.com/SciCatProject/scitacean)
# @author Jan-Lukas Wynen
from __future__ import annotations

import functools
from copy import deepcopy
from pathlib import Path
from typing import Dict, List, Optional, Union
import uuid

from pyscicat import model
import pyscicat.client

from ..dataset import Dataset
from ..pid import PID
from ..typing import FileTransfer


def _conditionally_disabled(func):
    @functools.wraps(func)
    def impl(self, *args, **kwargs):
        if (exc := self.main.disabled.get(func.__name__)) is not None:
            raise exc
        return func(self, *args, **kwargs)

    return impl


class FakeClient:
    # TODO users should not rely on error messages

    def __init__(
        self,
        *,
        file_transfer: Optional[FileTransfer] = None,
        disable: Optional[Dict[str, Exception]] = None,
    ):
        self._scicat_client = FakeScicatClient(self)
        self.disabled = {} if disable is None else dict(disable)
        self.datasets: Dict[PID, Union[model.DerivedDataset, model.RawDataset]] = {}
        self.orig_datablocks: Dict[PID, List[model.OrigDatablock]] = {}
        self.file_transfer = file_transfer

    @classmethod
    def from_token(
        cls, *, url: str, token: str, file_transfer: Optional[FileTransfer] = None
    ) -> FakeClient:
        return FakeClient(file_transfer=file_transfer)

    @classmethod
    def from_credentials(
        cls,
        *,
        url: str,
        username: str,
        password: str,
        file_transfer: Optional[FileTransfer] = None,
    ) -> FakeClient:
        return FakeClient(file_transfer=file_transfer)

    def get_dataset(self, pid: Union[PID, str]) -> Dataset:
        return Dataset.from_models(
            dataset_model=self.scicat.get_dataset_model(str(pid)),
            orig_datablock_models=self.scicat.get_orig_datablocks(str(pid)),
        )

    @property
    def scicat(self) -> FakeScicatClient:
        return self._scicat_client

    def download_file(self, *, remote: Union[str, Path], local: Union[str, Path]):
        if self.file_transfer is None:
            raise RuntimeError(
                f"No file transfer handler specified, cannot download file {remote}"
            )
        with self.file_transfer.connect_for_download() as con:
            con.download_file(remote=remote, local=local)

    def upload_file(
        self, *, dataset_id: str, remote: Union[str, Path], local: Union[str, Path]
    ) -> str:
        if self.file_transfer is None:
            raise RuntimeError(
                f"No file transfer handler specified, cannot upload file {local}"
            )
        with self.file_transfer.connect_for_upload(dataset_id) as con:
            return con.upload_file(remote=remote, local=local)


class FakeScicatClient:
    def __init__(self, main_client):
        self.main = main_client

    @_conditionally_disabled
    def get_dataset_model(
        self, pid: str
    ) -> Union[model.DerivedDataset, model.RawDataset]:
        try:
            return self.main.datasets[pid]
        except KeyError:
            raise pyscicat.client.ScicatCommError(
                f"Unable to retrieve dataset {pid}"
            ) from None

    @_conditionally_disabled
    def get_orig_datablocks(self, pid: str) -> List[model.OrigDatablock]:
        try:
            return self.main.orig_datablocks[pid]
        except KeyError:
            raise pyscicat.client.ScicatCommError(
                f"Unable to retrieve orig datablock for dataset {pid}"
            ) from None

    @_conditionally_disabled
    def create_dataset_model(self, dset: model.Dataset) -> str:
        pid = PID(
            pid=dset.pid if dset.pid is not None else str(uuid.uuid4().hex),
            prefix="PID.SAMPLE.PREFIX",
        )
        if pid in self.main.datasets:
            raise pyscicat.client.ScicatCommError(f"Dataset id already exists: {pid}")
        self.main.datasets[pid] = deepcopy(dset)
        self.main.datasets[pid].pid = str(pid)
        return str(pid)

    @_conditionally_disabled
    def create_orig_datablock(self, dblock: model.OrigDatablock):
        dataset_id = PID.parse(dblock.datasetId)
        if dataset_id not in self.main.datasets:
            raise pyscicat.client.ScicatCommError(f"No dataset with id {dataset_id}")
        self.main.orig_datablocks.setdefault(dataset_id, []).append(dblock)
