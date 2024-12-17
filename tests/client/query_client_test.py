# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 SciCat Project (https://github.com/SciCatProject/scitacean)

import pytest
from dateutil.parser import parse as parse_datetime

from scitacean import Client, DatasetType, RemotePath, model
from scitacean.testing.backend import skip_if_not_backend
from scitacean.testing.backend.config import SciCatAccess

UPLOAD_DATASETS: dict[str, model.UploadDerivedDataset | model.UploadRawDataset] = {
    "raw1": model.UploadRawDataset(
        ownerGroup="PLACEHOLDER",
        accessGroups=["uu", "faculty"],
        contactEmail="ponder.stibbons@uu.am",
        creationTime=parse_datetime("2004-06-13T01:45:28.100Z"),
        datasetName="dataset 1",
        numberOfFiles=0,
        numberOfFilesArchived=0,
        owner="PLACEHOLDER",
        sourceFolder=RemotePath("/hex/raw1"),
        type=DatasetType.RAW,
        principalInvestigator="investigator 1",
        creationLocation="UU",
        proposalId="p0124",
        inputDatasets=[],
        usedSoftware=["scitacean"],
    ),
    "raw2": model.UploadRawDataset(
        ownerGroup="PLACEHOLDER",
        accessGroups=["uu", "faculty"],
        contactEmail="ponder.stibbons@uu.am",
        creationTime=parse_datetime("2004-06-14T14:00:30Z"),
        datasetName="dataset 2",
        numberOfFiles=0,
        numberOfFilesArchived=0,
        owner="PLACEHOLDER",
        sourceFolder=RemotePath("/hex/raw2"),
        type=DatasetType.RAW,
        principalInvestigator="investigator 2",
        creationLocation="UU",
        proposalId="p0124",
        inputDatasets=[],
        usedSoftware=[],
    ),
    "raw3": model.UploadRawDataset(
        ownerGroup="PLACEHOLDER",
        accessGroups=["uu", "faculty"],
        contactEmail="ponder.stibbons@uu.am",
        creationTime=parse_datetime("2004-06-10T00:13:13Z"),
        datasetName="dataset 3",
        numberOfFiles=0,
        numberOfFilesArchived=0,
        owner="PLACEHOLDER",
        sourceFolder=RemotePath("/hex/raw3"),
        type=DatasetType.RAW,
        principalInvestigator="investigator 1",
        creationLocation="UU",
        proposalId="p0124",
        inputDatasets=[],
        usedSoftware=["scitacean"],
    ),
    "raw4": model.UploadRawDataset(
        ownerGroup="PLACEHOLDER",
        accessGroups=["uu", "faculty"],
        contactEmail="ponder.stibbons@uu.am",
        creationTime=parse_datetime("2005-11-03T21:56:02Z"),
        datasetName="dataset 1",
        numberOfFiles=0,
        numberOfFilesArchived=0,
        owner="PLACEHOLDER",
        sourceFolder=RemotePath("/hex/raw4"),
        type=DatasetType.RAW,
        principalInvestigator="investigator X",
        creationLocation="UU",
        inputDatasets=[],
        usedSoftware=[],
    ),
    "derived1": model.UploadDerivedDataset(
        ownerGroup="PLACEHOLDER",
        accessGroups=["uu", "faculty"],
        contactEmail="ponder.stibbons@uu.am",
        creationTime=parse_datetime("2004-10-02T08:47:33Z"),
        datasetName="dataset 1",
        numberOfFiles=0,
        numberOfFilesArchived=0,
        owner="PLACEHOLDER",
        sourceFolder=RemotePath("/hex/derived1"),
        type=DatasetType.DERIVED,
        investigator="investigator 1",
        inputDatasets=[],
        usedSoftware=["scitacean"],
    ),
    "derived2": model.UploadDerivedDataset(
        ownerGroup="PLACEHOLDER",
        accessGroups=["uu", "faculty"],
        contactEmail="ponder.stibbons@uu.am",
        creationTime=parse_datetime("2004-10-14T09:18:58Z"),
        datasetName="derived dataset 2",
        numberOfFiles=0,
        numberOfFilesArchived=0,
        owner="PLACEHOLDER",
        sourceFolder=RemotePath("/hex/derived2"),
        type=DatasetType.DERIVED,
        investigator="investigator 1",
        inputDatasets=[],
        usedSoftware=["scitacean"],
    ),
}
SEED = {}


