# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 SciCat Project (https://github.com/SciCatProject/scitacean)

from typing import cast

import pytest

from scitacean import PID, Client, RemotePath, model
from scitacean.testing.backend import seed

pytestmark = pytest.mark.skip(
    "Querying is currently broken because of a mismatch between DTOs and schemas."
)


@pytest.fixture
def client(real_client: Client, require_scicat_backend: None) -> Client:
    assert real_client is not None
    return real_client


def get_seed(*keys: str) -> dict[PID, model.DownloadDataset]:
    keys = tuple(f"query-{key}" for key in keys)
    return {
        cast(PID, seed.INITIAL_DATASETS[key].pid): seed.INITIAL_DATASETS[key]
        for key in keys
    }


def test_query_dataset_multiple_by_single_field(client: Client) -> None:
    datasets = client.scicat.query_datasets({"proposalIds": ["p0124"]})
    actual = {ds.pid: ds for ds in datasets}
    expected = get_seed("raw1", "raw2", "raw3")
    assert actual == expected


def test_query_dataset_no_match(client: Client) -> None:
    datasets = client.scicat.query_datasets({"owner": "librarian"})
    assert not datasets


def test_query_dataset_multiple_by_multiple_fields(client: Client) -> None:
    datasets = client.scicat.query_datasets(
        {"proposalIds": ["p0124"], "principalInvestigator": "investigator 1"},
    )
    actual = {ds.pid: ds for ds in datasets}
    expected = get_seed("raw1", "raw3")
    assert actual == expected


def test_query_dataset_multiple_by_derived_field(client: Client) -> None:
    datasets = client.scicat.query_datasets({"principalInvestigator": "investigator 1"})
    actual = {ds.pid: ds for ds in datasets}
    expected = get_seed("derived1", "derived2", "raw1", "raw3")
    assert actual == expected


def test_query_dataset_uses_conjunction_of_fields(client: Client) -> None:
    datasets = client.scicat.query_datasets(
        {"proposalIds": ["p0124"], "principalInvestigator": "investigator X"},
    )
    assert not datasets


def test_query_dataset_can_use_custom_type(client: Client) -> None:
    datasets = client.scicat.query_datasets(
        {"sourceFolder": RemotePath("/hex/raw4")},
    )
    expected = [seed.INITIAL_DATASETS["query-raw4"]]
    assert datasets == expected


def test_query_dataset_set_order(client: Client) -> None:
    datasets = client.scicat.query_datasets(
        {"proposalIds": ["p0124"]},
        order="creationTime:desc",
    )
    # This test uses a list to check the order
    expected = [
        seed.INITIAL_DATASETS[key] for key in ("query-raw2", "query-raw1", "query-raw3")
    ]
    assert datasets == expected


def test_query_dataset_limit_ascending_creation_time(client: Client) -> None:
    datasets = client.scicat.query_datasets(
        {"proposalIds": "p0124"},
        limit=2,
        order="creationTime:asc",
    )
    actual = {ds.pid: ds for ds in datasets}
    expected = get_seed("raw1", "raw3")
    assert actual == expected


def test_query_dataset_limit_descending_creation_time(client: Client) -> None:
    datasets = client.scicat.query_datasets(
        {"proposalIds": ["p0124"]},
        limit=2,
        order="creationTime:desc",
    )
    actual = {ds.pid: ds for ds in datasets}
    expected = get_seed("raw1", "raw2")
    assert actual == expected


def test_query_dataset_limit_needs_order(client: Client) -> None:
    with pytest.raises(ValueError, match="limit"):
        client.scicat.query_datasets(
            {"proposalIds": ["p0124"]},
            limit=2,
        )


def test_query_dataset_all(client: Client) -> None:
    # Need a high limit to make sure we get all expected datasets because
    # other tests may upload additional datasets.
    datasets = client.scicat.query_datasets({}, limit=1000, order="creationTime:asc")
    actual = {ds.pid: ds for ds in datasets}
    # We cannot test `datasets` directly because there are other datasets
    # in the database from other tests.
    reference = [
        seed.INITIAL_DATASETS[key]
        for key in (
            "query-raw1",
            "query-raw2",
            "query-raw3",
            "query-raw4",
            "query-derived1",
            "query-derived2",
        )
    ]
    for ds in reference:
        actual[ds.pid].updatedAt = ds.updatedAt
        assert actual[ds.pid] == ds
