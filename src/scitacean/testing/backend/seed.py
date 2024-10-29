# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 SciCat Project (https://github.com/SciCatProject/scitacean)

"""Initial contents of the SciCat testing backend.

The contents of this module are used to initialize
the local database before making it available to tests.
"""

import pickle
from copy import deepcopy
from pathlib import Path

from dateutil.parser import parse as parse_datetime

from ... import model
from ...client import Client
from ...filesystem import RemotePath
from ...model import (
    DatasetType,
    DownloadAttachment,
    DownloadDataset,
    DownloadOrigDatablock,
    UploadAttachment,
    UploadDataFile,
    UploadDerivedDataset,
    UploadOrigDatablock,
    UploadRawDataset,
    UploadTechnique,
)
from ...pid import PID
from ...thumbnail import Thumbnail
from .config import SITE, SciCatAccess, ScicatUser

# Dataset models to upload to the database.
_DATASETS: dict[str, UploadRawDataset | UploadDerivedDataset] = {
    "raw": UploadRawDataset(
        ownerGroup="PLACEHOLDER",
        accessGroups=["uu", "faculty"],
        classification="IN=medium,AV=low,CO=low",
        contactEmail="ponder.stibbons@uu.am",
        creationTime=parse_datetime("2004-06-13T01:45:28.100Z"),
        datasetName="My darkest magic yet",
        description="Doing some dark shit",
        isPublished=False,
        numberOfFilesArchived=0,
        owner="PLACEHOLDER",
        ownerEmail="PLACE@HOLD.ER",
        sourceFolder=RemotePath("/hex/data/123"),
        type=DatasetType.RAW,
        investigator="Ponder Stibbons",
        principalInvestigator="Ponder Stibbons",
        creationLocation=SITE,
        techniques=[UploadTechnique(pid="DM666", name="dark_magic")],
        scientificMetadata={
            "data_type": "event data",
            "temperature": {"value": "123", "unit": "K"},
            "weight": {"value": "42", "unit": "mg"},
        },
        usedSoftware=[],
        inputDatasets=[],
    ),
    "derived": UploadDerivedDataset(
        ownerGroup="PLACEHOLDER",
        accessGroups=["uu", "faculty"],
        classification="IN=medium,AV=low,CO=low",
        contactEmail="ponder.stibbons@uu.am",
        creationTime=parse_datetime("2005-11-04T13:37:44.002Z"),
        datasetName="Reprocessed dark magic",
        description="Making it even darker",
        isPublished=True,
        numberOfFilesArchived=0,
        owner="PLACEHOLDER",
        ownerEmail="PLACE@HOLD.ER",
        sourceFolder=RemotePath("/hex/data/dd"),
        type=DatasetType.DERIVED,
        investigator="Ponder Stibbons",
        inputDatasets=[],
        usedSoftware=["scitacean"],
        scientificMetadata={
            "data_type": "reduced",
            "pressure": {"value": "8.1", "unit": "Pa"},
        },
    ),
    "public": UploadRawDataset(
        ownerGroup="PLACEHOLDER",
        accessGroups=["uu"],
        classification="IN=medium,AV=low,CO=low",
        contactEmail="mustrum.ridcully69@uu.am",
        creationTime=parse_datetime("1998-11-05T23:00:42.000Z"),
        datasetName="Shoe counter",
        description="Got all these shoes!",
        isPublished=True,
        numberOfFilesArchived=0,
        owner="PLACEHOLDER",
        ownerEmail="PLACE@HOLD.ER",
        sourceFolder=RemotePath("/hex/secret/stuff"),
        type=DatasetType.RAW,
        investigator="Mustrum Ridcully",
        principalInvestigator="Mustrum Ridcully",
        creationLocation=SITE,
        techniques=[UploadTechnique(pid="S", name="shoes")],
        inputDatasets=[],
        usedSoftware=["scitacean"],
    ),
    "partially-broken": model.construct(
        UploadDerivedDataset,
        _strict_validation=False,
        _quiet=True,
        ownerGroup="PLACEHOLDER",
        accessGroups=["uu"],
        classification="IN=medium,AV=low,CO=low",
        contactEmail="owner@mail.com",
        orcidOfOwner="00-11-22-33",
        creationTime=parse_datetime("1998-11-05T23:00:42.000Z"),
        datasetName="Dataset with broken fields",
        description="Bad fields: orcidOfOwner, numberOfFiles, size",
        isPublished=False,
        numberOfFiles=-1,
        numberOfFilesArchived=0,
        owner="PLACEHOLDER",
        ownerEmail="PLACE@HOLD.ER",
        size=-10,
        sourceFolder=RemotePath("/remote/source"),
        type=DatasetType.DERIVED,
        investigator="who?!",
        inputDatasets=[],
        usedSoftware=["scitacean"],
    ),
}

# Orig datablocks to upload to the database.
_ORIG_DATABLOCKS: dict[str, list[UploadOrigDatablock]] = {
    "raw": [
        UploadOrigDatablock(
            size=619,
            chkAlg="md5",
            dataFileList=[
                UploadDataFile(
                    path="file1.txt",
                    size=300,
                    time=parse_datetime("2005-11-04T13:22:09.000Z"),
                    chk="97157d347fe9af920f5e61e96cf401cb",
                    gid="1000",
                    uid="1000",
                    perm="777",
                ),
                UploadDataFile(
                    path="sub/song.mp3",
                    size=319,
                    time=parse_datetime("2005-11-02T09:02:54.100Z"),
                    chk=None,
                    gid="1000",
                    uid="1000",
                    perm="777",
                ),
            ],
        )
    ],
    "derived": [
        UploadOrigDatablock(
            size=464,
            chkAlg="sha256",
            dataFileList=[
                UploadDataFile(
                    path="table.csv",
                    size=464,
                    time=parse_datetime("2005-10-31T00:00:01.000Z"),
                    chk="dddd8355da9105acabb9928196f022ca0581ffb73d8b89c891eb6f71477cb4cb",
                    gid="2000",
                    uid="0",
                    perm="656",
                ),
            ],
        )
    ],
    "public": [
        UploadOrigDatablock(
            size=64,
            chkAlg="md5",
            dataFileList=[
                UploadDataFile(
                    path="shoes",
                    size=64,
                    time=parse_datetime("1998-11-05T22:56:13.000Z"),
                    chk="95fe96bf90f6a53c1e20d6578e0d9e6e",
                    gid="0",
                    uid="0",
                    perm="0",
                ),
            ],
        )
    ],
}

