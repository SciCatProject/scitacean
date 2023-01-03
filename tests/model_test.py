# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 SciCat Project (https://github.com/SciCatProject/scitacean)
import uuid

import pytest
from dateutil.parser import parse as parse_date

from scitacean import PID, Client, DatasetType
from scitacean.model import DerivedDataset, RawDataset, Technique

from .common.backend import skip_if_not_backend


@pytest.fixture
def client(
    request,
    scicat_access,
    scicat_backend,
):
    skip_if_not_backend(request)
    return Client.from_credentials(
        url=scicat_access.url, **scicat_access.functional_credentials
    )


def test_derived_dataset_default_values(client):
    dset = DerivedDataset(
        accessGroups=["access1"],
        contactEmail="contact@email.com",
        creationTime=parse_date("2000-01-01T01:01:01.000Z"),
        inputDatasets=[PID(prefix="PID.SAMPLE.PREFIX", pid="abcd")],
        investigator="inv@esti.gator",
        owner="owner",
        ownerGroup="ownerGroup",
        sourceFolder="/source/folder",
        usedSoftware=["software1"],
        type=DatasetType.DERIVED,
    )
    pid = client.scicat.create_dataset_model(dset).pid
    finalized = client.scicat.get_dataset_model(pid)

    # Inputs
    assert finalized.accessGroups == ["access1"]
    assert finalized.contactEmail == "contact@email.com"
    assert finalized.creationTime == parse_date("2000-01-01T01:01:01.000Z")
    assert finalized.inputDatasets == [PID(prefix="PID.SAMPLE.PREFIX", pid="abcd")]
    assert finalized.investigator == "inv@esti.gator"
    assert finalized.owner == "owner"
    assert finalized.ownerGroup == "ownerGroup"
    assert finalized.sourceFolder == "/source/folder"
    assert finalized.usedSoftware == ["software1"]

    # Default values
    assert finalized.createdAt  # some non-empty str
    assert finalized.createdBy  # some non-empty str
    assert finalized.classification  # some non-empty str
    assert finalized.datasetName  # some non-empty str
    assert finalized.history == []
    assert finalized.isPublished is None
    assert finalized.pid  # some non-empty str
    assert finalized.techniques == []
    assert finalized.updatedAt  # some non-empty str
    assert finalized.version  # some non-empty str

    # Left empty
    assert finalized.description is None is None
    assert finalized.instrumentId is None
    assert finalized.jobParameters is None
    assert finalized.jobLogData is None
    assert finalized.keywords is None
    assert finalized.license is None
    assert finalized.numberOfFiles is None
    assert finalized.numberOfFilesArchived is None
    assert finalized.orcidOfOwner is None
    assert finalized.ownerEmail is None
    assert finalized.packedSize is None
    assert finalized.scientificMetadata is None
    assert finalized.sharedWith is None
    assert finalized.size is None
    assert finalized.sourceFolderHost is None
    assert finalized.validationStatus is None


def test_raw_dataset_default_values(client):
    dset = RawDataset(
        accessGroups=["access1"],
        contactEmail="contact@email.com",
        creationTime=parse_date("2000-01-01T01:01:01.000Z"),
        owner="owner",
        ownerGroup="ownerGroup",
        principalInvestigator="inv@esti.gator",
        sourceFolder="/source/folder",
        type=DatasetType.RAW,
    )
    pid = client.scicat.create_dataset_model(dset).pid
    finalized = client.scicat.get_dataset_model(pid)

    # Inputs
    assert finalized.accessGroups == ["access1"]
    assert finalized.contactEmail == "contact@email.com"
    assert finalized.creationTime == parse_date("2000-01-01T01:01:01.000Z")
    assert finalized.owner == "owner"
    assert finalized.ownerGroup == "ownerGroup"
    assert finalized.principalInvestigator == "inv@esti.gator"
    assert finalized.sourceFolder == "/source/folder"

    # Default values
    assert finalized.createdAt  # some non-empty str
    assert finalized.createdBy  # some non-empty str
    assert finalized.classification  # some non-empty str
    assert finalized.datasetName  # some non-empty str
    assert finalized.history == []
    assert finalized.isPublished is None
    assert finalized.pid  # some non-empty str
    assert finalized.techniques == []
    assert finalized.updatedAt  # some non-empty str
    assert finalized.version  # some non-empty str

    # Left empty
    assert finalized.creationLocation is None
    assert finalized.dataFormat is None
    assert finalized.description is None
    assert finalized.endTime is None
    assert finalized.instrumentId is None
    assert finalized.keywords is None
    assert finalized.license is None
    assert finalized.numberOfFiles is None
    assert finalized.numberOfFilesArchived is None
    assert finalized.orcidOfOwner is None
    assert finalized.ownerEmail is None
    assert finalized.packedSize is None
    assert finalized.proposalId is None
    assert finalized.sampleId is None
    assert finalized.scientificMetadata is None
    assert finalized.sharedWith is None
    assert finalized.size is None
    assert finalized.sourceFolderHost is None
    assert finalized.validationStatus is None


