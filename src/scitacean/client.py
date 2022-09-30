# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2022 Scitacean contributors (https://github.com/SciCatProject/scitacean)
# @author Jan-Lukas Wynen
from __future__ import annotations
from typing import Union

import pyscicat.client
from pyscicat import model

# TODO check that PID is handled as described in create_* methods


class Client:
    """SciCat client to communicate with a backend.

    Users of Scitacean should instantiate this class but not use it directly.
    The corresponding methods of ``Dataset`` should be preferred as ``Client``
    handles basic API calls to SciCat but not files.

    Use :func:`Client.from_token` or :func:`Client.from_credentials` to initialize
    a client instead of the constructor directly.
    """

    def __init__(self, *, client):
        self._client = client

    @classmethod
    def from_token(cls, *, url, token) -> Client:
        """Create a new client and authenticate with a token.

        Parameters
        ----------
        url:
            URL of the SciCat api.
            It should include the suffix `api/vn` where `n` is a number.
        token:
            User token to authenticate with SciCat.

        Returns
        -------
        :
            A new client.
        """
        return Client(client=pyscicat.client.from_token(base_url=url, token=token))

    @classmethod
    def from_credentials(cls, *, url, username, password) -> Client:
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

        Returns
        -------
        :
            A new client.
        """
        return Client(
            client=pyscicat.client.from_credentials(
                base_url=url, username=username, password=password
            )
        )

    def get_dataset(self, pid: str) -> Union[model.DerivedDataset, model.RawDataset]:
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
         pyscicat.client.ScicatCommError
            If the dataset does not exist or communication fails for some other reason.
        """
        if dset_json := self._client.datasets_get_one(pid):
            return (
                model.DerivedDataset(**dset_json)
                if dset_json["type"] == "derived"
                else model.RawDataset(**dset_json)
            )
        raise pyscicat.client.ScicatCommError(f"Unable to retrieve dataset {pid}")

    def get_orig_datablock(self, pid: str) -> model.OrigDatablock:
        """Fetch an orig datablock from SciCat.

        Parameters
        ----------
        pid:
            Unique ID of the *dataset*. Must include the facility ID.

        Returns
        -------
        :
            A model of the datablock.

        Raises
        ------
         pyscicat.client.ScicatCommError
            If the datablock does not exist or communication
            fails for some other reason.
        """
        if dblock_json := self._client.datasets_origdatablocks_get_one(pid):
            if len(dblock_json) != 1:
                raise NotImplementedError(
                    f"Got {len(dblock_json)} original datablocks for dataset {pid} "
                    "but only support for one is implemented."
                )
            return _make_orig_datablock(dblock_json[0])
        raise pyscicat.client.ScicatCommError(
            f"Unable to retrieve orig datablock for dataset {pid}"
        )

    def create_dataset(self, dset: model.Dataset) -> str:
        """Create a new dataset in SciCat.

        The dataset PID must be either

        - ``None``, in which case SciCat assigns an ID.
        - An unused id, in which case SciCat uses it for the new dataset.

        If the ID already exists, creation will fail without
        modification to the database.

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
         pyscicat.client.ScicatCommError
            If SciCat refuses the dataset or communication
            fails for some other reason.
        """
        return self._client.datasets_create(dset)["pid"]

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
         pyscicat.client.ScicatCommError
            If SciCat refuses the datablock or communication
            fails for some other reason.
        """
        self._client.datasets_origdatablock_create(dblock)


def _make_orig_datablock(fields):
    files = [model.DataFile(**file_fields) for file_fields in fields["dataFileList"]]
    return model.OrigDatablock(**{**fields, "dataFileList": files})
