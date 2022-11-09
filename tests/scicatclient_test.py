# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2022 Scitacean contributors (https://github.com/SciCatProject/scitacean)
# @author Jan-Lukas Wynen
from copy import deepcopy

import pyscicat.client
from pyscicat.model import DataFile, DatasetType, DerivedDataset, OrigDatablock
import pytest

from scitacean.testing.client import FakeClient, FakeScicatClient
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
    return client.scicat


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
        ).scicat


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


def test_get_dataset_model(client, derived_dataset):
    dset = client.get_dataset_model(derived_dataset.pid)
    assert dset == derived_dataset


def test_get_dataset_model_bad_id(client):
    with pytest.raises(pyscicat.client.ScicatCommError):
        client.get_dataset_model("bad-pid")


def test_get_orig_datablock(client, orig_datablock):
    dblock = client.get_orig_datablock(orig_datablock.datasetId)
    assert orig_datablock == dblock


def test_get_orig_datablock_bad_id(client):
    with pytest.raises(pyscicat.client.ScicatCommError):
        client.get_orig_datablock("bollocks")


def test_get_orig_datablock_multi_not_supported(client):
    if isinstance(client, FakeScicatClient):
        dset = data.as_dataset_model(data.load_datasets()[1])
        assert dset.pid == "PID.SAMPLE.PREFIX/dataset-with-2-blocks"
        client.main.datasets[dset.pid] = dset
        dblocks = [
            data.as_orig_datablock_model(data.load_orig_datablocks()[i])
            for i in range(1, 3)
        ]
        client.main.orig_datablocks[dset.pid] = dblocks
    with pytest.raises(NotImplementedError):
        client.get_orig_datablock("PID.SAMPLE.PREFIX/dataset-with-2-blocks")


@pytest.mark.parametrize("pid", ("PID.SAMPLE.PREFIX/jeck", "kamelle", None))
def test_create_dataset_model(pid, client):
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
    full_pid = client.create_dataset_model(dset)
    dset.pid = full_pid
    downloaded = client.get_dataset_model(full_pid)
    for key, expected in dset.dict(exclude_none=True).items():
        # The database populates a number of fields that are None in dset.
        # But we don't want to test those here as we don't want to test the database.
        assert expected == downloaded.dict()[key], f"key = {key}"


def test_create_dataset_model_id_clash(client, derived_dataset):
    dset = deepcopy(derived_dataset)
    dset.pid = dset.pid.split("/")[1]
    dset.owner = "a new owner to trigger a failure"
    with pytest.raises(pyscicat.client.ScicatCommError):
        client.create_dataset_model(dset)


def test_create_first_orig_datablock(client, derived_dataset):
    dset = deepcopy(derived_dataset)
    dset.pid = "new-dataset-id"
    dset.pid = client.create_dataset_model(dset)

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
    client.create_orig_datablock(dblock)
    downloaded = client.get_orig_datablock(dset.pid)
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


def test_fake_can_disable_functions():
    client = FakeClient(
        disable={
            "get_dataset_model": RuntimeError("custom failure"),
            "get_orig_datablock": IndexError("custom index error"),
        }
    )
    with pytest.raises(RuntimeError, match="custom failure"):
        client.scicat.get_dataset_model("some-pid")
    with pytest.raises(IndexError, match="custom index error"):
        client.scicat.get_orig_datablock("some-pid")
