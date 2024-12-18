# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 SciCat Project (https://github.com/SciCatProject/scitacean)
"""Client to handle communication with SciCat servers."""

from __future__ import annotations

import dataclasses
import datetime
import json
import re
import warnings
from collections import Counter
from collections.abc import Callable, Iterable, Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus

import httpx
import pydantic

from . import model
from ._base_model import convert_download_to_user_model
from .dataset import Dataset
from .error import ScicatCommError, ScicatLoginError
from .file import File
from .filesystem import RemotePath
from .logging import get_logger
from .pid import PID
from .typing import DownloadConnection, FileTransfer, UploadConnection
from .util.credentials import ExpiringToken, SecretStr, StrStorage


class Client:
    """SciCat client to communicate with a server.

    Clients hold all information needed to communicate with a SciCat instance
    and a filesystem that holds data files (via ``file_transfer``).

    Use :func:`Client.from_token` or :func:`Client.from_credentials` to initialize
    a client instead of the constructor directly.

    See the user guide for typical usage patterns.
    In particular, `Downloading Datasets <../../user-guide/downloading.ipynb>`_
    and `Uploading Datasets <../../user-guide/uploading.ipynb>`_.
    """

    def __init__(
        self,
        *,
        client: ScicatClient,
        file_transfer: FileTransfer | None,
    ):
        """Initialize a client.

        Do not use directly, instead use :func:`Client.from_token`
        or :func:`Client.from_credentials`!
        """
        self._client = client
        self._file_transfer = file_transfer

    @classmethod
    def from_token(
        cls,
        *,
        url: str,
        token: str | StrStorage,
        file_transfer: FileTransfer | None = None,
    ) -> Client:
        """Create a new client and authenticate with a token.

        Parameters
        ----------
        url:
            URL of the SciCat api.
        token:
            User token to authenticate with SciCat.
        file_transfer:
            Handler for down-/uploads of files.

        Returns
        -------
        :
            A new client.
        """
        return Client(
            client=ScicatClient.from_token(url=url, token=token),
            file_transfer=file_transfer,
        )

    # TODO rename to login? and provide logout?
    @classmethod
    def from_credentials(
        cls,
        *,
        url: str,
        username: str | StrStorage,
        password: str | StrStorage,
        file_transfer: FileTransfer | None = None,
    ) -> Client:
        """Create a new client and authenticate with username and password.

        Parameters
        ----------
        url:
            URL of the SciCat api.
            It should include the suffix `api/vn` where `n` is a number.
        username:
            Name of the user.
        password:
            Password of the user.
        file_transfer:
            Handler for down-/uploads of files.

        Returns
        -------
        :
            A new client.
        """
        return Client(
            client=ScicatClient.from_credentials(
                url=url, username=username, password=password
            ),
            file_transfer=file_transfer,
        )

    @classmethod
    def without_login(
        cls, *, url: str, file_transfer: FileTransfer | None = None
    ) -> Client:
        """Create a new client without authentication.

        The client can only download public datasets and not upload at all.

        Parameters
        ----------
        url:
            URL of the SciCat api.
            It should include the suffix `api/vn` where `n` is a number.
        file_transfer:
            Handler for down-/uploads of files.

        Returns
        -------
        :
            A new client.
        """
        return Client(
            client=ScicatClient.without_login(url=url), file_transfer=file_transfer
        )

    @property
    def scicat(self) -> ScicatClient:
        """Low-level client for SciCat.

        Should typically not be used by users of Scitacean!
        """
        return self._client

    @property
    def file_transfer(self) -> FileTransfer | None:
        """Stored handler for file down-/uploads."""
        return self._file_transfer

    def get_dataset(
        self,
        pid: str | PID,
        strict_validation: bool = False,
        attachments: bool = False,
    ) -> Dataset:
        """Download a dataset from SciCat.

        Does not download any files.

        Parameters
        ----------
        pid:
            ID of the dataset. Must include the prefix, i.e. have the form
            ``prefix/dataset-id``.
        strict_validation:
            If ``True``, the dataset must pass validation.
            If ``False``, a dataset is still returned if validation fails.
            Note that some dataset fields may have a bad value or type.
            A warning will be logged if validation fails.
        attachments:
            Select whether to download attachments.
            If this is ``False``, the attachments of the returned dataset are ``None``.
            They can be downloaded later using :meth:`Client.download_attachments_for`.

        Returns
        -------
        :
            A new dataset.
        """
        pid = PID.parse(pid)
        dataset = self.scicat.get_dataset_model(
            pid, strict_validation=strict_validation
        )

        try:
            orig_datablocks = self.scicat.get_orig_datablocks(
                pid, strict_validation=strict_validation
            )
        except ScicatCommError:
            # TODO more precise error handling. We only want to set to None if
            #   communication succeeded and the dataset exists but there simply
            #   are no datablocks.
            orig_datablocks = None

        attachment_models = (
            self.scicat.get_attachments_for_dataset(pid) if attachments else None
        )

        return Dataset.from_download_models(
            dataset_model=dataset,
            orig_datablock_models=orig_datablocks or [],
            attachment_models=attachment_models,
        )

    def get_sample(
        self,
        sample_id: str,
        strict_validation: bool = False,
    ) -> model.Sample:
        """Download a sample from SciCat.

        Parameters
        ----------
        sample_id:
            ID of the sample.
        strict_validation:
            If ``True``, the sample must pass validation.
            If ``False``, a sample is still returned if validation fails.
            Note that some sample fields may have a bad value or type.
            A warning will be logged if validation fails.

        Returns
        -------
        :
            The downloaded sample.
        """
        sample_model = self.scicat.get_sample_model(
            sample_id, strict_validation=strict_validation
        )
        return model.Sample.from_download_model(sample_model)

    def upload_new_dataset_now(self, dataset: Dataset) -> Dataset:
        """Upload a dataset as a new entry to SciCat immediately.

        The dataset is inserted as a new entry in the database and will
        never overwrite existing data.

        Attachments are also uploaded automatically.
        This happens after the upload of files and the dataset itself.
        So if uploading the attachments fails, check the dataset in SciCat to
        determine which attachments you need to re-upload
        (using :meth:`ScicatClient.create_attachment_for_dataset`).

        Parameters
        ----------
        dataset:
            The dataset to upload.

        Returns
        -------
        :
            A copy of the input dataset with fields adjusted
            according to the response of the server.

        Raises
        ------
        scitacean.ScicatCommError
            If the upload to SciCat fails.
        RuntimeError
            If the file upload fails or if a critical error is encountered
            and some files or a partial dataset are left on the servers.
            Note the error message if that happens.
        """
        dataset = dataset.replace(source_folder=self._source_folder_for(dataset))
        files_to_upload = _files_to_upload(dataset.files)
        self.scicat.validate_dataset_model(dataset.make_upload_model())
        with self._connect_for_file_upload(dataset, files_to_upload) as con:
            # TODO check if any remote file is out of date.
            #  if so, raise an error. We never overwrite remote files!
            uploaded_files = con.upload_files(*files_to_upload)
            dataset = dataset.replace_files(*uploaded_files)
            try:
                finalized_model = self.scicat.create_dataset_model(
                    dataset.make_upload_model()
                )
            except ScicatCommError:
                con.revert_upload(*uploaded_files)
                raise

        with_new_pid = dataset.replace(_read_only={"pid": finalized_model.pid})
        finalized_orig_datablocks = self._upload_orig_datablocks(
            with_new_pid.make_datablock_upload_models().orig_datablocks,
            with_new_pid.pid,  # type: ignore[arg-type]
        )
        finalized_attachments = self._upload_attachments_for_dataset(
            with_new_pid.make_attachment_upload_models(),
            dataset_id=with_new_pid.pid,  # type: ignore[arg-type]
        )

        return Dataset.from_download_models(
            dataset_model=finalized_model,
            orig_datablock_models=finalized_orig_datablocks,
            attachment_models=finalized_attachments,
        )

    def upload_new_sample_now(self, sample: model.Sample) -> model.Sample:
        """Upload a sample as a new entry to SciCat immediately.

        The sample is inserted as a new entry in the database and will
        never overwrite existing data.
        To this end, the input sample's ID is ignored and a new one is
        assigned automatically.

        Parameters
        ----------
        sample:
            The sample to upload.

        Returns
        -------
        :
            A copy of the input sample with fields adjusted
            according to the response of the server.

        Raises
        ------
        scitacean.ScicatCommError
            If the upload to SciCat fails.
        """
        sample = dataclasses.replace(sample, sample_id=None)
        finalized_model = self.scicat.create_sample_model(sample.make_upload_model())
        return model.Sample.from_download_model(finalized_model)

    def _upload_orig_datablocks(
        self,
        orig_datablocks: list[model.UploadOrigDatablock] | None,
        dataset_id: PID,
    ) -> list[model.DownloadOrigDatablock]:
        if not orig_datablocks:
            return []

        try:
            return [
                self.scicat.create_orig_datablock(orig_datablock, dataset_id=dataset_id)
                for orig_datablock in orig_datablocks
            ]
        except ScicatCommError as exc:
            raise RuntimeError(
                "Failed to upload original datablocks for SciCat dataset "
                f"{dataset_id}:"
                f"\n{exc.args}\nThe dataset and data files were successfully uploaded "
                "but are not linked with each other. Please fix the dataset manually!"
            ) from exc

    def _upload_attachments_for_dataset(
        self, attachments: list[model.UploadAttachment], *, dataset_id: PID
    ) -> list[model.DownloadAttachment]:
        try:
            return [
                self.scicat.create_attachment_for_dataset(
                    attachment, dataset_id=dataset_id
                )
                for attachment in attachments
            ]
        except ScicatCommError as exc:
            raise RuntimeError(
                f"Failed to upload attachments for SciCat dataset {dataset_id}:"
                f"\n{exc.args}\nThe dataset and data files were successfully uploaded "
                "and will not be reverted. Please upload the attachments manually!"
            ) from exc

    @contextmanager
    def _connect_for_file_upload(
        self, dataset: Dataset, files_to_upload: Iterable[File]
    ) -> Iterator[UploadConnection]:
        if not files_to_upload:
            yield _NullUploadConnection()
        else:
            with self._expect_file_transfer().connect_for_upload(dataset) as con:
                yield con

    def _source_folder_for(self, dataset: Dataset) -> RemotePath:
        if self._file_transfer is not None:
            return self._file_transfer.source_folder_for(dataset)
        if dataset.source_folder is None:
            raise ValueError(
                "Cannot determine source_folder for dataset because "
                "the dataset's source_folder is None and there is no file transfer."
            )
        return dataset.source_folder

    def _expect_file_transfer(self) -> FileTransfer:
        if self.file_transfer is None:
            raise ValueError(
                "Cannot upload/download files because no file transfer is set. "
                "Specify one when constructing a client."
            )
        return self.file_transfer

    def download_files(
        self,
        dataset: Dataset,
        *,
        target: str | Path,
        select: FileSelector = True,
        checksum_algorithm: str | None = None,
        force: bool = False,
    ) -> Dataset:
        r"""Download files of a dataset.

        Makes selected files available on the local filesystem using the file transfer
        object stored in the client.
        All files are downloaded to the ``target`` directory.
        Any directory structure on the remote system is discarded, that is all files
        are placed directly in ``target``.

        Parameters
        ----------
        dataset:
            Download files of this dataset.
        target:
            Files are stored to this path on the local filesystem.
        select:
            A file ``f`` is downloaded if ``select`` is

            - **True**: downloaded
            - **False**: not downloaded
            - A **string**: if ``f.remote_path`` equals this string
            - A **list[str]** or **tuple[str]**: if ``f.remote_path``
              equals any of these strings
            - An **re.Pattern** as returned by :func:`re.compile`:
              if this pattern matches ``f.remote_path`` using :func:`re.search`
            - A **Callable[File]**: if this callable returns ``True`` for ``f``
        checksum_algorithm:
            Select an algorithm for computing file checksums.
            The data block normally determines the algorithm, but this argument can
            override the stored value if the data block is broken
            or no algorithm has been set.
        force:
            If ``True``, download files regardless of whether they already exist
            locally.
            This bypasses the checksum computation of pre-existing local files.

        Returns
        -------
        :
            A copy of the input dataset with files replaced to reflect the downloads.
            That is, the ``local_path`` of all downloaded files is set.

        Examples
        --------
        Download all files

        .. code-block:: python

            client.download_files(dataset, target="./data", select=True)

        Download a specific file

        .. code-block:: python

            client.download_files(dataset, target="./data", select="my-file.dat")

        Download all files with a ``nxs`` extension

        .. code-block:: python

            import re
            client.download_files(
                dataset,
                target="./data",
                select=re.compile(r"\.nxs$")
            )
            # or
            client.download_files(
                dataset,
                target="./data",
                select=lambda file: file.remote_path.suffix == ".nxs"
            )
        """
        if dataset.source_folder is None:
            raise ValueError("Dataset has no source folder, cannot download files.")
        target = Path(target)
        # TODO undo if later fails but only if no files were written
        target.mkdir(parents=True, exist_ok=True)
        files = _select_files(select, dataset)
        downloaded_files = [
            f.downloaded(local_path=target / f.remote_path.to_local()) for f in files
        ]
        _expect_no_duplicate_filenames(f.local_path for f in downloaded_files)
        if not force:
            to_download = _remove_up_to_date_local_files(
                downloaded_files, checksum_algorithm=checksum_algorithm
            )
        else:
            to_download = downloaded_files

        if not to_download:
            return dataset.replace_files(*downloaded_files)

        with self._connect_for_file_download() as con:
            con.download_files(
                remote=[
                    p
                    for f in to_download
                    if (p := f.remote_access_path(dataset.source_folder)) is not None
                ],
                local=[f.local_path for f in to_download],  # type: ignore[misc]
            )
        for f in to_download:
            f.validate_after_download()
        return dataset.replace_files(*downloaded_files)

    @contextmanager
    def _connect_for_file_download(self) -> Iterator[DownloadConnection]:
        if self.file_transfer is None:
            raise ValueError(
                "Cannot download files because no file transfer is set. "
                "Specify one when constructing a client."
            )
        with self.file_transfer.connect_for_download() as con:
            yield con

    def download_attachments_for(self, target: Dataset) -> Dataset:
        """Download all attachments for a given object.

        The target object must have an ID, that is, it must represent an entry
        in SciCat and not just a locally created object.

        If the input already has attachments, they will be overwritten and a
        ``UserWarning`` will be raised.

        Parameters
        ----------
        target:
            Download attachments for this object.

        Returns
        -------
        :
            A copy of the input dataset with attachments replaced
            with the downloaded models.
        """
        if target.pid is None:
            raise ValueError(
                "Cannot download attachments because the dataset has no PID."
            )
        if target.attachments is not None:
            warnings.warn(
                "Downloading attachments for a dataset that already has "
                "attachments. The existing attachments will be overwritten.",
                stacklevel=2,
            )
        return target.replace(
            attachments=convert_download_to_user_model(
                self.scicat.get_attachments_for_dataset(target.pid)
            )
        )


