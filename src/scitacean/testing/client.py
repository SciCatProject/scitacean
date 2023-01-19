# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 SciCat Project (https://github.com/SciCatProject/scitacean)
"""Fake client for testing."""

from __future__ import annotations

import functools
import uuid
from copy import deepcopy
from typing import Any, Callable, Dict, List, Optional, Union

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
        client.datasets[pid] = model.DerivedDataset(...)
        client.orig_datablocks[pid] = [model.OrigDatablock(
            datasetId=str(pid),
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
    ) -> None:
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
        super().__init__(client=FakeScicatClient(self), file_transfer=file_transfer)

        self.disabled = {} if disable is None else dict(disable)
        self.datasets: Dict[PID, Union[model.DerivedDataset, model.RawDataset]] = {}
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
        super().__init__(url="", token="")  # noqa: S106
        self.main = main_client

    @_conditionally_disabled
    def get_dataset_model(
        self, pid: PID, strict_validation: bool = False
    ) -> Union[model.DerivedDataset, model.RawDataset]:
        _ = strict_validation  # unused by fake
        try:
            return self.main.datasets[pid]
        except KeyError:
            raise ScicatCommError(f"Unable to retrieve dataset {pid}") from None

    @_conditionally_disabled
    def get_orig_datablocks(
        self, pid: PID, strict_validation: bool = False
    ) -> List[model.OrigDatablock]:
        _ = strict_validation  # unused by fake
        try:
            return self.main.orig_datablocks[pid]
        except KeyError:
            raise ScicatCommError(
                f"Unable to retrieve orig datablock for dataset {pid}"
            ) from None

    @_conditionally_disabled
    def create_dataset_model(
        self, dset: Union[model.DerivedDataset, model.RawDataset]
    ) -> Union[model.DerivedDataset, model.RawDataset]:
        pid = PID(
            pid=str(dset.pid) if dset.pid is not None else str(uuid.uuid4()),
            prefix="PID.SAMPLE.PREFIX",
        )
        if pid in self.main.datasets:
            raise ScicatCommError(f"Dataset id already exists: {pid}")
        self.main.datasets[pid] = deepcopy(dset)
        self.main.datasets[pid].pid = pid
        return self.main.datasets[pid]

    @_conditionally_disabled
    def create_orig_datablock(self, dblock: model.OrigDatablock) -> model.OrigDatablock:
        dataset_id = dblock.datasetId
        if dataset_id not in self.main.datasets:
            raise ScicatCommError(f"No dataset with id {dataset_id}")
        self.main.orig_datablocks.setdefault(dataset_id, []).append(dblock)
        return dblock
