# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2022 Scitacean contributors (https://github.com/SciCatProject/scitacean)
# @author Jan-Lukas Wynen
from copy import deepcopy

from dateutil.parser import parse as parse_date
import pytest
from scitacean.model import DataFile, DatasetType, DerivedDataset, OrigDatablock
from scitacean import PID, ScicatCommError

from scitacean.testing.client import FakeClient
from scitacean import Client

from . import data
from .common.backend import skip_if_not_backend


@pytest.fixture(scope="module")
def derived_dataset():
    d = data.load_datasets()[0]
    print("!!!0 loaded json: ", d)
    ds = data.as_dataset_model(d)
    print("!!!2 loaded model: ", ds)
    return ds


@pytest.fixture
def orig_datablock(derived_dataset):
    return data.as_orig_datablock_model(data.load_orig_datablocks()[0])


def make_fake_client(dataset, datablock):
    client = FakeClient(file_transfer=None)
    client.datasets[dataset.pid] = dataset
    client.orig_datablocks[dataset.pid] = [datablock]
    return client


@pytest.fixture(params=["real", "fake"])
def client(
    request,
    derived_dataset,
    orig_datablock,
    scicat_access,
    scicat_backend,
):
    if request.param == "fake":
        return make_fake_client(derived_dataset, orig_datablock)
    if request.param == "real":
        skip_if_not_backend(request)
        return Client.from_credentials(
            url=scicat_access.url, **scicat_access.functional_credentials
        )


@pytest.fixture
def scicat_client(client):
    return client.scicat


def test_from_token_fake():
    # This should not call the API
    assert isinstance(
        FakeClient.from_token(url="some.url/api/v3", token="a-token"), FakeClient
    )


def test_from_credentials_fake():
    # This should not call the API
    assert isinstance(
        FakeClient.from_credentials(
            url="some.url/api/v3", username="someone", password="the-fake-does-not-care"
        ),
        FakeClient,
    )


def test_from_credentials_real(scicat_access, scicat_backend):
    if not scicat_backend:
        pytest.skip("No backend")
    Client.from_credentials(
        url=scicat_access.url, **scicat_access.functional_credentials
    )


def test_get_dataset_model(scicat_client, derived_dataset):
    dset = scicat_client.get_dataset_model(derived_dataset.pid)
    assert dset == derived_dataset


def test_get_dataset_model_bad_id(scicat_client):
    with pytest.raises(ScicatCommError):
        scicat_client.get_dataset_model("bad-pid")


def test_get_orig_datablock(scicat_client, orig_datablock):
    dblock = scicat_client.get_orig_datablocks(orig_datablock.datasetId)
    assert [orig_datablock] == dblock


def test_get_orig_datablock_bad_id(scicat_client):
    with pytest.raises(ScicatCommError):
        scicat_client.get_orig_datablocks("bollocks")


@pytest.mark.parametrize("pid", ("PID.SAMPLE.PREFIX/jeck", "kamelle", None))
def test_create_dataset_model(pid, scicat_client):
    dset = DerivedDataset(
        pid=pid,
        contactEmail="black.foess@dom.koelle",
        creationTime=parse_date("1995-11-11T11:11:11.000Z"),
        owner="bfoess",
        investigator="b.foess@dom.koelle",
        sourceFolder="/dom/platt",
        type=DatasetType.DERIVED,
        inputDatasets=[],
        usedSoftware=[],
        ownerGroup="bfoess",
        accessGroups=["koelle"],
    )
    full_pid = scicat_client.create_dataset_model(dset)
    dset.pid = full_pid
    downloaded = scicat_client.get_dataset_model(full_pid)
    for key, expected in dset.dict(exclude_none=True).items():
        # The database populates a number of fields that are None in dset.
        # But we don't want to test those here as we don't want to test the database.
        assert expected == downloaded.dict()[key], f"key = {key}"


def test_create_dataset_model_id_clash(scicat_client, derived_dataset):
    dset = deepcopy(derived_dataset)
    dset.pid = PID(prefix=None, pid=dset.pid.pid)
    dset.owner = "a new owner to trigger a failure"
    with pytest.raises(ScicatCommError):
        scicat_client.create_dataset_model(dset)


def test_create_first_orig_datablock(scicat_client, derived_dataset):
    dset = deepcopy(derived_dataset)
    dset.pid = "new-dataset-id"
    dset.pid = scicat_client.create_dataset_model(dset)

    dblock = OrigDatablock(
        id="PID.SAMPLE.PREFIX/new-datablock-id",
        size=9235,
        dataFileList=[
            DataFile(path="data.nxs", size=9235, time="2023-08-18T13:52:33.000Z")
        ],
        datasetId=dset.pid,
        ownerGroup="uu",
        accessGroups=["group1", "2nd_group"],
    )
    scicat_client.create_orig_datablock(dblock)
    downloaded = scicat_client.get_orig_datablocks(dset.pid)
    assert len(downloaded) == 1
    downloaded = downloaded[0]
    for key, expected in dblock.dict(exclude_none=True).items():
        # The database populates a number of fields that are None in dset.
        # But we don't want to test those here as we don't want to test the database.
        if key != "dataFileList":
            assert expected == downloaded.dict()[key], f"key = {key}"
    for i in range(len(dblock.dataFileList)):
        for key, expected in dblock.dataFileList[i].dict(exclude_none=True).items():
            assert (
                expected == downloaded.dataFileList[i].dict()[key]
            ), f"i = {i}, key = {key}"


def test_get_dataset(client, derived_dataset, orig_datablock):
    d = data.load_datasets()[0]
    print("!!!0 loaded json: ", d)
    ds = data.as_dataset_model(d)
    print("!!!2 loaded model: ", ds)
    derived_dataset = ds
    print("!!!t in test: ", derived_dataset)
    assert derived_dataset.pid is not None
    dset = client.get_dataset(derived_dataset.pid)

    assert dset.source_folder == derived_dataset.sourceFolder
    assert dset.creation_time == derived_dataset.creationTime
    assert dset.access_groups == derived_dataset.accessGroups
    assert dset.meta["temperature"] == derived_dataset.scientificMetadata["temperature"]
    assert dset.meta["data_type"] == derived_dataset.scientificMetadata["data_type"]

    for dset_file, expected_file in zip(dset.files, orig_datablock.dataFileList):
        assert dset_file.local_path is None
        assert dset_file.size == expected_file.size
        assert dset_file.creation_time == expected_file.time


def test_fake_can_disable_functions():
    client = FakeClient(
        disable={
            "get_dataset_model": RuntimeError("custom failure"),
            "get_orig_datablocks": IndexError("custom index error"),
        }
    )
    with pytest.raises(RuntimeError, match="custom failure"):
        client.scicat.get_dataset_model("some-pid")
    with pytest.raises(IndexError, match="custom index error"):
        client.scicat.get_orig_datablocks("some-pid")


def test_can_get_public_dataset_without_login(request, scicat_access, scicat_backend):
    skip_if_not_backend(request)
    client = Client.without_login(url=scicat_access.url)
    dset = client.get_dataset("PID.SAMPLE.PREFIX/public-dataset")
    assert dset.type == DatasetType.RAW
    assert dset.owner == "librarian"
    assert dset.creation_time == parse_date("2022-11-25T22:12:04.512Z")
    assert dset.number_of_files == 0


def test_cannot_upload_without_login(
    request, derived_dataset, scicat_access, scicat_backend
):
    skip_if_not_backend(request)
    client = Client.without_login(url=scicat_access.url)
    derived_dataset.pid = None
    with pytest.raises(ScicatCommError):
        client.scicat.create_dataset_model(derived_dataset)
