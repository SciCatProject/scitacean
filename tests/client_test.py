# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2022 Scitacean contributors (https://github.com/SciCatProject/scitacean)
# @author Jan-Lukas Wynen
from copy import deepcopy

import dateutil.parser
import pyscicat.client
from pyscicat.model import DataFile, DatasetType, DerivedDataset, OrigDatablock
import pytest

from scitacean.testing.client import FakeClient
from scitacean import Client

from . import data


@pytest.fixture(scope="module")
def derived_dataset():
    return data.as_dataset_model(data.load_datasets()[0])


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
        if not request.config.getoption("--backend-tests"):
            # The backend only exists if this option is set.
            pytest.skip(
                "Tests against a real backend are disabled, "
                "use --backend-tests to enable them"
            )
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
    with pytest.raises(pyscicat.client.ScicatCommError):
        scicat_client.get_dataset_model("bad-pid")


def test_get_orig_datablock(scicat_client, orig_datablock):
    dblock = scicat_client.get_orig_datablocks(orig_datablock.datasetId)
    assert [orig_datablock] == dblock


def test_get_orig_datablock_bad_id(scicat_client):
    with pytest.raises(pyscicat.client.ScicatCommError):
        scicat_client.get_orig_datablocks("bollocks")


@pytest.mark.parametrize("pid", ("PID.SAMPLE.PREFIX/jeck", "kamelle", None))
def test_create_dataset_model(pid, scicat_client):
    dset = DerivedDataset(
        pid=pid,
        contactEmail="black.foess@dom.k",
        creationTime="1995-11-11T11:11:11.000Z",
        owner="bfoess",
        investigator="bfoess",
        sourceFolder="/dom/platt",
        type=DatasetType.derived,
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
    dset.pid = dset.pid.split("/")[1]
    dset.owner = "a new owner to trigger a failure"
    with pytest.raises(pyscicat.client.ScicatCommError):
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
    dset = client.get_dataset(derived_dataset.pid)

    assert dset.source_folder == derived_dataset.sourceFolder
    assert dset.creation_time == derived_dataset.creationTime
    assert dset.access_groups == derived_dataset.accessGroups
    assert dset.meta["temperature"] == derived_dataset.scientificMetadata["temperature"]
    assert dset.meta["data_type"] == derived_dataset.scientificMetadata["data_type"]

    for i in range(len(orig_datablock.dataFileList)):
        assert dset.files[i].local_path is None
        assert dset.files[i].size == orig_datablock.dataFileList[i].size
        assert dset.files[i].creation_time == dateutil.parser.parse(
            orig_datablock.dataFileList[i].time
        )


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