_ATTACHMENTS: dict[str, list[UploadAttachment]] = {
    "derived": [
        UploadAttachment(
            caption="Process Overview",
            ownerGroup="PLACEHOLDER",
            accessGroups=["uu"],
            datasetId=PID(pid="PLACEHOLDER"),
            thumbnail=Thumbnail(mime="image/png", data=b"nag;aso;i"),
        ),
        UploadAttachment(
            caption="Pretty picture no 1",
            ownerGroup="PLACEHOLDER",
            accessGroups=["uu", "faculty"],
            datasetId=PID(pid="PLACEHOLDER"),
            thumbnail=Thumbnail(mime="image/jpeg", data=b"gj0ajs93jka2jv89a"),
            sampleId="kjsdf",
        ),
    ]
}

INITIAL_DATASETS: dict[str, DownloadDataset] = {}
"""Initial datasets in the testing database."""
INITIAL_ORIG_DATABLOCKS: dict[str, list[DownloadOrigDatablock]] = {}
"""Initial orig datablocks in the testing database."""
INITIAL_ATTACHMENTS: dict[str, list[DownloadAttachment]] = {}


def _apply_config_dataset(
    dset: UploadRawDataset | UploadDerivedDataset, user: ScicatUser
) -> UploadRawDataset | UploadDerivedDataset:
    dset = deepcopy(dset)
    dset.owner = user.username
    dset.ownerGroup = user.group
    dset.ownerEmail = user.email
    return dset


def _apply_config_attachment(
    attachment: UploadAttachment, user: ScicatUser
) -> UploadAttachment:
    attachment = deepcopy(attachment)
    attachment.ownerGroup = user.group
    return attachment


def _create_dataset_model(
    client: Client, dset: UploadRawDataset | UploadDerivedDataset
) -> DownloadDataset:
    uploaded = client.scicat.create_dataset_model(dset)
    # pid is a str if validation fails but we need a PID for fake clients.
    uploaded.pid = PID.parse(uploaded.pid)  # type: ignore[arg-type]
    return uploaded


def seed_database(*, client: Client, scicat_access: SciCatAccess) -> None:
    """Seed the database for testing.

    Uses the provided client to upload the datasets.
    Initializes ``INITIAL_DATASETS``, ``INITIAL_ORIG_DATABLOCKS``,
    and ``INITIAL_ATTACHMENTS`` with finalized datasets returned by the client.
    """
    upload_datasets = {
        key: _apply_config_dataset(dset, scicat_access.user)
        for key, dset in _DATASETS.items()
    }
    download_datasets = {
        key: _create_dataset_model(client, dset)
        for key, dset in upload_datasets.items()
    }
    INITIAL_DATASETS.update(download_datasets)

    download_orig_datablocks = {
        key: [
            client.scicat.create_orig_datablock(
                dblock,
                dataset_id=download_datasets[key].pid,  # type: ignore[arg-type]
            )
            for dblock in dblocks
        ]
        for key, dblocks in _ORIG_DATABLOCKS.items()
    }
    INITIAL_ORIG_DATABLOCKS.update(download_orig_datablocks)
    for key, dblocks in INITIAL_ORIG_DATABLOCKS.items():
        # Need to set these after uploading the datablocks to
        # make sure that the database has the correct values.
        INITIAL_DATASETS[key].numberOfFiles = sum(
            len(dblock.dataFileList or ()) for dblock in dblocks
        )
        INITIAL_DATASETS[key].size = sum(dblock.size or 0 for dblock in dblocks)

    upload_attachments = {
        key: [
            _apply_config_attachment(attachment, scicat_access.user)
            for attachment in attachments
        ]
        for key, attachments in _ATTACHMENTS.items()
    }
    download_attachments = {
        key: [
            client.scicat.create_attachment_for_dataset(
                attachment,
                dataset_id=download_datasets[key].pid,  # type: ignore[arg-type]
            )
            for attachment in attachments
        ]
        for key, attachments in upload_attachments.items()
    }
    INITIAL_ATTACHMENTS.update(download_attachments)


def save_seed(target_dir: Path) -> None:
    """Save the processed seed to a file."""
    with open(target_dir / "seed", "wb") as f:
        pickle.dump(
            {
                "datasets": INITIAL_DATASETS,
                "orig_datablocks": INITIAL_ORIG_DATABLOCKS,
                "attachments": INITIAL_ATTACHMENTS,
            },
            f,
        )


def seed_worker(target_dir: Path) -> None:
    """Load the processed seed from a file."""
    with open(target_dir / "seed", "rb") as f:
        loaded = pickle.load(f)  # noqa: S301
        INITIAL_DATASETS.update(loaded["datasets"])
        INITIAL_ORIG_DATABLOCKS.update(loaded["orig_datablocks"])
        INITIAL_ATTACHMENTS.update(loaded["attachments"])
