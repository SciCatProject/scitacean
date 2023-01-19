# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 SciCat Project (https://github.com/SciCatProject/scitacean)
"""Client to handle communication with SciCat servers."""

from __future__ import annotations

import datetime
import re
from pathlib import Path
from typing import Callable, List, Optional, Tuple, Union
from urllib.parse import quote_plus

import requests

from . import model
from .dataset import Dataset
from .error import ScicatCommError, ScicatLoginError
from .file import File
from .logging import get_logger
from .pid import PID
from .typing import FileTransfer
from .util.credentials import SecretStr, StrStorage


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
        cls,
        *,
        url: str,
        token: Union[str, StrStorage],
        file_transfer: Optional[FileTransfer] = None,
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
        username: Union[str, StrStorage],
        password: Union[str, StrStorage],
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

    @classmethod
    def without_login(
        cls, *, url: str, file_transfer: Optional[FileTransfer] = None
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

    def get_dataset(
        self, pid: Union[str, PID], strict_validation: bool = False
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

        Returns
        -------
        :
            A new dataset.
        """
        if isinstance(pid, str):
            pid = PID.parse(pid)
        try:
            orig_datablocks = self.scicat.get_orig_datablocks(
                pid, strict_validation=strict_validation
            )
        except ScicatCommError:
            # TODO more precise error handling. We only want to set to None if
            #   communication succeeded and the dataset exists but there simply
            #   are no datablocks.
            orig_datablocks = None
        return Dataset.from_models(
            dataset_model=self.scicat.get_dataset_model(
                pid, strict_validation=strict_validation
            ),
            orig_datablock_models=orig_datablocks,
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
        base_pid = PID.generate()
        dset = dataset.replace(_read_only={"pid": base_pid})
        with self.file_transfer.connect_for_upload(base_pid) as con:
            # TODO check if any remote file is out of date.
            #  if so, raise an error. We never overwrite remote files!
            uploaded_files = con.upload_files(*dset.files)
            dset = dset.replace_files(*uploaded_files).replace(
                source_folder=con.source_dir
            )
            try:
                finalized_model = self.scicat.create_dataset_model(dset.make_model())
            except ScicatCommError:
                con.revert_upload(*uploaded_files)
                raise

        with_new_pid = dset.replace(_read_only={"pid": finalized_model.pid})
        datablock_models = with_new_pid.make_datablock_models()
        finalized_orig_datablocks = self._upload_orig_datablocks(
            datablock_models.orig_datablocks
        )

        return Dataset.from_models(
            dataset_model=finalized_model,
            orig_datablock_models=finalized_orig_datablocks,
        )

    def _upload_orig_datablocks(
        self, orig_datablocks: Optional[List[model.OrigDatablock]]
    ) -> Optional[List[model.OrigDatablock]]:
        if orig_datablocks is None:
            return None

        try:
            return [
                self.scicat.create_orig_datablock(orig_datablock)
                for orig_datablock in orig_datablocks
            ]
        except ScicatCommError as exc:
            raise RuntimeError(
                "Failed to upload original datablocks for SciCat dataset "
                f"{orig_datablocks[0].datasetId}:"
                f"\n{exc.args}\nThe dataset and data files were successfully uploaded "
                "but are not linked with each other. Please fix the dataset manually!"
            ) from exc

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

    def download_files(
        self, dataset: Dataset, *, target: Union[str, Path], select: FileSelector = True
    ) -> Dataset:
        r"""Download files of a dataset.

        Makes selected files available on the local filesystem using the file transfer
        object stored in the client.

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
        target = Path(target)
        # TODO undo if later fails but only if no files were written
        target.mkdir(parents=True, exist_ok=True)
        files = _select_files(select, dataset)
        local_paths = [target / f.remote_path for f in files]
        with self.file_transfer.connect_for_download() as con:
            con.download_files(
                remote=[f.remote_access_path(dataset.source_folder) for f in files],
                local=local_paths,
            )
        downloaded_files = tuple(
            f.downloaded(local_path=l) for f, l in zip(files, local_paths)
        )
        for f in downloaded_files:
            f.validate_after_download()
        return dataset.replace_files(*downloaded_files)


class ScicatClient:
    def __init__(
        self,
        url: str,
        token: Optional[Union[str, StrStorage]],
        timeout: Optional[datetime.timedelta] = None,
    ):
        # Need to add a final /
        self._base_url = url[:-1] if url.endswith("/") else url
        self._timeout = timeout
        self._token: Optional[StrStorage] = (
            SecretStr(token) if isinstance(token, str) else token
        )

    @classmethod
    def from_token(
        cls,
        url: str,
        token: Union[str, StrStorage],
        timeout: Optional[datetime.timedelta] = None,
    ) -> ScicatClient:
        return ScicatClient(url=url, token=token, timeout=timeout)

    @classmethod
    def from_credentials(
        cls,
        url: str,
        username: Union[str, StrStorage],
        password: Union[str, StrStorage],
        timeout: Optional[datetime.timedelta] = None,
    ) -> ScicatClient:
        if not isinstance(username, StrStorage):
            username = SecretStr(username)
        if not isinstance(password, StrStorage):
            password = SecretStr(password)
        return ScicatClient(
            url=url,
            token=SecretStr(
                _get_token(
                    url=url, username=username, password=password, timeout=timeout
                )
            ),
            timeout=timeout,
        )

    @classmethod
    def without_login(
        cls, url: str, timeout: Optional[datetime.timedelta] = None
    ) -> ScicatClient:
        return ScicatClient(url=url, token=None, timeout=timeout)

    def get_dataset_model(
        self, pid: PID, strict_validation: bool = False
    ) -> Union[model.DerivedDataset, model.RawDataset]:
        """Fetch a dataset from SciCat.

        Parameters
        ----------
        pid:
            Unique ID of the dataset. Must include the facility ID.
        strict_validation:
            If ``True``, the dataset must pass validation.
            If ``False``, a dataset is still returned if validation fails.
            Note that some dataset fields may have a bad value or type.
            A warning will be logged if validation fails.

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
        return model.construct(
            model.DerivedDataset
            if dset_json["type"] == "derived"
            else model.RawDataset,
            _strict_validation=strict_validation,
            **dset_json,
        )

    def get_orig_datablocks(
        self, pid: PID, strict_validation: bool = False
    ) -> List[model.OrigDatablock]:
        """Fetch all orig datablocks from SciCat for a given dataset.

        Parameters
        ----------
        pid:
            Unique ID of the *dataset*. Must include the facility ID.
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
            If the datablock does not exist or communication
            fails for some other reason.
        """
        dblock_json = self._call_endpoint(
            cmd="get",
            url=f"Datasets/{quote_plus(str(pid))}/origdatablocks",
            operation="get_orig_datablocks",
        )
        return [
            _make_orig_datablock(dblock, strict_validation=strict_validation)
            for dblock in dblock_json
        ]

    def create_dataset_model(
        self, dset: Union[model.DerivedDataset, model.RawDataset]
    ) -> Union[model.DerivedDataset, model.RawDataset]:
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
        uploaded = self._call_endpoint(
            cmd="post", url="Datasets", data=dset, operation="create_dataset_model"
        )
        return (
            model.DerivedDataset(**uploaded)
            if uploaded["type"] == "derived"
            else model.RawDataset(**uploaded)
        )

    def create_orig_datablock(self, dblock: model.OrigDatablock) -> model.OrigDatablock:
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
        return model.OrigDatablock(
            **self._call_endpoint(
                cmd="post",
                url=f"Datasets/{quote_plus(str(dblock.datasetId))}/origdatablocks",
                data=dblock,
                operation="create_orig_datablock",
            )
        )

    def _send_to_scicat(
        self, *, cmd: str, url: str, data: Optional[model.BaseModel] = None
    ) -> requests.Response:
        if self._token is not None:
            token = self._token.get_str()
            params = {"access_token": token}
            headers = {"Authorization": "Bearer {}".format(token)}
        else:
            params = {}
            headers = {}

        if data is not None:
            headers["Content-Type"] = "application/json"

        try:
            return requests.request(
                method=cmd,
                url=url,
                data=data.json(exclude_none=True) if data is not None else None,
                params=params,
                headers=headers,
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
        logger.info("API call successful for operation '%s'", operation)
        return response.json()


def _url_concat(a: str, b: str) -> str:
    # Combine two pieces or a URL without handling absolute
    # paths as in urljoin.
    a = a if a.endswith("/") else (a + "/")
    b = b[1:] if b.endswith("/") else b
    return a + b


def _make_orig_datablock(fields, strict_validation: bool):
    files = [
        model.construct(
            model.DataFile, _strict_validation=strict_validation, **file_fields
        )
        for file_fields in fields["dataFileList"]
    ]
    return model.construct(
        model.OrigDatablock,
        _strict_validation=strict_validation,
        **{**fields, "dataFileList": files},
    )


def _log_in_via_users_login(
    url: str, username: StrStorage, password: StrStorage, timeout: datetime.timedelta
) -> requests.Response:
    """Currently only used for functional accounts."""
    response = requests.post(
        _url_concat(url, "Users/login"),
        json={"username": username.get_str(), "password": password.get_str()},
        stream=False,
        verify=True,
        timeout=timeout.seconds if timeout is not None else None,
    )
    if not response.ok:
        get_logger().info(
            "Failed to log in via endpoint Users/login: %s", response.json()["error"]
        )
    return response


def _log_in_via_auth_msad(
    url: str, username: StrStorage, password: StrStorage, timeout: datetime.timedelta
) -> requests.Response:
    """Used for user accounts."""
    import re

    # Strip the api/vn suffix
    base_url = re.sub(r"/api/v\d+/?", "", url)
    response = requests.post(
        _url_concat(base_url, "auth/msad"),
        json={"username": username.get_str(), "password": password.get_str()},
        stream=False,
        verify=True,
        timeout=timeout.seconds if timeout is not None else None,
    )
    if not response.ok:
        get_logger().error(
            "Failed to log in via auth/msad: %s", response.json()["error"]
        )
    return response


def _get_token(
    url: str, username: StrStorage, password: StrStorage, timeout: datetime.timedelta
) -> str:
    """Logs in using the provided username + password.

    Returns a token for the given user.
    """
    # Users/login only works for functional accounts and auth/msad for regular users.
    # Try both and see what works. This is not nice but seems to be the only
    # feasible solution right now.
    get_logger().info("Logging in to %s", url)

    response = _log_in_via_users_login(
        url=url, username=username, password=password, timeout=timeout
    )
    if response.ok:
        return response.json()["id"]  # not sure if semantically correct

    response = _log_in_via_auth_msad(
        url=url, username=username, password=password, timeout=timeout
    )
    if response.ok:
        return response.json()["access_token"]

    get_logger().error("Failed log in:  %s", response.json()["error"])
    raise ScicatLoginError(response.content)


FileSelector = Union[
    bool, str, List[str], Tuple[str], re.Pattern, Callable[[File], bool]
]


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
        return lambda f: select.search(str(f.remote_path)) is not None
    return select


def _select_files(select: FileSelector, dataset: Dataset) -> List[File]:
    selector = _file_selector(select)
    return [f for f in dataset.files if selector(f)]
