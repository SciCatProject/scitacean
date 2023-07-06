# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 SciCat Project (https://github.com/SciCatProject/scitacean)
import pickle

import pydantic
import pytest
from dateutil.parser import parse as parse_date

from scitacean import PID, Client, RemotePath, ScicatCommError
from scitacean.client import ScicatClient
from scitacean.model import (
    DatasetType,
    UploadDataFile,
    UploadDerivedDataset,
    UploadOrigDatablock,
)
from scitacean.testing.backend.seed import INITIAL_DATASETS, INITIAL_ORIG_DATABLOCKS
from scitacean.testing.client import FakeClient
from scitacean.util.credentials import SecretStr


@pytest.fixture()
def scicat_client(client) -> ScicatClient:
    return client.scicat


@pytest.fixture()
def derived_dataset(scicat_access):
    return UploadDerivedDataset(
        contactEmail="black.foess@dom.koelle",
        creationTime=parse_date("1995-11-11T11:11:11.000Z"),
        owner="bfoess",
        investigator="b.foess@dom.koelle",
        sourceFolder="/dom/platt",
        type=DatasetType.DERIVED,
        inputDatasets=[],
        usedSoftware=[],
        ownerGroup=scicat_access.user.group,
        accessGroups=["koelle"],
        numberOfFilesArchived=0,
    )


@pytest.fixture()
def orig_datablock(scicat_access):
    # NOTE the placeholder!
    return UploadOrigDatablock(
        size=9235,
        dataFileList=[
            UploadDataFile(
                path="data.nxs", size=9235, time=parse_date("2023-08-18T13:52:33.000Z")
            )
        ],
        datasetId="PLACEHOLDER",
        ownerGroup="uu",
        accessGroups=["group1", "2nd_group"],
    )


def test_from_token_fake():
    # This should not call the API
    client = FakeClient.from_token(url="some.url/api/v3", token="a-token")  # noqa: S106
    assert isinstance(client, FakeClient)


def test_from_credentials_fake():
    # This should not call the API
    client = FakeClient.from_credentials(
        url="some.url/api/v3",
        username="someone",
        password="the-fake-does-not-care",  # noqa: S106
    )
    assert isinstance(
        client,
        FakeClient,
    )


def test_from_credentials_real(scicat_access, scicat_backend):
    if not scicat_backend:
        pytest.skip("No backend")
    Client.from_credentials(url=scicat_access.url, **scicat_access.user.credentials)


@pytest.mark.parametrize("key", ("raw", "derived"))
def test_get_dataset_model(scicat_client, key):
    dset = INITIAL_DATASETS[key]
    downloaded = scicat_client.get_dataset_model(dset.pid)
    assert downloaded == dset


def test_get_dataset_model_bad_id(scicat_client):
    with pytest.raises(ScicatCommError):
        scicat_client.get_dataset_model(PID(pid="bad-pid"))


@pytest.mark.parametrize("key", ("raw", "derived"))
def test_get_orig_datablock(scicat_client, key):
    dblock = INITIAL_ORIG_DATABLOCKS[key][0]
    downloaded = scicat_client.get_orig_datablocks(dblock.datasetId)
    assert downloaded == [dblock]


def test_get_orig_datablock_bad_id(scicat_client):
    with pytest.raises(ScicatCommError):
        scicat_client.get_orig_datablocks(PID(pid="bollocks"))


def test_create_dataset_model(scicat_client, derived_dataset):
    finalized = scicat_client.create_dataset_model(derived_dataset)
    downloaded = scicat_client.get_dataset_model(finalized.pid)
    for key, expected in finalized:
        # The database populates a number of fields that are None in dset.
        # But we don't want to test those here as we don't want to test the database.
        if expected is not None:
            assert expected == dict(downloaded)[key], f"key = {key}"


def test_create_first_orig_datablock(scicat_client, derived_dataset, orig_datablock):
    uploaded = scicat_client.create_dataset_model(derived_dataset)
    orig_datablock.datasetId = uploaded.pid
    scicat_client.create_orig_datablock(orig_datablock)
    downloaded = scicat_client.get_orig_datablocks(uploaded.pid)
    assert len(downloaded) == 1
    downloaded = downloaded[0]
    for key, expected in orig_datablock:
        # The database populates a number of fields that are None in dset.
        # But we don't want to test those here as we don't want to test the database.
        if expected is not None and key != "dataFileList":
            assert expected == dict(downloaded)[key], f"key = {key}"
    for i in range(len(orig_datablock.dataFileList)):
        for key, expected in orig_datablock.dataFileList[i]:
            assert (
                expected == dict(downloaded.dataFileList[i])[key]
            ), f"i = {i}, key = {key}"


