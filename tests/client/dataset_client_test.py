# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 SciCat Project (https://github.com/SciCatProject/scitacean)
# mypy: disable-error-code="arg-type, index"

import pydantic
import pytest
from dateutil.parser import parse as parse_date

from scitacean import PID, Client, RemotePath, ScicatCommError
from scitacean.client import ScicatClient
from scitacean.model import (
    DatasetType,
    UploadDerivedDataset,
)
from scitacean.testing.backend.seed import (
    INITIAL_DATASETS,
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


@pytest.mark.parametrize("key", ("raw", "derived"))
def test_get_dataset_model(scicat_client, key):
    dset = INITIAL_DATASETS[key]
    downloaded = scicat_client.get_dataset_model(dset.pid)
    # The backend may update the dataset after upload.
    # We cannot easily predict when that happens.
    downloaded.updatedAt = dset.updatedAt
    assert downloaded == dset


def test_get_dataset_model_bad_id(scicat_client):
    with pytest.raises(ScicatCommError):
        scicat_client.get_dataset_model(PID(pid="bad-pid"))


def test_create_dataset_model(scicat_client, derived_dataset):
    finalized = scicat_client.create_dataset_model(derived_dataset)
    downloaded = scicat_client.get_dataset_model(finalized.pid)
    for key, expected in finalized:
        # The database populates a number of fields that are None in dset.
        # But we don't want to test those here as we don't want to test the database.
        if expected is not None:
            assert expected == dict(downloaded)[key], f"key = {key}"


def test_validate_dataset_model(real_client, require_scicat_backend, derived_dataset):
    real_client.scicat.validate_dataset_model(derived_dataset)
    derived_dataset.contactEmail = "NotAnEmail"
    with pytest.raises(ValueError):
        real_client.scicat.validate_dataset_model(derived_dataset)


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
