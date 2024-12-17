# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 SciCat Project (https://github.com/SciCatProject/scitacean)
"""Fake client for testing."""

from __future__ import annotations

import datetime
import functools
import uuid
from collections.abc import Callable
from copy import deepcopy
from typing import Any

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
            :class:`dict` of lists of :class:`scitacean.model.DownloadOrigDatablock`,
            indexed by the *dataset* ID.
    - ``FakeClient.attachments``:
            :class:`dict` of lists of :class:`scitacean.model.DownloadAttachment`,
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
        file_transfer: FileTransfer | None = None,
        disable: dict[str, Exception] | None = None,
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
        self.datasets: dict[PID, model.DownloadDataset] = {}
        self.orig_datablocks: dict[PID, list[model.DownloadOrigDatablock]] = {}
        self.attachments: dict[PID, list[model.DownloadAttachment]] = {}
        self.samples: dict[str, model.DownloadSample] = {}

    @classmethod
    def from_token(
        cls,
        *,
        url: str,
        token: str | StrStorage,
        file_transfer: FileTransfer | None = None,
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
        username: str | StrStorage,
        password: str | StrStorage,
        file_transfer: FileTransfer | None = None,
    ) -> FakeClient:
        """Create a new fake client.

        All arguments except ``file_Transfer`` are ignored.
        """
        return FakeClient(file_transfer=file_transfer)

    @classmethod
    def without_login(
        cls, *, url: str, file_transfer: FileTransfer | None = None
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
        """Fetch a dataset from SciCat."""
        _ = strict_validation  # unused by fake
        try:
            return self.main.datasets[pid]
        except KeyError:
            raise ScicatCommError(f"Unable to retrieve dataset {pid}") from None

    @_conditionally_disabled
    def get_orig_datablocks(
        self, pid: PID, strict_validation: bool = False
    ) -> list[model.DownloadOrigDatablock]:
        """Fetch an orig datablock from SciCat."""
        _ = strict_validation  # unused by fake
        try:
            return self.main.orig_datablocks[pid]
        except KeyError:
            raise ScicatCommError(
                f"Unable to retrieve orig datablock for dataset {pid}"
            ) from None

    @_conditionally_disabled
    def get_attachments_for_dataset(
        self, pid: PID, strict_validation: bool = False
    ) -> list[model.DownloadAttachment]:
        """Fetch all attachments from SciCat for a given dataset."""
        _ = strict_validation  # unused by fake
        return self.main.attachments.get(pid) or []

    @_conditionally_disabled
    def get_sample_model(
        self, sample_id: str, strict_validation: bool = False
    ) -> model.DownloadSample:
        """Fetch a sample from SciCat."""
        _ = strict_validation  # unused by fake
        try:
            return self.main.samples[sample_id]
        except KeyError:
            raise ScicatCommError(f"Unable to retrieve sample {sample_id}") from None

    @_conditionally_disabled
    def create_dataset_model(
        self, dset: model.UploadDerivedDataset | model.UploadRawDataset
    ) -> model.DownloadDataset:
        """Create a new dataset in SciCat."""
        ingested = _process_dataset(dset)
        pid: PID = ingested.pid  # type: ignore[assignment]
        if pid in self.main.datasets:
            raise ScicatCommError(
                f"Cannot create dataset with pid '{pid}' "
                "because there already is a dataset with this pid."
            )
        self.main.datasets[pid] = ingested
        return ingested

    @_conditionally_disabled
    def create_orig_datablock(
        self, dblock: model.UploadOrigDatablock, *, dataset_id: PID
    ) -> model.DownloadOrigDatablock:
        """Create a new orig datablock in SciCat."""
        if (dset := self.main.datasets.get(dataset_id)) is None:
            raise ScicatCommError(f"No dataset with id {dataset_id}")
        ingested = _process_orig_datablock(dblock, dset)
        self.main.orig_datablocks.setdefault(dataset_id, []).append(ingested)
        return ingested

    @_conditionally_disabled
    def create_attachment_for_dataset(
        self,
        attachment: model.UploadAttachment,
        dataset_id: PID | None = None,
    ) -> model.DownloadAttachment:
        """Create a new attachment for a dataset in SciCat."""
        if dataset_id is None:
            dataset_id = attachment.datasetId
        if dataset_id is None:
            raise ValueError(
                "Cannot determine the dataset ID for attachment. "
                "Specify the ID as a function argument or in the attachment."
            )

        ingested = _process_attachment(attachment, dataset_id)
        if dataset_id not in self.main.datasets:
            raise ScicatCommError(f"No dataset with id {dataset_id}")
        self.main.attachments.setdefault(dataset_id, []).append(ingested)
        return ingested

    @_conditionally_disabled
    def create_sample_model(self, sample: model.UploadSample) -> model.DownloadSample:
        """Create a new sample in SciCat."""
        ingested = _process_sample(sample)
        if ingested.sampleId in self.main.samples:
            raise ScicatCommError(
                f"Cannot create sample with id '{ingested.sampleId}' "
                "because there already is a sample with this id."
            )
        sample_id: str = ingested.sampleId  # type: ignore[assignment]
        self.main.samples[sample_id] = ingested
        return ingested

    @_conditionally_disabled
    def validate_dataset_model(
        self, dset: model.UploadDerivedDataset | model.UploadRawDataset
    ) -> None:
        """Validate model remotely in SciCat."""
        # Models were locally validated on construction, assume they are valid.
        pass


def _model_dict(mod: model.BaseModel) -> dict[str, Any]:
    return {
        key: deepcopy(val)
        for key in mod.model_fields.keys()
        if (val := getattr(mod, key)) is not None
    }


def _process_relationship(
    relationship: model.UploadRelationship,
) -> model.DownloadRelationship:
    return model.DownloadRelationship(**_model_dict(relationship))


def _process_technique(technique: model.UploadTechnique) -> model.DownloadTechnique:
    return model.DownloadTechnique(**_model_dict(technique))


def _process_data_file(file: model.UploadDataFile) -> model.DownloadDataFile:
    return model.DownloadDataFile(**_model_dict(file))


def _process_dataset(
    dset: model.UploadDerivedDataset | model.UploadRawDataset,
) -> model.DownloadDataset:
    created_at = datetime.datetime.now(tz=datetime.timezone.utc)
    # TODO use user login if possible
    # Using strict_validation=False because the input model should already be validated.
    # If there are validation errors, it was probably intended by the user.
    fields = _model_dict(dset)
    if "relationships" in fields:
        fields["relationships"] = list(
            map(_process_relationship, fields["relationships"])
        )
    if "techniques" in fields:
        fields["techniques"] = list(map(_process_technique, fields["techniques"]))

    # TODO remove in API v4
    for singular in ("proposalId", "sampleId", "instrumentId"):
        if singular in fields:
            fields[singular + "s"] = [fields[singular]]
    fields.pop("investigator")

    return model.construct(
        model.DownloadDataset,
        _strict_validation=False,
        pid=PID.generate(prefix="PID.prefix.a0b1"),
        createdBy="fake",
        createdAt=created_at,
        updatedBy="fake",
        updatedAt=created_at,
        **fields,
    )


def _process_orig_datablock(
    dblock: model.UploadOrigDatablock,
    dset: model.DownloadDataset,
) -> model.DownloadOrigDatablock:
    created_at = datetime.datetime.now(tz=datetime.timezone.utc)
    # TODO use user login if possible
    # TODO more fields
    # Using strict_validation=False because the input model should already be validated.
    # If there are validation errors, it was probably intended by the user.
    fields = _model_dict(dblock)
    if "dataFileList" in fields:
        fields["dataFileList"] = list(map(_process_data_file, fields["dataFileList"]))
    fields["accessGroups"] = dset.accessGroups
    processed = model.construct(
        model.DownloadOrigDatablock,
        _strict_validation=False,
        createdBy="fake",
        createdAt=created_at,
        updatedBy="fake",
        updatedAt=created_at,
        datasetId=dset.pid,
        **fields,
    )
    return processed


def _process_attachment(
    attachment: model.UploadAttachment, dataset_id: PID | None = None
) -> model.DownloadAttachment:
    created_at = datetime.datetime.now(tz=datetime.timezone.utc)
    fields = _model_dict(attachment)
    if fields.get("id") is None:
        fields["id"] = str(uuid.uuid4())
    if dataset_id is not None:
        fields["datasetId"] = dataset_id
    # Using strict_validation=False because the input model should already be validated.
    # If there are validation errors, it was probably intended by the user.
    return model.construct(
        model.DownloadAttachment,
        _strict_validation=False,
        createdBy="fake",
        createdAt=created_at,
        updatedBy="fake",
        updatedAt=created_at,
        **fields,
    )


def _process_sample(sample: model.UploadSample) -> model.DownloadSample:
    created_at = datetime.datetime.now(tz=datetime.timezone.utc)
    fields = _model_dict(sample)
    if fields.get("sampleId") is None:
        fields["sampleId"] = str(uuid.uuid4())
    # Using strict_validation=False because the input model should already be validated.
    # If there are validation errors, it was probably intended by the user.
    return model.construct(
        model.DownloadSample,
        _strict_validation=False,
        createdBy="fake",
        createdAt=created_at,
        updatedBy="fake",
        updatedAt=created_at,
        **fields,
    )


def process_uploaded_dataset(
    dataset: model.UploadDerivedDataset | model.UploadRawDataset,
    orig_datablocks: list[model.UploadOrigDatablock] | None,
    attachments: list[model.UploadAttachment] | None,
) -> tuple[
    model.DownloadDataset,
    list[model.DownloadOrigDatablock] | None,
    list[model.DownloadAttachment] | None,
]:
    """Process a dataset as if it was uploaded to SciCat.

    This function attempts to mimic how SciCat converts uploaded dataset
    (and associated) models to the in-database (and download) models.
    It is not completely faithful to the real SciCat but only an approximation.
    """
    ds = _process_dataset(dataset)
    dblocks = (
        [_process_orig_datablock(db, ds) for db in orig_datablocks]
        if orig_datablocks is not None
        else None
    )
    atts = (
        list(map(_process_attachment, attachments)) if attachments is not None else None
    )
    return ds, dblocks, atts
