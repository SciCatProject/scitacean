# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 SciCat Project (https://github.com/SciCatProject/scitacean)
# mypy: disable-error-code="arg-type"

import pytest
from dateutil.parser import parse as parse_date

from scitacean import Client
from scitacean.client import ScicatClient
from scitacean.model import (
    DatasetType,
    UploadDataFile,
    UploadDerivedDataset,
    UploadOrigDatablock,
)
from scitacean.testing.backend.seed import (
    INITIAL_ORIG_DATABLOCKS,
)


@pytest.fixture()
def scicat_client(client: Client) -> ScicatClient:
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
        ownerGroup=scicat_access.user.group,
        accessGroups=["group1", "2nd_group"],
    )


@pytest.mark.parametrize("key", ("raw", "derived"))
def test_get_orig_datablock(scicat_client, key):
    dblock = INITIAL_ORIG_DATABLOCKS[key][0]
    downloaded = scicat_client.get_orig_datablocks(dblock.datasetId)
    assert downloaded == [dblock]


def test_create_first_orig_datablock(scicat_client, derived_dataset, orig_datablock):
    uploaded = scicat_client.create_dataset_model(derived_dataset)
    orig_datablock.datasetId = uploaded.pid
    scicat_client.create_orig_datablock(orig_datablock)
    downloaded = scicat_client.get_orig_datablocks(uploaded.pid)
    assert len(downloaded) == 1
    downloaded = downloaded[0]
    for key, expected in orig_datablock:
        # The database populates a number of fields that are orig_datablock in dset.
        # But we don't want to test those here as we don't want to test the database.
        if expected is not None and key != "dataFileList":
            assert expected == dict(downloaded)[key], f"key = {key}"
    for i in range(len(orig_datablock.dataFileList)):
        for key, expected in orig_datablock.dataFileList[i]:
            assert (
                expected == dict(downloaded.dataFileList[i])[key]
            ), f"i = {i}, key = {key}"
