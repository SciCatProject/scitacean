# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 SciCat Project (https://github.com/SciCatProject/scitacean)
"""Fake client for testing."""

from __future__ import annotations

import datetime
import functools
from copy import deepcopy
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from .. import model
from ..client import Client, ScicatClient
from ..error import ScicatCommError
from ..pid import PID
from ..typing import FileTransfer
from ..util.credentials import StrStorage


def _conditionally_disabled(func: Callable[..., Any]) -> Callable[..., Any]:
    @functools.wraps(func)
    def impl(self, *args, **kwargs):  # type: ignore[no-untyped-def]
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
    `pydantic <https://docs.pydantic.dev/>`_ models, namely

    - ``FakeClient.datasets``:
            :class:`dict` of :class:`scitacean.model.DownloadDataset`,
            indexed by dataset PID.
    - ``FakeClient.orig_datablocks``:
            :class:`dict` of lists of :class:`scitacean.model.OrigDatablock`,
            indexed by the *dataset* ID.

    Individual functions can be disabled (that is, made to raise an exception)
    using the ``disabled`` argument of the initializer.

    Important
    ---------
    ``FakeClient`` does not behave exactly like a ``Client`` connected to a real
    server as that would require reimplementing a large part of the SciCat backend.
    You should thus always also test your code against a (potentially locally deployed)
    real server.

    In particular, do not rely on specific error messages or the detailed settings
    in the datasets returned by ``FakeClient.upload_new_dataset_now``!

    Examples
    --------
    Set up a fake client for download:

    .. code-block:: python

        client = FakeClient()
        pid = PID(prefix="sample.prefix", pid="1234-5678-abcd")
        client.datasets[pid] = model.DownloadDataset(pid=pid, ...)
        client.orig_datablocks[pid] = [model.OrigDatablock(
            datasetId=str(pid),
            ...
        )]
        client.get_dataset(pid)

    Upload a dataset:

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
    ) -> None:
        """Initialize a fake client with empty dataset storage.

        Parameters
        ----------
        file_transfer:
            Typically :class:`scitacean.testing.transfer.FakeFileTransfer`
            but may be a real file transfer.
        disable:
            ``dict`` of function names to exceptions.
            Functions listed here raise the given exception
            when called and do nothing else.
        """
        super().__init__(client=FakeScicatClient(self), file_transfer=file_transfer)

        self.disabled = {} if disable is None else dict(disable)
        self.datasets: Dict[PID, model.DownloadDataset] = {}
        self.orig_datablocks: Dict[PID, List[model.OrigDatablock]] = {}

    @classmethod
    def from_token(
        cls,
        *,
        url: str,
        token: Union[str, StrStorage],
        file_transfer: Optional[FileTransfer] = None,
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
        username: Union[str, StrStorage],
        password: Union[str, StrStorage],
        file_transfer: Optional[FileTransfer] = None,
    ) -> FakeClient:
        """Create a new fake client.

        All arguments except ``file_Transfer`` are ignored.
        """
        return FakeClient(file_transfer=file_transfer)

    @classmethod
    def without_login(
        cls, *, url: str, file_transfer: Optional[FileTransfer] = None
    ) -> FakeClient:
        """Create a new fake client.

        All arguments except ``file_Transfer`` are ignored.
        """
        return FakeClient(file_transfer=file_transfer)


class FakeScicatClient(ScicatClient):
    """Mimics a ScicatClient, to be used by FakeClient."""

    def __init__(self, main_client: FakeClient) -> None:
        super().__init__(url="", token="", timeout=datetime.timedelta(seconds=60))
        self.main = main_client

    @_conditionally_disabled
    def get_dataset_model(
        self, pid: PID, strict_validation: bool = False
    ) -> model.DownloadDataset:
        _ = strict_validation  # unused by fake
        try:
            return self.main.datasets[pid]
        except KeyError:
            raise ScicatCommError(f"Unable to retrieve dataset {pid}") from None

    @_conditionally_disabled
    def get_orig_datablocks(
        self, pid: PID, strict_validation: bool = False
    ) -> List[model.OrigDatablock]:  # TODO here and rest of classes
        _ = strict_validation  # unused by fake
        try:
            return self.main.orig_datablocks[pid]
        except KeyError:
            raise ScicatCommError(
                f"Unable to retrieve orig datablock for dataset {pid}"
            ) from None

    @_conditionally_disabled
    def create_dataset_model(
        self, dset: Union[model.UploadDerivedDataset, model.UploadRawDataset]
    ) -> model.DownloadDataset:
        ingested = _process_dataset(dset)
        self.main.datasets[ingested.pid] = ingested
        return ingested

    @_conditionally_disabled
    def create_orig_datablock(
        self, dblock: model.UploadOrigDatablock
    ) -> model.DownloadOrigDatablock:
        dataset_id = dblock.datasetId
        if dataset_id not in self.main.datasets:
            raise ScicatCommError(f"No dataset with id {dataset_id}")
        self.main.orig_datablocks.setdefault(dataset_id, []).append(dblock)
        return dblock


def _process_dataset(
    dset: Union[model.UploadDerivedDataset, model.UploadRawDataset]
) -> model.DownloadDataset:
    return model.DownloadDataset(
        pid=PID.generate(prefix="PID.SAMPLE.PREFIX"),
        createdBy="fake",
        createdAt=datetime.datetime.now(tz=datetime.timezone.utc),
        **deepcopy(dset).dict(exclude_none=True),
    )


def _process_orig_datablock(
    dblock: model.UploadOrigDatablock,
) -> model.DownloadOrigDatablock:
    return model.DownloadOrigDatablock(
        datasetId=dblock.datasetId,
        createdBy="fake",
        createdAt=datetime.datetime.now(tz=datetime.timezone.utc),
        **deepcopy(dblock).dict(exclude_none=True),
    )


def process_uploaded_dataset(
    dataset: Union[model.UploadDerivedDataset, model.UploadRawDataset],
    orig_datablocks: Optional[List[model.UploadOrigDatablock]],
) -> Tuple[model.DownloadDataset, Optional[List[model.DownloadOrigDatablock]]]:
    dblocks = (
        list(map(_process_orig_datablock, orig_datablocks))
        if orig_datablocks is not None
        else None
    )
    return _process_dataset(dataset), dblocks
