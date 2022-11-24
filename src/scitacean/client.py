# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2022 Scitacean contributors (https://github.com/SciCatProject/scitacean)
# @author Jan-Lukas Wynen
"""Client to handle communication with SciCat servers."""

from __future__ import annotations

import datetime
from pathlib import Path
from typing import List, Optional, Union
from urllib.parse import quote_plus

import requests

from .dataset import Dataset
from .error import ScicatCommError, ScicatLoginError
from .logging import get_logger
from .pid import PID
from .typing import FileTransfer
from . import model


class Client:
    """SciCat client to communicate with a server.

    Clients hold all information needed to communicate with a SciCat instance
    and a filesystem that holds data files (via ``file_transfer``).

    Use :func:`Client.from_token` or :func:`Client.from_credentials` to initialize
    a client instead of the constructor directly.

    See the user guide for typical usage patterns.
    In particular `Downloading Datasets <../../user-guide/downloading.ipynb>`_
    and `Uploading Datasets <../../user-guide/uploading.ipynb>`_.
    """

    def __init__(
        self,
        *,
        client: ScicatClient,
        file_transfer: Optional[FileTransfer],
    ):
        """Initialize a client.

        Do not use directly, instead use :func:`Client.from_token`
        or :func:`Client.from_credentials`!
        """
        self._client = client
        self._file_transfer = file_transfer

    @classmethod
    def from_token(
        cls, *, url: str, token: str, file_transfer: Optional[FileTransfer] = None
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
        username: str,
        password: str,
        file_transfer: Optional[FileTransfer] = None,
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

    def get_dataset(self, pid: Union[str, PID]) -> Dataset:
        """Download a dataset from SciCat.

        Does not download any files.

        Parameters
        ----------
        pid:
            ID of the dataset. Must include the prefix, i.e. have the form
            ``prefix/dataset-id``.

        Returns
        -------
        :
            A new dataset.
        """
        if isinstance(pid, str):
            pid = PID.parse(pid)
        return Dataset.from_models(
            dataset_model=self.scicat.get_dataset_model(pid),
            orig_datablock_models=self.scicat.get_orig_datablocks(pid),
        )

    def upload_new_dataset_now(self, dataset: Dataset) -> Dataset:
        """Upload a dataset as a new entry to SciCat immediately.

        The dataset is inserted as a new entry in the database and will
        never overwrite existing data.
        To this end, the input dataset's ID is ignored and a new one is
        assigned automatically.

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
        dset = dataset.prepare_as_new()
        dset.pid = dset.pid.without_prefix
        with self.file_transfer.connect_for_upload(dset.pid) as con:
            dset.source_folder = con.source_dir
            for file in dset.files:
                file.source_folder = dset.source_folder
                con.upload_file(local=file.local_path, remote=file.remote_access_path)

            models = dset.make_scicat_models()
            try:
                dataset_id = self.scicat.create_dataset_model(models.dataset)
            except ScicatCommError:
                for file in dset.files:
                    con.revert_upload(
                        local=file.local_path, remote=file.remote_access_path
                    )
                raise

        dset.pid = dataset_id
        models.datablock.datasetId = dataset_id
        try:
            self.scicat.create_orig_datablock(models.datablock)
        except ScicatCommError as exc:
            raise RuntimeError(
                f"Failed to upload original datablocks for SciCat dataset {dset.pid}:"
                f"\n{exc.args}\nThe dataset and data files were successfully uploaded "
                "but are not linked with each other. Please fix the dataset manually!"
            ) from exc

        return dset

    @property
    def scicat(self) -> ScicatClient:
        """Low level client for SciCat.

        Should typically not be used by users of Scitacean!
        """
        return self._client

    @property
    def file_transfer(self) -> FileTransfer:
        """Stored handler for file down-/uploads."""
        return self._file_transfer

    def download_file(self, *, remote: Union[str, Path], local: Union[str, Path]):
        if self._file_transfer is None:
            raise RuntimeError(
                f"No file transfer handler specified, cannot download file {remote}"
            )
        with self._file_transfer.connect_for_download() as con:
            con.download_file(remote=remote, local=local)

    def upload_file(
        self, *, dataset_id: str, remote: Union[str, Path], local: Union[str, Path]
    ) -> str:
        if self._file_transfer is None:
            raise RuntimeError(
                f"No file transfer handler specified, cannot upload file {local}"
            )
        with self._file_transfer.connect_for_upload(dataset_id) as con:
            return con.upload_file(remote=remote, local=local)


class ScicatClient:
    def __init__(
        self, url: str, token: str, timeout: Optional[datetime.timedelta] = None
    ):
        # Need to add a final /
        self._base_url = url[:-1] if url.endswith("/") else url
        self._timeout = timeout
        self._token = token

    @classmethod
    def from_token(
        cls, url: str, token: str, timeout: Optional[datetime.timedelta] = None
    ) -> ScicatClient:
        return ScicatClient(url=url, token=token, timeout=timeout)

    @classmethod
    def from_credentials(
        cls,
        url: str,
        username: str,
        password: str,
        timeout: Optional[datetime.timedelta] = None,
    ) -> ScicatClient:
        return ScicatClient(
            url=url,
            token=_get_token(url=url, username=username, password=password),
            timeout=timeout,
        )

    def get_dataset_model(
        self, pid: PID
    ) -> Union[model.DerivedDataset, model.RawDataset]:
        """Fetch a dataset from SciCat.

        Parameters
        ----------
        pid:
            Unique ID of the dataset. Must include the facility ID.

        Returns
        -------
        :
            A model of the dataset. The type is deduced from the received data.

        Raises
        ------
        scitacean.ScicatCommError
            If the dataset does not exist or communication fails for some other reason.
        """
        dset_json = self._call_endpoint(
            cmd="get",
            url=f"Datasets/{quote_plus(str(pid))}",
            operation="get_dataset_model",
        )
        return (
            model.DerivedDataset(**dset_json)
            if dset_json["type"] == "derived"
            else model.RawDataset(**dset_json)
        )

    def get_orig_datablocks(self, pid: PID) -> List[model.OrigDatablock]:
        """Fetch all orig datablocks from SciCat for a given dataset.

        Parameters
        ----------
        pid:
            Unique ID of the *dataset*. Must include the facility ID.

        Returns
        -------
        :
            Models of the orig datablocks.

        Raises
        ------
        scitacean.ScicatCommError
            If the datablock does not exist or communication
            fails for some other reason.
        """
        dblock_json = self._call_endpoint(
            cmd="get",
            url=f"Datasets/{quote_plus(str(pid))}/origdatablocks",
            operation="get_orig_datablocks",
        )
        return [_make_orig_datablock(dblock) for dblock in dblock_json]

    # TODO return full dataset
    def create_dataset_model(
        self, dset: Union[model.DerivedDataset, model.RawDataset]
    ) -> PID:
        """Create a new dataset in SciCat.

        The dataset PID must be either

        - ``None``, in which case SciCat assigns an ID.
        - An unused id, in which case SciCat uses it for the new dataset.

        If the ID already exists, creation will fail without
        modification to the database.
        Unless the new dataset is identical to the existing one,
        in which case nothing happens.

        Parameters
        ----------
        dset:
            Model of the dataset to create.

        Returns
        -------
        :
            The PID of the new dataset in the catalogue.

        Raises
        ------
        scitacean.ScicatCommError
            If SciCat refuses the dataset or communication
            fails for some other reason.
        """
        return self._call_endpoint(
            cmd="post", url="Datasets", data=dset, operation="create_dataset_model"
        ).get("pid")

    def create_orig_datablock(self, dblock: model.OrigDatablock):
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

        Raises
        ------
        scitacean.ScicatCommError
            If SciCat refuses the datablock or communication
            fails for some other reason.
        """
        return self._call_endpoint(
            cmd="post",
            url=f"Datasets/{quote_plus(str(dblock.datasetId))}/origdatablocks",
            data=dblock,
            operation="create_orig_datablock",
        )

    def _send_to_scicat(
        self, *, cmd: str, url: str, data: Optional[model.BaseModel] = None
    ) -> requests.Response:
        try:
            return requests.request(
                method=cmd,
                url=url,
                data=data.json(exclude_none=True) if data is not None else None,
                params={"access_token": self._token},
                headers={
                    "Authorization": "Bearer {}".format(self._token),
                    "Content-Type": "application/json",
                },
                timeout=self._timeout.seconds if self._timeout is not None else None,
                stream=False,
                verify=True,
            )
        except Exception as exc:
            # Remove concrete request function call from backtrace.
            raise type(exc)(exc.args) from None

    def _call_endpoint(
        self,
        *,
        cmd: str,
        url: str,
        data: Optional[model.BaseModel] = None,
        operation: str,
    ) -> Optional[dict]:
        full_url = _url_concat(self._base_url, url)
        logger = get_logger()
        logger.info("Calling SciCat API at %s for operation '%s'", full_url, operation)

        response = self._send_to_scicat(cmd=cmd, url=full_url, data=data)
        if not response.ok:
            err = response.json().get("error", {})
            logger.error("API call failed, endpoint: %s, response: %s", full_url, err)
            raise ScicatCommError(f"Error in operation {operation}: {err}")
        logger.info("API call successful for operation '%s'")
        return response.json()


def _url_concat(a: str, b: str) -> str:
    # Combine two pieces or a URL without handling absolute
    # paths as in urljoin.
    a = a if a.endswith("/") else (a + "/")
    b = b[1:] if b.endswith("/") else b
    return a + b


def _make_orig_datablock(fields):
    files = [model.DataFile(**file_fields) for file_fields in fields["dataFileList"]]
    return model.OrigDatablock(**{**fields, "dataFileList": files})


def _log_in_via_users_login(
    url: str, username: str, password: str
) -> requests.Response:
    """Currently only used for functional accounts."""
    response = requests.post(
        _url_concat(url, "Users/login"),
        json={"username": username, "password": password},
        stream=False,
        verify=True,
    )
    if not response.ok:
        get_logger().info(
            "Failed to log in via endpoint Users/login: %s", response.json()["error"]
        )
    return response


def _log_in_via_auth_msad(url: str, username: str, password: str) -> requests.Response:
    """Used for user accounts."""
    import re

    # Strip the api/vn suffix
    base_url = re.sub(r"/api/v\d+/?", "", url)
    response = requests.post(
        _url_concat(base_url, "auth/msad"),
        json={"username": username, "password": password},
        stream=False,
        verify=True,
    )
    if not response.ok:
        get_logger().error(
            "Failed to log in via auth/msad: %s", response.json()["error"]
        )
    return response


def _get_token(url: str, username: str, password: str) -> str:
    """Logs in using the provided username + password

    Returns a token for the given user.
    """
    # Users/login only works for functional accounts and auth/msad for regular users.
    # Try both and see what works. This is not nice but seems to be the only
    # feasible solution right now.
    get_logger().info("Loging in to %s", url)

    response = _log_in_via_users_login(url=url, username=username, password=password)
    if response.ok:
        return response.json()["id"]  # not sure if semantically correct

    response = _log_in_via_auth_msad(url=url, username=username, password=password)
    if response.ok:
        return response.json()["access_token"]

    get_logger().error("Failed log in:  %s", response.json()["error"])
    raise ScicatLoginError(response.content)