def test_derived_dataset_overwritten_values(client):
    dset = DerivedDataset(
        accessGroups=["access1"],
        classification="classes",
        contactEmail="contact@email.com",
        createdAt=parse_date("2001-01-01T01:01:01.000Z"),
        createdBy="creator",
        creationTime=parse_date("2000-01-01T01:01:01.000Z"),
        datasetName="datasetName",
        description="description",
        history=[
            DerivedDataset(
                accessGroups=["access1"],
                contactEmail="contact@email.com",
                creationTime=parse_date("2000-01-01T01:01:01.000Z"),
                inputDatasets=[PID(prefix="PID.SAMPLE.PREFIX", pid="abcd")],
                investigator="inv@esti.gator",
                owner="owner",
                ownerGroup="ownerGroup",
                sourceFolder="/source/folder",
                usedSoftware=["software1"],
                type=DatasetType.DERIVED,
            ).dict()
        ],
        inputDatasets=[PID(prefix="PID.SAMPLE.PREFIX", pid="abcd")],
        instrumentId="instrument-id",
        investigator="inv@esti.gator",
        isPublished=True,
        jobParameters={"tiredness": "great"},
        jobLogData="all-good",
        keywords=["keyword1"],
        license="the-license",
        numberOfFiles=123,
        numberOfFilesArchived=42,
        orcidOfOwner="https://orcid.org/0000-0002-3761-3201",
        owner="owner",
        ownerEmail="owner@email.eu",
        ownerGroup="ownerGroup",
        packedSize=551,
        pid=PID(pid=f"derived-id-{uuid.uuid4()}"),
        scientificMetadata={"sci1": ["data1"]},
        sharedWith=["shared1"],
        size=6123,
        sourceFolder="/source/folder",
        sourceFolderHost="/host/source/folder",
        techniques=[Technique(name="technique1", pid="technique1-id")],
        type=DatasetType.DERIVED,
        updatedAt=parse_date("2001-01-01T01:01:01.000Z"),
        usedSoftware=["software1"],
        validationStatus="not-validated",
        version="9999.00.888",
    )
    pid = client.scicat.create_dataset_model(dset).pid
    finalized = client.scicat.get_dataset_model(pid)

    preserved_inputs = [
        "accessGroups",
        "classification",
        "contactEmail",
        "creationTime",
        "datasetName",
        "description",
        "inputDatasets",
        "instrumentId",
        "investigator",
        "isPublished",
        "jobParameters",
        "jobLogData",
        "keywords",
        "license",
        "numberOfFiles",
        "numberOfFilesArchived",
        "orcidOfOwner",
        "owner",
        "ownerEmail",
        "ownerGroup",
        "packedSize",
        "scientificMetadata",
        "sharedWith",
        "size",
        "sourceFolder",
        "sourceFolderHost",
        "techniques",
        "usedSoftware",
        "validationStatus",
    ]

    overwritten_inputs = ["createdAt", "createdBy", "updatedAt", "pid", "version"]

    for key in preserved_inputs:
        assert getattr(finalized, key) == getattr(dset, key)
    for key in overwritten_inputs:
        assert getattr(finalized, key) != getattr(dset, key)
    assert finalized.history == []  # This is a new dataset, so the history is empty.


def test_raw_dataset_overwritten_values(client):
    dset = RawDataset(
        accessGroups=["access1"],
        classification="classes",
        contactEmail="contact@email.com",
        createdAt=parse_date("2001-01-01T01:01:01.000Z"),
        createdBy="creator",
        creationLocation="the-realverse",
        creationTime=parse_date("2000-01-01T01:01:01.000Z"),
        dataFormat="data-format",
        datasetName="datasetName",
        description="description",
        endTime=parse_date("2010-01-01T01:01:01.000Z"),
        history=[
            RawDataset(
                accessGroups=["access1"],
                contactEmail="contact@email.com",
                creationTime=parse_date("2000-01-01T01:01:01.000Z"),
                owner="owner",
                ownerGroup="ownerGroup",
                principalInvestigator="inv@esti.gator",
                sourceFolder="/source/folder",
                type=DatasetType.RAW,
            ).dict()
        ],
        instrumentId="instrument-id",
        isPublished=True,
        keywords=["keyword1"],
        license="the-license",
        numberOfFiles=123,
        numberOfFilesArchived=42,
        orcidOfOwner="https://orcid.org/0000-0002-3761-3201",
        owner="owner",
        ownerEmail="owner@email.eu",
        ownerGroup="ownerGroup",
        packedSize=551,
        pid=PID(pid=f"derived-id-{uuid.uuid4()}"),
        principalInvestigator="inv@esti.gator",
        proposalId="proposal-id",
        sampleId="sample-id",
        scientificMetadata={"sci1": ["data1"]},
        sharedWith=["shared1"],
        size=6123,
        sourceFolder="/source/folder",
        sourceFolderHost="/host/source/folder",
        techniques=[Technique(name="technique1", pid="technique1-id")],
        type=DatasetType.RAW,
        updatedAt=parse_date("2001-01-01T01:01:01.000Z"),
        validationStatus="not-validated",
        version="9999.00.888",
    )
    pid = client.scicat.create_dataset_model(dset).pid
    finalized = client.scicat.get_dataset_model(pid)

    preserved_inputs = [
        "accessGroups",
        "classification",
        "contactEmail",
        "creationLocation",
        "creationTime",
        "dataFormat",
        "datasetName",
        "description",
        "endTime",
        "instrumentId",
        "isPublished",
        "keywords",
        "license",
        "numberOfFiles",
        "numberOfFilesArchived",
        "orcidOfOwner",
        "owner",
        "ownerEmail",
        "ownerGroup",
        "packedSize",
        "principalInvestigator",
        "proposalId",
        "sampleId",
        "scientificMetadata",
        "sharedWith",
        "size",
        "sourceFolder",
        "sourceFolderHost",
        "techniques",
        "validationStatus",
    ]

    overwritten_inputs = ["createdAt", "createdBy", "updatedAt", "pid", "version"]

    for key in preserved_inputs:
        assert getattr(finalized, key) == getattr(dset, key)
    for key in overwritten_inputs:
        assert getattr(finalized, key) != getattr(dset, key)
    assert finalized.history == []  # This is a new dataset, so the history is empty.
