# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2022 Scitacean contributors (https://github.com/SciCatProject/scitacean)
# @author Jan-Lukas Wynen
"""Fake client for testing."""

from __future__ import annotations

import functools
from copy import deepcopy
from pathlib import Path
from typing import Dict, List, Optional, Union
import uuid

from pyscicat import model
import pyscicat.client

from ..client import Client, ScicatClient
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


# Inherits from Client to satisfy type hints.
class FakeClient(Client):
    """Mimics a client without accessing the internet.

    This class is a stand in for :class:`scitacean.Client` to emulate downloading and
    uploading of datasets without actually accessing a SciCat server.

    Since this client fakes communication with SciCat, it stores raw
    `pydantic <https://pydantic-docs.helpmanual.io/>`_ models, namely

    - ``FakeClient.datasets``:
            :class:`dict` of :class:`pydantic.model.DerivedDataset` and
            :class:`pydantic.model.RawDataset`,
            indexed by dataset ID.
    - ``FakeClient.orig_datablocks``:
            :class:`dict` of lists of :class:`pydantic.model.OrigDatablock`,
            indexed by the *dataset* ID.

    Individual functions can be disabled (that is made to raise an exception)
    using the ``disabled`` argument of the initializer.

    Important
    ---------
    ``FakeClient`` does not behave exactly like a ``Client`` connected to a real
    server as that would require reimplementing a large part of the SciCat backend.
    You should thus always test your code against a (potentially locally deployed)
    real server.

    In particular, do not rely on specific error messages or the detailed settings
    in the datasets returned by ``FakeClient.upload_new_dataset_now``!

    Examples
    --------
    Set up a fake client for download:

    .. code-block:: python

        client = FakeClient()
        pid = PID(prefix="sample.prefix", pid="1234-5678-abcd")
        client.datasets[pid] = pyscicat.model.DerivedDataset(...)
        client.orig_datablocks[pid] = [pyscicat.model.OrigDatablock(
            datasetID=str(pid),
            ...
        )]
        client.get_dataset(pid)

    Use to upload a dataset:

    .. code-block:: python

        client = FakeClient(file_transfer=FakeFileTransfer())
        finalized = client.upload_new_dataset_now(dset)

        # contains new dataset and datablock:
        client.datasets[finalized.pid]
        client.orig_datablocks[finalized.pid]

    Disable a method:

    .. code-block:: python

        client = FakeClient(
            disable={"create_dataset_model": RuntimeError("Upload failed")})
        # raises RuntimeError("Upload failed"):
        client.upload_new_dataset_now(dset)

    See Also
    --------
    scitacean.testing.transfer.FakeFileTransfer: Fake file up-/downloads
        without a real server.
    """

    def __init__(
        self,
        *,
        file_transfer: Optional[FileTransfer] = None,
        disable: Optional[Dict[str, Exception]] = None,
    ):
        """Initialize a fake client with empty dataset storage.

        Parameters
        ----------
        file_transfer:
            Typically :class:`scitacean.testing.transfer.FakeFileTransfer`
            but may be a real file transfer.
        disable:
            dict function names to exceptions. Functions listed here raise
            the given exception when called and do nothing else.
        """
        # Normally, client must not be None, but the fake must never
        # call it, so setting it to None serves as an extra safeguard.
        super().__init__(client=None, file_transfer=file_transfer)  # noqa

        self._scicat_client = FakeScicatClient(self)
        self.disabled = {} if disable is None else dict(disable)
        self.datasets: Dict[PID, Union[model.DerivedDataset, model.RawDataset]] = {}
        self.orig_datablocks: Dict[PID, List[model.OrigDatablock]] = {}

    @classmethod
    def from_token(
        cls, *, url: str, token: str, file_transfer: Optional[FileTransfer] = None
    ) -> FakeClient:
        """Create a new fake client.

        All arguments except ``file_Transfer`` are ignored.
        """
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
        """Create a new fake client.

        All arguments except ``file_Transfer`` are ignored.
        """
        return FakeClient(file_transfer=file_transfer)

    def get_dataset(self, pid: Union[PID, str]) -> Dataset:
        """Return a dataset from the client's internal storage."""
        return Dataset.from_models(
            dataset_model=self.scicat.get_dataset_model(str(pid)),
            orig_datablock_models=self.scicat.get_orig_datablocks(str(pid)),
        )

    @property
    def scicat(self) -> FakeScicatClient:
        """Client for lower level SciCat communication."""
        return self._scicat_client

    def download_file(self, *, remote: Union[str, Path], local: Union[str, Path]):
        """Download a file using the client's file_transfer."""
        if self.file_transfer is None:
            raise RuntimeError(
                f"No file transfer handler specified, cannot download file {remote}"
            )
        with self.file_transfer.connect_for_download() as con:
            con.download_file(remote=remote, local=local)

    def upload_file(
        self, *, dataset_id: PID, remote: Union[str, Path], local: Union[str, Path]
    ) -> str:
        """Upload a file using the client's file_transfer."""
        if self.file_transfer is None:
            raise RuntimeError(
                f"No file transfer handler specified, cannot upload file {local}"
            )
        with self.file_transfer.connect_for_upload(dataset_id) as con:
            return con.upload_file(remote=remote, local=local)


class FakeScicatClient(ScicatClient):
    """Mimics a ScicatClient, to be used by FakeClient."""

    def __init__(self, main_client):
        super().__init__(None)  # noqa
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
            pid=dset.pid if dset.pid is not None else str(uuid.uuid4()),
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
