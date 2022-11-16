import uuid

from pyscicat.model import DerivedDataset, RawDataset
import pytest
from scitacean import Client

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
        creationTime="2000-01-01T01:01:01.000Z",
        inputDatasets=["input1"],
        investigator="investigator",
        isPublished=None,  # override default value in model
        owner="owner",
        ownerGroup="ownerGroup",
        sourceFolder="/source/folder",
        usedSoftware=["software1"],
    )
    pid = client.scicat.create_dataset_model(dset)
    finalized = client.scicat.get_dataset_model(pid)

    # Inputs
    assert finalized.accessGroups == ["access1"]
    assert finalized.contactEmail == "contact@email.com"
    assert finalized.creationTime == "2000-01-01T01:01:01.000Z"
    assert finalized.inputDatasets == ["input1"]
    assert finalized.investigator == "investigator"
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
    assert finalized.isPublished is False
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
        creationTime="2000-01-01T01:01:01.000Z",
        isPublished=None,  # override default value in model
        owner="owner",
        ownerGroup="ownerGroup",
        principalInvestigator="investigator",
        sourceFolder="/source/folder",
    )
    pid = client.scicat.create_dataset_model(dset)
    finalized = client.scicat.get_dataset_model(pid)

    # Inputs
    assert finalized.accessGroups == ["access1"]
    assert finalized.contactEmail == "contact@email.com"
    assert finalized.creationTime == "2000-01-01T01:01:01.000Z"
    assert finalized.owner == "owner"
    assert finalized.ownerGroup == "ownerGroup"
    assert finalized.principalInvestigator == "investigator"
    assert finalized.sourceFolder == "/source/folder"

    # Default values
    assert finalized.createdAt  # some non-empty str
    assert finalized.createdBy  # some non-empty str
    assert finalized.classification  # some non-empty str
    assert finalized.datasetName  # some non-empty str
    assert finalized.history == []
    assert finalized.isPublished is False
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
        createdAt="2001-01-01T01:01:01.000Z",
        createdBy="creator",
        creationTime="2000-01-01T01:01:01.000Z",
        datasetName="datasetName",
        description="description",
        history=[
            DerivedDataset(
                accessGroups=["access1"],
                contactEmail="contact@email.com",
                creationTime="2000-01-01T01:01:01.000Z",
                inputDatasets=["input1"],
                investigator="investigator",
                owner="owner",
                ownerGroup="ownerGroup",
                sourceFolder="/source/folder",
                usedSoftware=["software1"],
            ).dict()
        ],
        inputDatasets=["input1"],
        instrumentId="instrument-id",
        investigator="investigator",
        isPublished=True,
        jobParameters={"tiredness": "great"},
        jobLogData="all-good",
        keywords=["keyword1"],
        license="the-license",
        numberOfFiles=123,
        numberOfFilesArchived=42,
        orcidOfOwner="owners'-orcid",
        owner="owner",
        ownerEmail="owner@email.eu",
        ownerGroup="ownerGroup",
        packedSize=551,
        pid=f"derived-id-{uuid.uuid4()}",
        scientificMetadata={"sci1": ["data1"]},
        sharedWith=["shared1"],
        size=6123,
        sourceFolder="/source/folder",
        sourceFolderHost="/host/source/folder",
        techniques=[{"name": "technique1", "pid": "technique1-id"}],
        updatedAt="2001-01-01T01:01:01.000Z",
        usedSoftware=["software1"],
        validationStatus="not-validated",
        version="9999.00.888",
    )
    pid = client.scicat.create_dataset_model(dset)
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
        createdAt="2001-01-01T01:01:01.000Z",
        createdBy="creator",
        creationLocation="the-realverse",
        creationTime="2000-01-01T01:01:01.000Z",
        dataFormat="data-format",
        datasetName="datasetName",
        description="description",
        endTime="2010-01-01T01:01:01.000Z",
        history=[
            RawDataset(
                accessGroups=["access1"],
                contactEmail="contact@email.com",
                creationTime="2000-01-01T01:01:01.000Z",
                owner="owner",
                ownerGroup="ownerGroup",
                principalInvestigator="investigator",
                sourceFolder="/source/folder",
            ).dict()
        ],
        instrumentId="instrument-id",
        isPublished=True,
        keywords=["keyword1"],
        license="the-license",
        numberOfFiles=123,
        numberOfFilesArchived=42,
        orcidOfOwner="owners'-orcid",
        owner="owner",
        ownerEmail="owner@email.eu",
        ownerGroup="ownerGroup",
        packedSize=551,
        pid=f"derived-id-{uuid.uuid4()}",
        principalInvestigator="investigator",
        proposalId="proposal-id",
        sampleId="sample-id",
        scientificMetadata={"sci1": ["data1"]},
        sharedWith=["shared1"],
        size=6123,
        sourceFolder="/source/folder",
        sourceFolderHost="/host/source/folder",
        techniques=[{"name": "technique1", "pid": "technique1-id"}],
        updatedAt="2001-01-01T01:01:01.000Z",
        validationStatus="not-validated",
        version="9999.00.888",
    )
    pid = client.scicat.create_dataset_model(dset)
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