class ScicatClient:
    """Low-level client to call the SciCat API."""

    def __init__(
        self,
        url: str,
        token: str | StrStorage | None,
        timeout: datetime.timedelta | None,
    ):
        # Need to add a final /
        self._base_url = url[:-1] if url.endswith("/") else url
        self._timeout = datetime.timedelta(seconds=10) if timeout is None else timeout
        self._token: StrStorage | None = (
            ExpiringToken.from_jwt(SecretStr(token))
            if isinstance(token, str)
            else token
        )

    @classmethod
    def from_token(
        cls,
        url: str,
        token: str | StrStorage,
        timeout: datetime.timedelta | None = None,
    ) -> ScicatClient:
        """Create a new low-level client and authenticate with a token.

        Parameters
        ----------
        url:
            URL of the SciCat api.
        token:
            User token to authenticate with SciCat.
        timeout:
            Timeout for all API requests.

        Returns
        -------
        :
            A new low-level client.
        """
        return ScicatClient(url=url, token=token, timeout=timeout)

    @classmethod
    def from_credentials(
        cls,
        url: str,
        username: str | StrStorage,
        password: str | StrStorage,
        timeout: datetime.timedelta | None = None,
    ) -> ScicatClient:
        """Create a new low-level client and authenticate with username and password.

        Parameters
        ----------
        url:
            URL of the SciCat api.
            It should include the suffix `api/vn` where `n` is a number.
        username:
            Name of the user.
        password:
            Password of the user.
        timeout:
            Timeout for all API requests.

        Returns
        -------
        :
            A new low-level client.
        """
        if not isinstance(username, StrStorage):
            username = SecretStr(username)
        if not isinstance(password, StrStorage):
            password = SecretStr(password)
        return ScicatClient(
            url=url,
            token=SecretStr(
                _get_token(
                    url=url,
                    username=username,
                    password=password,
                    timeout=timeout if timeout else datetime.timedelta(seconds=10),
                )
            ),
            timeout=timeout,
        )

    @classmethod
    def without_login(
        cls, url: str, timeout: datetime.timedelta | None = None
    ) -> ScicatClient:
        """Create a new low-level client without authentication.

        The client can only download public datasets and not upload at all.

        Parameters
        ----------
        url:
            URL of the SciCat api.
            It should include the suffix `api/vn` where `n` is a number.
        timeout:
            Timeout for all API requests.

        Returns
        -------
        :
            A new low-level client.
        """
        return ScicatClient(url=url, token=None, timeout=timeout)

    def get_dataset_model(
        self, pid: PID, strict_validation: bool = False
    ) -> model.DownloadDataset:
        """Fetch a dataset from SciCat.

        Parameters
        ----------
        pid:
            Unique ID of the dataset.
            Must include the facility ID.
        strict_validation:
            If ``True``, the dataset must pass validation.
            If ``False``, a dataset is still returned if validation fails.
            Note that some dataset fields may have a bad value or type.
            A warning will be logged if validation fails.

        Returns
        -------
        :
            A model of the dataset.

        Raises
        ------
        scitacean.ScicatCommError
            If the dataset does not exist or communication fails for some other reason.
        """
        dset_json = self._call_endpoint(
            cmd="get",
            url=f"datasets/{quote_plus(str(pid))}",
            operation="get_dataset_model",
        )
        if not dset_json:
            raise ScicatCommError(
                f"Cannot get dataset with {pid=}, "
                f"no such dataset in SciCat at {self._base_url}."
            )
        return model.construct(
            model.DownloadDataset,
            _strict_validation=strict_validation,
            **dset_json,
        )

    def query_datasets(
        self,
        fields: dict[str, Any],
        *,
        limit: int | None = None,
        order: str | None = None,
        strict_validation: bool = False,
    ) -> list[model.DownloadDataset]:
        """Query for datasets in SciCat.

        Attention
        ---------
        This function is experimental and may change or be removed in the future.
        It is currently unclear how best to implement querying because SciCat
        provides multiple, very different APIs and there are plans for supporting
        queries via Mongo query language directly.

        See `issue #177 <https://github.com/SciCatProject/scitacean/issues/177>`_
        for a discussion.

        Parameters
        ----------
        fields:
            Fields to query for.
            Returned datasets must match all fields exactly.
            See examples below.
        limit:
            Maximum number of results to return.
            Requires ``order`` to be specified.
            If not given, all matching datasets are returned.
        order:
            Specify order of results.
            For example, ``"creationTime:asc"`` and ``"creationTime:desc"`` return
            results in ascending or descending order in creation time, respectively.
        strict_validation:
            If ``True``, the datasets must pass validation.
            If ``False``, datasets are still returned if validation fails.
            Note that some dataset fields may have a bad value or type.
            A warning will be logged if validation fails.

        Returns
        -------
        :
            A list of dataset models that match the query.

        Examples
        --------
        Get all datasets belonging to proposal ``abc.123``:

        .. code-block:: python

            scicat_client.query_datasets({'proposalIds': ['abc.123']})

        Get all datasets that belong to proposal ``abc.123``
        **and** have name ``"ds name"``: (The name and proposal must match exactly.)

        .. code-block:: python

            scicat_client.query_datasets({
                'proposalIds': ['abc.123'],
                'datasetName': 'ds name'
            })

        Return only the newest 5 datasets for proposal ``bc.123``:

        .. code-block:: python

            scicat_client.query_datasets(
                {'proposalIds': ['bc.123']},
                limit=5,
                order="creationTime:desc",
            )
        """
        # Use a pydantic model to support serializing custom types to JSON.
        params_model = pydantic.create_model(  # type: ignore[call-overload]
            "QueryParams", **{key: (type(field), ...) for key, field in fields.items()}
        )
        params = {"fields": params_model(**fields).model_dump_json()}

        limits: dict[str, str | int] = {}
        if order is not None:
            limits["order"] = order
        if limit is not None:
            if order is None:
                raise ValueError("`order` is required when `limit` is specified.")
            limits["limit"] = limit
        if limits:
            params["limits"] = json.dumps(limits)

        dsets_json = self._call_endpoint(
            cmd="get",
            url="datasets/fullquery",
            params=params,
            operation="query_datasets",
        )
        if not dsets_json:
            return []
        return [
            model.construct(
                model.DownloadDataset,
                _strict_validation=strict_validation,
                **dset_json,
            )
            for dset_json in dsets_json
        ]

    def get_orig_datablocks(
        self, pid: PID, strict_validation: bool = False
    ) -> list[model.DownloadOrigDatablock]:
        """Fetch all orig datablocks from SciCat for a given dataset.

        Parameters
        ----------
        pid:
            Unique ID of the *dataset*.
            Must include the facility ID.
        strict_validation:
            If ``True``, the datablocks must pass validation.
            If ``False``, datablocks are still returned if validation fails.
            Note that some fields may have a bad value or type.
            A warning will be logged if validation fails.

        Returns
        -------
        :
            Models of the orig datablocks.

        Raises
        ------
        scitacean.ScicatCommError
            If communication fails.
        """
        dblock_json = self._call_endpoint(
            cmd="get",
            url=f"datasets/{quote_plus(str(pid))}/origdatablocks",
            operation="get_orig_datablocks",
        )
        return [
            _make_orig_datablock(dblock, strict_validation=strict_validation)
            for dblock in dblock_json
        ]

    def get_attachments_for_dataset(
        self, pid: PID, strict_validation: bool = False
    ) -> list[model.DownloadAttachment]:
        """Fetch all attachments from SciCat for a given dataset.

        Parameters
        ----------
        pid:
            Unique ID of the *dataset*.
            Must include the facility ID.
        strict_validation:
            If ``True``, the attachments must pass validation.
            If ``False``, attachments are still returned if validation fails.
            Note that some fields may have a bad value or type.
            A warning will be logged if validation fails.

        Returns
        -------
        :
            Models of the attachments.

        Raises
        ------
        scitacean.ScicatCommError
            If communication fails.
        """
        attachment_json = self._call_endpoint(
            cmd="get",
            url=f"datasets/{quote_plus(str(pid))}/attachments",
            operation="get_attachments_for_dataset",
        )
        return [
            model.construct(
                model.DownloadAttachment,
                _strict_validation=strict_validation,
                **attachment,
            )
            for attachment in attachment_json
        ]

    def get_sample_model(
        self, sample_id: str, strict_validation: bool = False
    ) -> model.DownloadSample:
        """Fetch a sample from SciCat.

        Parameters
        ----------
        sample_id:
            ID of the sample to fetch.
        strict_validation:
            If ``True``, the sample must pass validation.
            If ``False``, a sample is still returned if validation fails.
            Note that some fields may have a bad value or type.
            A warning will be logged if validation fails.

        Returns
        -------
        :
            A model of the sample.

        Raises
        ------
        scitacean.ScicatCommError
            If the sample does not exist or communication fails for some other reason.
        """
        sample_json = self._call_endpoint(
            cmd="get",
            url=f"samples/{quote_plus(sample_id)}",
            operation="get_sample_model",
        )
        if not sample_json:
            raise ScicatCommError(
                f"Cannot get sample with {sample_id=}, "
                f"no such sample in SciCat at {self._base_url}."
            )
        return model.construct(
            model.DownloadSample,
            _strict_validation=strict_validation,
            **sample_json,
        )

    def create_dataset_model(
        self, dset: model.UploadDerivedDataset | model.UploadRawDataset
    ) -> model.DownloadDataset:
        """Create a new dataset in SciCat.

        The dataset PID must be either

        - ``None``, in which case SciCat assigns an ID,
        - an unused id, in which case SciCat uses it for the new dataset.

        If the ID already exists, creation will fail without
        modification to the database.
        Unless the new dataset is identical to the existing one,
        in which case, nothing happens.

        Parameters
        ----------
        dset:
            Model of the dataset to create.

        Returns
        -------
        :
            The uploaded dataset as returned by SciCat.
            This is the input plus some modifications.

        Raises
        ------
        scitacean.ScicatCommError
            If SciCat refuses the dataset or communication
            fails for some other reason.
        """
        uploaded = self._call_endpoint(
            cmd="post", url="datasets", data=dset, operation="create_dataset_model"
        )
        return model.construct(
            model.DownloadDataset, _strict_validation=False, **uploaded
        )

    def create_orig_datablock(
        self,
        dblock: model.UploadOrigDatablock,
        *,
        dataset_id: PID,
    ) -> model.DownloadOrigDatablock:
        """Create a new orig datablock in SciCat.

        The datablock PID must be either

        - ``None``, in which case SciCat assigns an ID.
        - An unused id, in which case SciCat uses it for the new datablock.

        If the ID already exists, creation will fail without
        modification to the database.

        Parameters
        ----------
        dblock:
            Model of the orig datablock to create.
        dataset_id:
            PID of the dataset that this datablock belongs to.

        Raises
        ------
        scitacean.ScicatCommError
            If SciCat refuses the datablock or communication
            fails for some other reason.
        """
        uploaded = self._call_endpoint(
            cmd="post",
            url=f"datasets/{quote_plus(str(dataset_id))}/origdatablocks",
            data=dblock,
            operation="create_orig_datablock",
        )
        return model.construct(
            model.DownloadOrigDatablock, _strict_validation=False, **uploaded
        )

    def create_attachment_for_dataset(
        self,
        attachment: model.UploadAttachment,
        *,
        dataset_id: PID,
    ) -> model.DownloadAttachment:
        """Create a new attachment for a dataset in SciCat.

        The attachment ID must be either

        - ``None``, in which case SciCat assigns an ID.
        - An unused id, in which case SciCat uses it for the new attachment.

        If the ID already exists, creation will fail without
        modification to the database.

        Parameters
        ----------
        attachment:
            Model of the attachment to create.
        dataset_id:
            ID of the dataset to which the attachment belongs.

        Raises
        ------
        scitacean.ScicatCommError
            If SciCat refuses the attachment or communication
            fails for some other reason.
        """
        uploaded = self._call_endpoint(
            cmd="post",
            url=f"datasets/{quote_plus(str(dataset_id))}/attachments",
            data=attachment,
            operation="create_attachment",
        )
        if not uploaded:
            raise ScicatCommError(
                f"Failed to upload attachment for dataset with pid={dataset_id}. "
                "The server reported success but did not return a finalized attachment."
                " This likely means that there is no dataset with this ID."
            )
        return model.construct(
            model.DownloadAttachment, _strict_validation=False, **uploaded
        )

    def create_sample_model(self, sample: model.UploadSample) -> model.DownloadSample:
        """Create a new sample in SciCat.

        The sample ID must be either

        - ``None``, in which case SciCat assigns an ID,
        - an unused id, in which case SciCat uses it for the new sample.

        If the ID already exists, creation will fail without
        modification to the database.
        Unless the new sample is identical to the existing one,
        in which case, nothing happens.

        Parameters
        ----------
        sample:
            Model of the sample to create.

        Returns
        -------
        :
            The uploaded sample as returned by SciCat.
            This is the input plus some modifications.

        Raises
        ------
        scitacean.ScicatCommError
            If SciCat refuses the sample or communication
            fails for some other reason.
        """
        uploaded = self._call_endpoint(
            cmd="post", url="samples", data=sample, operation="create_sample_model"
        )
        return model.construct(
            model.DownloadSample, _strict_validation=False, **uploaded
        )

    def validate_dataset_model(
        self, dset: model.UploadDerivedDataset | model.UploadRawDataset
    ) -> None:
        """Validate a dataset in SciCat.

        Parameters
        ----------
        dset:
            Model of the dataset to validate.

        Raises
        ------
        ValueError
            If the dataset does not pass validation.
        """
        response = self._call_endpoint(
            cmd="post",
            url="datasets/isValid",
            data=dset,
            operation="validate_dataset_model",
        )
        if not response["valid"]:
            raise ValueError(f"Dataset {dset} did not pass validation in SciCat.")

    def _send_to_scicat(
        self,
        *,
        cmd: str,
        url: str,
        data: model.BaseModel | None = None,
        params: dict[str, str] | None = None,
    ) -> httpx.Response:
        if self._token is not None:
            token = self._token.get_str()
            headers = {"Authorization": f"Bearer {token}"}
        else:
            token = ""
            headers = {}

        if data is not None:
            headers["Content-Type"] = "application/json"

        try:
            return httpx.request(
                method=cmd,
                url=url,
                content=data.model_dump_json(exclude_none=True)
                if data is not None
                else None,
                params=params,
                headers=headers,
                timeout=self._timeout.seconds,
            )
        except Exception as exc:
            # Remove concrete request function call from backtrace to hide the token.
            # Also modify the error message to strip out the token.
            # It shows up, e.g. in urllib3.exceptions.NewConnectionError.
            # This turns the exception args into strings.
            # But we have little use of more structured errors, so that should be fine.
            raise type(exc)(
                tuple(_strip_token(arg, token) for arg in exc.args)
            ) from None

    def _call_endpoint(
        self,
        *,
        cmd: str,
        url: str,
        operation: str,
        data: model.BaseModel | None = None,
        params: dict[str, str] | None = None,
    ) -> Any:
        full_url = _url_concat(self._base_url, url)
        logger = get_logger()
        logger.info("Calling SciCat API at %s for operation '%s'", full_url, operation)

        response = self._send_to_scicat(cmd=cmd, url=full_url, data=data, params=params)
        if not response.is_success:
            logger.error(
                "SciCat API call to %s failed: %s %s: %s",
                full_url,
                response.status_code,
                response.reason_phrase,
                response.text,
            )
            raise ScicatCommError(
                f"Error in operation '{operation}': {response.status_code} "
                f"{response.reason_phrase}: {response.text}"
            )
        logger.info("API call successful for operation '%s'", operation)

        return None if not response.text else response.json()


