# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 SciCat Project (https://github.com/SciCatProject/scitacean)

import pickle
from copy import deepcopy
from pathlib import Path
from typing import Dict, List, Optional, Union

from dateutil.parser import parse as parse_datetime

from ... import model
from ...client import Client
from ...model import (
    DownloadDataset,
    DownloadOrigDatablock,
    UploadDataFile,
    UploadDerivedDataset,
    UploadOrigDatablock,
    UploadRawDataset,
    UploadTechnique,
)
from ...pid import PID
from .config import SITE, SciCatAccess, SciCatUser

_DATASETS: Dict[str, Union[UploadRawDataset, UploadDerivedDataset]] = {
    "raw": UploadRawDataset(
        ownerGroup="PLACEHOLDER",
        accessGroups=["uu", "faculty"],
        classification="IN=medium,AV=low,CO=low",
        contactEmail="ponder.stibbons@uu.am",
        creationTime=parse_datetime("2004-06-13T01:45:28.100Z"),
        datasetName="My darkest magic yet",
        description="Doing some dark shit",
        isPublished=False,
        numberOfFiles=2,
        numberOfFilesArchived=0,
        owner="PLACEHOLDER",
        ownerEmail="PLACE@HOLD.ER",
        size=619,
        sourceFolder="/hex/data/123",
        type="raw",
        principalInvestigator="Ponder Stibbons",
        creationLocation=SITE,
        techniques=[UploadTechnique(pid="DM666", name="dark_magic")],
        scientificMetadata={
            "data_type": "event data",
            "temperature": {"value": "123", "unit": "K"},
            "weight": {"value": "42", "unit": "mg"},
        },
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
        numberOfFiles=1,
        numberOfFilesArchived=0,
        owner="PLACEHOLDER",
        ownerEmail="PLACE@HOLD.ER",
        size=464,
        sourceFolder="/hex/data/dd",
        type="derived",
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
        numberOfFiles=1,
        numberOfFilesArchived=0,
        owner="PLACEHOLDER",
        ownerEmail="PLACE@HOLD.ER",
        size=64,
        sourceFolder="/hex/secret/stuff",
        type="raw",
        principalInvestigator="Mustrum Ridcully",
        creationLocation=SITE,
        techniques=[UploadTechnique(pid="S", name="shoes")],
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
        sourceFolder="/remote/source",
        type="derived",
        investigator="who?!",
        inputDatasets=[],
        usedSoftware=["scitacean"],
    ),
}

_ORIG_DATABLOCKS: Dict[str, List[UploadOrigDatablock]] = {
    "raw": [
        UploadOrigDatablock(
            datasetId=PID(pid="PLACEHOLDER"),
            ownerGroup="PLACEHOLDER",
            size=619,
            accessGroups=["uu", "faculty"],
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
            datasetId=PID(pid="PLACEHOLDER"),
            ownerGroup="PLACEHOLDER",
            size=464,
            accessGroups=["uu", "faculty"],
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
            datasetId=PID(pid="PLACEHOLDER"),
            ownerGroup="PLACEHOLDER",
            size=64,
            accessGroups=["uu"],
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

INITIAL_DATASETS: Dict[str, DownloadDataset] = {}
INITIAL_ORIG_DATABLOCKS: Dict[str, List[DownloadOrigDatablock]] = {}


def _apply_config_dataset(
    dset: Union[UploadRawDataset, UploadDerivedDataset], user: SciCatUser
) -> Union[UploadRawDataset, UploadDerivedDataset]:
    dset = deepcopy(dset)
    dset.owner = user.username
    dset.ownerGroup = user.group
    dset.ownerEmail = user.email
    return dset


def _apply_config_orig_datablock(
    dblock: UploadOrigDatablock, dset: DownloadDataset, user: SciCatUser
) -> UploadOrigDatablock:
    dblock = deepcopy(dblock)
    dblock.ownerGroup = user.group
    dblock.datasetId = dset.pid
    return dblock


def _create_dataset_model(
    client: Client, dset: Union[UploadRawDataset, UploadDerivedDataset]
) -> DownloadDataset:
    uploaded = client.scicat.create_dataset_model(dset)
    # pid is a str if validation fails but we need a PID for fake clients.
    uploaded.pid = PID.parse(uploaded.pid)
    return uploaded


def seed_database(*, client: Optional[Client], scicat_access: SciCatAccess) -> None:
    """Seed the database for testing.

    Uses the provided client to upload the datasets.
    Initializes ``INITIAL_DATASETS`` and ``INITIAL_ORIG_DATABLOCKS``
    with finalized datasets returned by the client.
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

    upload_orig_datablocks = {
        key: [
            _apply_config_orig_datablock(
                dblock, download_datasets[key], scicat_access.user
            )
            for dblock in dblocks
        ]
        for key, dblocks in _ORIG_DATABLOCKS.items()
    }
    download_orig_datablocks = {
        key: [client.scicat.create_orig_datablock(dblock) for dblock in dblocks]
        for key, dblocks in upload_orig_datablocks.items()
    }
    INITIAL_ORIG_DATABLOCKS.update(download_orig_datablocks)


def save_seed(target_dir: Path) -> None:
    """Save the processed seed to a file."""
    with open(target_dir / "seed", "wb") as f:
        pickle.dump(
            {"datasets": INITIAL_DATASETS, "orig_datablocks": INITIAL_ORIG_DATABLOCKS},
            f,
        )


def seed_worker(target_dir: Path) -> None:
    """Load the processed seed from a file."""
    with open(target_dir / "seed", "rb") as f:
        loaded = pickle.load(f)
        INITIAL_DATASETS.update(loaded["datasets"])
        INITIAL_ORIG_DATABLOCKS.update(loaded["orig_datablocks"])
