# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2022 Scitacean contributors (https://github.com/SciCatProject/scitacean)
# @author Jan-Lukas Wynen
from __future__ import annotations
from copy import deepcopy
from pathlib import Path
from typing import Dict, List, Optional, Union
import uuid

from pyscicat import model
import pyscicat.client

from ..typing import FileTransfer


class FakeClient:
    # TODO users should not rely on error messages

    def __init__(self, file_transfer: Optional[FileTransfer]):
        self.datasets: Dict[str, Union[model.DerivedDataset, model.RawDataset]] = {}
        self.orig_datablocks: Dict[str, List[model.OrigDatablock]] = {}
        self.file_transfer = file_transfer

    @classmethod
    def from_token(
        cls, *, url: str, token: str, file_transfer: Optional[FileTransfer] = None
    ) -> FakeClient:
        return FakeClient(file_transfer)

    @classmethod
    def from_credentials(
        cls,
        *,
        url: str,
        username: str,
        password: str,
        file_transfer: Optional[FileTransfer] = None,
    ) -> FakeClient:
        return FakeClient(file_transfer)

    def get_dataset_model(
        self, pid: str
    ) -> Union[model.DerivedDataset, model.RawDataset]:
        try:
            return self.datasets[pid]
        except KeyError:
            raise pyscicat.client.ScicatCommError(
                f"Unable to retrieve dataset {pid}"
            ) from None

    def get_orig_datablock(self, pid: str) -> model.OrigDatablock:
        try:
            dblocks = self.orig_datablocks[pid]
        except KeyError:
            raise pyscicat.client.ScicatCommError(
                f"Unable to retrieve orig datablock for dataset {pid}"
            ) from None
        if len(dblocks) != 1:
            raise NotImplementedError(
                f"Got {len(dblocks)} original datablocks for dataset {pid} "
                "but only support for one is implemented."
            )
        return dblocks[0]

    def create_dataset_model(self, dset: model.Dataset) -> str:
        if dset.pid is None:
            pid = f"PID.SAMPLE.PREFIX/{uuid.uuid4().hex}"
        else:
            pid = f"PID.SAMPLE.PREFIX/{dset.pid}"
            if pid in self.datasets:
                raise pyscicat.client.ScicatCommError(
                    f"Dataset id already exists: {pid}"
                )
        self.datasets[pid] = deepcopy(dset)
        self.datasets[pid].pid = pid
        return pid

    def create_orig_datablock(self, dblock: model.OrigDatablock):
        if dblock.datasetId not in self.datasets:
            raise pyscicat.client.ScicatCommError(
                f"No dataset with id {dblock.datasetId}"
            )
        self.orig_datablocks.setdefault(dblock.datasetId, []).append(dblock)

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