def _url_concat(a: str, b: str) -> str:
    # Combine two pieces or a URL without handling absolute
    # paths as in urljoin.
    a = a if a.endswith("/") else (a + "/")
    b = b[1:] if b.endswith("/") else b
    return a + b


def _strip_token(error: Any, token: str) -> str:
    err = str(error)
    err = re.sub(r"token=[\w\-./]+", "token=<HIDDEN>", err)
    if token:  # token can be ""
        err = err.replace(token, "<HIDDEN>")
    return err


def _make_orig_datablock(
    fields: dict[str, Any], strict_validation: bool
) -> model.DownloadOrigDatablock:
    files = [
        model.construct(
            model.DownloadDataFile, _strict_validation=strict_validation, **file_fields
        )
        for file_fields in fields["dataFileList"]
    ]
    return model.construct(
        model.DownloadOrigDatablock,
        _strict_validation=strict_validation,
        **{**fields, "dataFileList": files},
    )


def _log_in_via_users_login(
    url: str, username: StrStorage, password: StrStorage, timeout: datetime.timedelta
) -> httpx.Response:
    # Currently only used for functional accounts.
    response = httpx.post(
        _url_concat(url, "auth/login"),
        json={"username": username.get_str(), "password": password.get_str()},
        timeout=timeout.seconds,
    )
    if not response.is_success:
        get_logger().info(
            "Failed to log in via endpoint Users/login: %s", response.text
        )
    return response