def test_get_dataset(client):
    dset = INITIAL_DATASETS["raw"]
    dblock = INITIAL_ORIG_DATABLOCKS["raw"][0]
    downloaded = client.get_dataset(dset.pid)

    assert downloaded.source_folder == dset.sourceFolder
    assert downloaded.creation_time == dset.creationTime
    assert downloaded.access_groups == dset.accessGroups
    assert downloaded.meta["temperature"] == dset.scientificMetadata["temperature"]
    assert downloaded.meta["data_type"] == dset.scientificMetadata["data_type"]

    for dset_file, expected_file in zip(downloaded.files, dblock.dataFileList):
        assert dset_file.local_path is None
        assert dset_file.size == expected_file.size
        assert dset_file.creation_time == expected_file.time


def test_can_get_public_dataset_without_login(require_scicat_backend, scicat_access):
    client = Client.without_login(url=scicat_access.url)

    dset = INITIAL_DATASETS["public"]
    dblock = INITIAL_ORIG_DATABLOCKS["public"][0]
    downloaded = client.get_dataset(dset.pid)

    assert downloaded.source_folder == dset.sourceFolder
    assert downloaded.creation_time == dset.creationTime
    assert downloaded.access_groups == dset.accessGroups

    for dset_file, expected_file in zip(downloaded.files, dblock.dataFileList):
        assert dset_file.local_path is None
        assert dset_file.size == expected_file.size
        assert dset_file.creation_time == expected_file.time


def test_cannot_upload_without_login(
    require_scicat_backend, derived_dataset, scicat_access
):
    client = Client.without_login(url=scicat_access.url)
    with pytest.raises(ScicatCommError):  # TODO test return code 403
        client.scicat.create_dataset_model(derived_dataset)


def test_get_broken_dataset(client):
    dset = INITIAL_DATASETS["partially-broken"]
    downloaded = client.get_dataset(dset.pid)
    assert downloaded.type == DatasetType.DERIVED
    # Intact field; was properly converted to RemotePath
    assert isinstance(downloaded.source_folder, RemotePath)
    assert downloaded.source_folder == "/remote/source"

    # Broken fields loaded
    assert isinstance(downloaded.orcid_of_owner, str)
    assert downloaded.orcid_of_owner == "00-11-22-33"

    # Ignored broken fields
    assert isinstance(downloaded.number_of_files, int)
    assert downloaded.number_of_files == 0
    assert isinstance(downloaded.size, int)
    assert downloaded.size == 0


def test_get_broken_dataset_strict_validation(real_client, require_scicat_backend):
    dset = INITIAL_DATASETS["partially-broken"]
    with pytest.raises(pydantic.ValidationError):
        real_client.get_dataset(dset.pid, strict_validation=True)


def test_cannot_pickle_client_credentials_manual_token_str():
    client = Client.from_token(url="/", token="the-token")  # noqa: S106
    with pytest.raises(TypeError):
        pickle.dumps(client)


def test_cannot_pickle_client_credentials_manual_token_secret_str():
    client = Client.from_token(url="/", token=SecretStr("the-token"))
    with pytest.raises(TypeError):
        pickle.dumps(client)


def test_cannot_pickle_client_credentials_login(scicat_access, require_scicat_backend):
    client = Client.from_credentials(
        url=scicat_access.url, **scicat_access.user.credentials
    )
    with pytest.raises(TypeError):
        pickle.dumps(client)


def test_connection_error_does_not_contain_token():
    client = Client.from_token(
        url="https://not-actually-a_server",
        token="the token/which_must-be.kept secret",  # noqa: S106
    )
    try:
        client.get_dataset("does not exist")
        assert False, "There must be an exception"  # noqa: B011
    except Exception as exc:
        assert "the token/which_must-be.kept secret" not in str(exc)
        for arg in exc.args:
            assert "the token/which_must-be.kept secret" not in str(arg)


def test_fake_can_disable_functions():
    client = FakeClient(
        disable={
            "get_dataset_model": RuntimeError("custom failure"),
            "get_orig_datablocks": IndexError("custom index error"),
        }
    )
    with pytest.raises(RuntimeError, match="custom failure"):
        client.scicat.get_dataset_model(PID(pid="some-pid"))
    with pytest.raises(IndexError, match="custom index error"):
        client.scicat.get_orig_datablocks(PID(pid="some-pid"))
