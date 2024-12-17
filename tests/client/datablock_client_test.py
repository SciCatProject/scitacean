# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 SciCat Project (https://github.com/SciCatProject/scitacean)
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
from scitacean.testing.backend import config as backend_config
from scitacean.testing.backend.seed import (
    INITIAL_ORIG_DATABLOCKS,
)


@pytest.fixture
def scicat_client(client: Client) -> ScicatClient:
    return client.scicat


@pytest.fixture
def derived_dataset(scicat_access: backend_config.SciCatAccess) -> UploadDerivedDataset:
    return UploadDerivedDataset(
        datasetName="Koelsche Lieder",
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


@pytest.fixture
def orig_datablock(scicat_access: backend_config.SciCatAccess) -> UploadOrigDatablock:
    # NOTE the placeholder!
    return UploadOrigDatablock(
        size=9235,
        dataFileList=[
            UploadDataFile(
                path="data.nxs", size=9235, time=parse_date("2023-08-18T13:52:33.000Z")
            )
        ],
    )


@pytest.mark.parametrize("key", ["raw", "derived"])
def test_get_orig_datablock(scicat_client: ScicatClient, key: str) -> None:
    dblock = INITIAL_ORIG_DATABLOCKS[key][0]
    downloaded = scicat_client.get_orig_datablocks(dblock.datasetId)
    assert downloaded == [dblock]


def test_create_first_orig_datablock(
    scicat_client: ScicatClient,
    derived_dataset: UploadDerivedDataset,
    orig_datablock: UploadOrigDatablock,
) -> None:
    uploaded = scicat_client.create_dataset_model(derived_dataset)
    scicat_client.create_orig_datablock(orig_datablock, dataset_id=uploaded.pid)
    [downloaded] = scicat_client.get_orig_datablocks(uploaded.pid)
    for key, expected in orig_datablock:
        # The database populates a number of fields that are orig_datablock in dset.
        # But we don't want to test those here as we don't want to test the database.
        if expected is not None and key != "dataFileList":
            assert dict(downloaded)[key] == expected, f"key = {key}"
    assert downloaded.accessGroups == derived_dataset.accessGroups
    assert downloaded.dataFileList is not None
    for i in range(len(orig_datablock.dataFileList)):
        for key, expected in orig_datablock.dataFileList[i]:
            assert (
                dict(downloaded.dataFileList[i])[key] == expected
            ), f"i = {i}, key = {key}"