def _log_in_via_auth_msad(
    url: str, username: StrStorage, password: StrStorage, timeout: datetime.timedelta
) -> httpx.Response:
    # Used for user accounts.
    import re

    # Strip the api/vn suffix
    base_url = re.sub(r"/api/v\d+/?", "", url)
    response = httpx.post(
        _url_concat(base_url, "auth/msad"),
        json={"username": username.get_str(), "password": password.get_str()},
        timeout=timeout.seconds,
    )
    if not response.is_success:
        get_logger().error("Failed to log in via auth/msad: %s", response.text)
    return response


def _get_token(
    url: str, username: StrStorage, password: StrStorage, timeout: datetime.timedelta
) -> str:
    """Log in using the provided username + password.

    Returns a token for the given user.
    """
    # Users/login only works for functional accounts and auth/msad for regular users.
    # Try both and see what works. This is not nice but seems to be the only
    # feasible solution right now.
    get_logger().info("Logging in to %s", url)

    response = _log_in_via_users_login(
        url=url, username=username, password=password, timeout=timeout
    )
    if response.is_success:
        return str(response.json()["id"])  # not sure if semantically correct

    response = _log_in_via_auth_msad(
        url=url, username=username, password=password, timeout=timeout
    )
    if response.is_success:
        return str(response.json()["access_token"])

    get_logger().error("Failed log in:  %s", response.text)
    raise ScicatLoginError(response.content)


