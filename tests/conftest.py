# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2022 Scowl contributors (https://github.com/SciCatProject/scowl)
# @author Jan-Lukas Wynen

from urllib.parse import urljoin

from pyscicat.client import ScicatClient
import pytest
import requests_mock


@pytest.fixture
def local_url() -> str:
    return "http://localhost:3000/api/v3/"


@pytest.fixture
def catamel_token() -> str:
    return "a_token"


@pytest.fixture
def mock_request(local_url, catamel_token):
    with requests_mock.Mocker() as mock:
        mock.post(
            urljoin(local_url, "Users/login"),
            json={"id": catamel_token},
        )
        yield mock


@pytest.fixture
def client(mock_request, local_url) -> ScicatClient:
    return ScicatClient(
        base_url=local_url,
        username="Zaphod",
        password="heartofgold",
    )