@pytest.fixture(scope="module", autouse=True)
def _seed_database(request: pytest.FixtureRequest, scicat_access: SciCatAccess) -> None:
    skip_if_not_backend(request)

    client = Client.from_credentials(
        url=scicat_access.url,
        **scicat_access.user.credentials,
    )
    for key, dset in UPLOAD_DATASETS.items():
        dset.ownerGroup = scicat_access.user.group
        dset.owner = scicat_access.user.username
        SEED[key] = client.scicat.create_dataset_model(dset)


@pytest.mark.usefixtures("_seed_database")
def test_query_dataset_multiple_by_single_field(real_client: Client) -> None:
    datasets = real_client.scicat.query_datasets({"proposalIds": ["p0124"]})
    actual = {ds.pid: ds for ds in datasets}
    expected = {SEED[key].pid: SEED[key] for key in ("raw1", "raw2", "raw3")}
    assert actual == expected


@pytest.mark.usefixtures("_seed_database")
def test_query_dataset_no_match(real_client: Client) -> None:
    datasets = real_client.scicat.query_datasets({"owner": "librarian"})
    assert not datasets


@pytest.mark.usefixtures("_seed_database")
def test_query_dataset_multiple_by_multiple_fields(real_client: Client) -> None:
    datasets = real_client.scicat.query_datasets(
        {"proposalIds": ["p0124"], "principalInvestigator": "investigator 1"},
    )
    actual = {ds.pid: ds for ds in datasets}
    expected = {SEED[key].pid: SEED[key] for key in ("raw1", "raw3")}
    assert actual == expected


@pytest.mark.usefixtures("_seed_database")
def test_query_dataset_multiple_by_derived_field(real_client: Client) -> None:
    datasets = real_client.scicat.query_datasets(
        {"principalInvestigator": "investigator 1"}
    )
    actual = {ds.pid: ds for ds in datasets}
    expected = {
        SEED[key].pid: SEED[key] for key in ("derived1", "derived2", "raw1", "raw3")
    }
    assert actual == expected


@pytest.mark.usefixtures("_seed_database")
def test_query_dataset_uses_conjunction_of_fields(real_client: Client) -> None:
    datasets = real_client.scicat.query_datasets(
        {"proposalIds": ["p0124"], "principalInvestigator": "investigator X"},
    )
    assert not datasets


@pytest.mark.usefixtures("_seed_database")
def test_query_dataset_can_use_custom_type(real_client: Client) -> None:
    datasets = real_client.scicat.query_datasets(
        {"sourceFolder": RemotePath("/hex/raw4")},
    )
    expected = [SEED["raw4"]]
    assert datasets == expected


@pytest.mark.usefixtures("_seed_database")
def test_query_dataset_set_order(real_client: Client) -> None:
    datasets = real_client.scicat.query_datasets(
        {"proposalIds": ["p0124"]},
        order="creationTime:desc",
    )
    # This test uses a list to check the order
    expected = [SEED[key] for key in ("raw2", "raw1", "raw3")]
    assert datasets == expected


@pytest.mark.usefixtures("_seed_database")
def test_query_dataset_limit_ascending_creation_time(real_client: Client) -> None:
    datasets = real_client.scicat.query_datasets(
        {"proposalIds": "p0124"},
        limit=2,
        order="creationTime:asc",
    )
    actual = {ds.pid: ds for ds in datasets}
    expected = {SEED[key].pid: SEED[key] for key in ("raw1", "raw3")}
    assert actual == expected


@pytest.mark.usefixtures("_seed_database")
def test_query_dataset_limit_descending_creation_time(real_client: Client) -> None:
    datasets = real_client.scicat.query_datasets(
        {"proposalIds": ["p0124"]},
        limit=2,
        order="creationTime:desc",
    )
    actual = {ds.pid: ds for ds in datasets}
    expected = {SEED[key].pid: SEED[key] for key in ("raw1", "raw2")}
    assert actual == expected


@pytest.mark.usefixtures("_seed_database")
def test_query_dataset_limit_needs_order(real_client: Client) -> None:
    with pytest.raises(ValueError, match="limit"):
        real_client.scicat.query_datasets(
            {"proposalIds": ["p0124"]},
            limit=2,
        )


@pytest.mark.usefixtures("_seed_database")
def test_query_dataset_all(real_client: Client) -> None:
    datasets = real_client.scicat.query_datasets({})
    actual = {ds.pid: ds for ds in datasets}
    # We cannot test `datasets` directly because there are other datasets
    # in the database from other tests.
    for ds in SEED.values():
        assert actual[ds.pid] == ds