FileSelector = (
    bool | str | list[str] | tuple[str] | re.Pattern[str] | Callable[[File], bool]
)


def _file_selector(select: FileSelector) -> Callable[[File], bool]:
    if select is True:
        return lambda _: True
    if select is False:
        return lambda _: False
    if isinstance(select, str):
        return lambda f: f.remote_path == select
    if isinstance(select, (list, tuple)):
        return lambda f: f.remote_path in select
    if isinstance(select, re.Pattern):
        return lambda f: (select.search(f.remote_path.posix) is not None)
    return select


def _select_files(select: FileSelector, dataset: Dataset) -> list[File]:
    selector = _file_selector(select)
    return [f for f in dataset.files if selector(f)]


def _remove_up_to_date_local_files(
    files: list[File], checksum_algorithm: str | None
) -> list[File]:
    def is_up_to_date(file: File) -> bool:
        if checksum_algorithm is not None:
            file = dataclasses.replace(file, checksum_algorithm=checksum_algorithm)
        return file.local_is_up_to_date()

    return [
        file
        for file in files
        if not (
            file.local_path.exists() and is_up_to_date(file)  # type: ignore[union-attr]
        )
    ]


def _files_to_upload(files: Iterable[File]) -> list[File]:
    for file in files:
        if file.is_on_local and file.is_on_remote:
            raise ValueError(
                f"Refusing to upload file at remote_path={file.remote_path} "
                "because it is both on local and remote and it is unclear what "
                "to do. If you want to perform the upload, set the local path to None."
            )
    return [file for file in files if file.local_path is not None]


class _NullUploadConnection:
    """File-upload connection that does not upload anything.

    Raises if called with files because uit should only be used by Client
    when there are no files to upload.
    """

    def upload_files(self, *files: File) -> list[File]:
        """Raise if given files."""
        if files:
            raise RuntimeError("Internal error: Bad upload connection")
        return []

    def revert_upload(self, *files: File) -> None:
        """Raise if given files."""
        if files:
            raise RuntimeError("Internal error: Bad upload connection")


def _expect_no_duplicate_filenames(paths: Iterable[Path | None]) -> None:
    counter = Counter(paths)
    non_unique = [str(path) for path, count in counter.items() if count > 1]
    if non_unique:
        raise RuntimeError(
            "Downloading selected files would result in duplicate local filenames: "
            f"({', '.join(non_unique)}). Consider limiting which files get downloaded "
            "using the `select` argument."
        )
