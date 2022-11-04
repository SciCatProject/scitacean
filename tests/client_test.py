# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2022 Scitacean contributors (https://github.com/SciCatProject/scitacean)
# @author Jan-Lukas Wynen
from copy import deepcopy
import dataclasses
import re
from typing import Dict, List, Union
from urllib.parse import quote_plus, urljoin
from uuid import uuid4

import pyscicat.client
from pyscicat.model import DataFile, DatasetType, DerivedDataset, OrigDatablock, Ownable
import pytest
import requests_mock

from scitacean.testing.client import FakeClient
from scitacean import Client

from . import data


@dataclasses.dataclass
class MockStorage:
    datasets: Dict[str, dict] = dataclasses.field(default_factory=dict)
    orig_datablocks: Dict[str, List[dict]] = dataclasses.field(default_factory=dict)

    def handle_get_dataset(self, request, context) -> dict:
        pid = request.path.rsplit("/", 1)[1]
        try:
            return self.datasets[pid]
        except KeyError:
            context.status_code = 404
            return {
                "error": {
                    "statusCode": 404,
                    "name": "Error",
                    "message": f'Unknown "Dataset" id "{pid}".',
                    "code": "MODEL_NOT_FOUND",
                }
            }

    def handle_get_orig_datablock(self, request, context) -> Union[List[dict], dict]:
        pid = request.path.rsplit("/", 2)[1]
        try:
            return self.orig_datablocks[pid]
        except KeyError:
            context.status_code = 404
            return {
                "error": {
                    "statusCode": 404,
                    "name": "Error",
                    "message": f'could not find a model with id "{pid}".',
                    "code": "MODEL_NOT_FOUND",
                }
            }

    def handle_post_dataset(self, request, context) -> dict:
        dset = deepcopy(request.json())
        pid = dset.get("pid")
        if pid is None:
            pid = "PID.SAMPLE.PREFIX/" + uuid4().hex
        elif "/" not in pid:
            pid = "PID.SAMPLE.PREFIX/" + pid
        dset["pid"] = pid
        encoded_pid = quote_plus(pid).lower()

        if encoded_pid in self.datasets:
            context.status_code = 404
            return {
                "error": {
                    "statusCode": 422,
                    "name": "ValidationError",
                    "message": "The `Dataset` instance is not valid. Details: `pid` "
                    f'is not unique (value: "{pid}").',
                    "details": {
                        "context": "Dataset",
                        "codes": {"pid": ["uniqueness"]},
                        "messages": {"pid": ["is not unique"]},
                    },
                }
            }
        self.datasets[encoded_pid] = dset
        context.status_code = 200
        return self.datasets[encoded_pid]

    def handle_post_orig_datablock(self, request, context) -> dict:
        pid = request.path.rsplit("/", 2)[1]

        if pid not in self.datasets:
            context.status_code = 404
            return {
                "error": {
                    "statusCode": 404,
                    "name": "Error",
                    "message": f"could not find a model with id {pid}",
                    "code": "MODEL_NOT_FOUND",
                }
            }
        self.orig_datablocks.setdefault(pid, []).append(deepcopy(request.json()))
        context.status_code = 200
        return self.orig_datablocks[pid][-1]


@pytest.fixture
def ownable():
    return Ownable(ownerGroup="uu", accessGroups=["darkmagic", "faculty"])


@pytest.fixture(scope="module")
def derived_dataset():
    return data.as_dataset_model(data.load_datasets()[0])


@pytest.fixture
def orig_datablock(ownable, derived_dataset):
    return data.as_orig_datablock_model(data.load_orig_datablocks()[0])


@pytest.fixture
def mock_storage(derived_dataset, orig_datablock):
    return MockStorage(
        datasets={
            quote_plus(derived_dataset.pid).lower(): derived_dataset.dict(
                exclude_none=True
            )
        },
        orig_datablocks={
            quote_plus(derived_dataset.pid).lower(): [
                orig_datablock.dict(exclude_none=True)
            ]
        },
    )


@pytest.fixture
def mock_scicat_url() -> str:
    return "http://localhost:3000/api/v3/"


@pytest.fixture
def user_token() -> str:
    return "a_token"


@pytest.fixture
def mock_request(mock_scicat_url, user_token, mock_storage):
    with requests_mock.Mocker() as mock:
        mock.post(
            urljoin(mock_scicat_url, "Users/login"),
            json={"id": user_token},
        )
        # TODO client inserts 2 slashes before 'Dataset':
        #  http://localhost:3000/api/v3//Datasets/...
        mock.get(
            re.compile(rf"{mock_scicat_url}/Datasets/[^?/]+"),
            json=mock_storage.handle_get_dataset,
        )
        mock.get(
            re.compile(rf"{mock_scicat_url}/Datasets/[^?/]+/origdatablocks"),
            json=mock_storage.handle_get_orig_datablock,
        )
        mock.post(
            urljoin(mock_scicat_url, "Datasets"), json=mock_storage.handle_post_dataset
        )
        mock.post(
            re.compile(mock_scicat_url + r"Datasets/[^?/]+/origdatablocks"),
            json=mock_storage.handle_post_orig_datablock,
        )
        yield mock


def make_mock_client(url, token):
    return Client.from_token(url=url, token=token)


def make_fake_client(dataset, datablock):
    client = FakeClient(file_transfer=None)
    client.datasets[dataset.pid] = dataset
    client.orig_datablocks[dataset.pid] = [datablock]
    return client


@pytest.fixture(params=["real", "mock", "fake"])
def client(
    request,
    derived_dataset,
    orig_datablock,
    scicat_access,
    mock_scicat_url,
    user_token,
    mock_request,
    scicat_backend,
):
    if request.param == "mock":
        return make_mock_client(mock_scicat_url, user_token)
    if request.param == "fake":
        return make_fake_client(derived_dataset, orig_datablock)
    if request.param == "real":
        if not request.config.getoption("--backend-tests"):
            # The backend only exists if this option is set.
            pytest.skip(
                "Tests against a real backend are disabled, "
                "use --backend-tests to enable them"
            )
        mock_request.register_uri(
            requests_mock.ANY, re.compile(scicat_access.url + ".*"), real_http=True
        )
        return Client.from_credentials(
            url=scicat_access.url, **scicat_access.functional_credentials
        )


def test_from_token_mock(mock_request):
    # This should not call the API
    assert isinstance(Client.from_token(url="some.url/api/v3", token="a-token"), Client)


def test_from_token_fake(mock_request):
    # This should not call the API
    assert isinstance(
        FakeClient.from_token(url="some.url/api/v3", token="a-token"), FakeClient
    )


def test_from_credentials_mock(mock_request, mock_scicat_url, user_token):
    client = Client.from_credentials(
        url=mock_scicat_url, username="someone", password="the-mock-does-not-care"
    )
    assert client._client._token == user_token


def test_from_credentials_fake(mock_request):
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


def test_get_orig_datablock_multi_not_supported(
    mock_request, mock_scicat_url, user_token, orig_datablock
):
    client = Client.from_token(url=mock_scicat_url, token=user_token)
    mock_request.get(
        f"{mock_scicat_url}/Datasets/dataset-id/origdatablocks"
        f"?access_token={user_token}",
        json=[
            orig_datablock.dict(exclude_none=True),
            orig_datablock.dict(exclude_none=True),
        ],
    )

    with pytest.raises(NotImplementedError):
        client.get_orig_datablock("dataset-id")


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


def test_create_first_orig_datablock(client, derived_dataset, ownable):
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
        **ownable.dict(),
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
