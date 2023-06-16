# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 SciCat Project (https://github.com/SciCatProject/scitacean)

import pickle
from copy import deepcopy
from pathlib import Path
from typing import Dict, Optional, Union

from dateutil.parser import parse as parse_datetime

from ...client import Client
from ...model import (
    DownloadDataset,
    UploadDerivedDataset,
    UploadRawDataset,
    UploadTechnique,
)
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
}

INITIAL_DATASETS: Dict[str, DownloadDataset] = {}


def _apply_config_dataset(
    dset: Union[UploadRawDataset, UploadDerivedDataset], user: SciCatUser
) -> Union[UploadRawDataset, UploadDerivedDataset]:
    dset = deepcopy(dset)
    dset.owner = user.username
    dset.ownerGroup = user.group
    dset.ownerEmail = user.email
    return dset


def seed_database(*, client: Optional[Client], scicat_access: SciCatAccess) -> None:
    """Seed the database for testing.

    Uses the provided client to upload the datasets.
    Initializes ``INITIAL_DATASETS`` with finalized datasets returned by the client.
    """
    upload_datasets = {
        key: _apply_config_dataset(dset, scicat_access.user)
        for key, dset in _DATASETS.items()
    }
    download_datasets = {
        key: client.scicat.create_dataset_model(dset)
        for key, dset in upload_datasets.items()
    }

    INITIAL_DATASETS.update(download_datasets)
    # TODO datablocks


def save_seed(target_dir: Path) -> None:
    """Save the processed seed to a file."""
    with open(target_dir / "seed", "wb") as f:
        pickle.dump(INITIAL_DATASETS, f)


def seed_worker(target_dir: Path) -> None:
    """Load the processed seed from a file."""
    with open(target_dir / "seed", "rb") as f:
        INITIAL_DATASETS.update(pickle.load(f))
