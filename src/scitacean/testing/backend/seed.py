# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 SciCat Project (https://github.com/SciCatProject/scitacean)

from copy import deepcopy
from typing import Dict, Optional, Union

from dateutil.parser import parse as parse_datetime

from ...client import Client
from ...model import (
    DownloadDataset,
    UploadDerivedDataset,
    UploadRawDataset,
    UploadTechnique,
)
from ..client import FakeClient
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


def _seed_with_real_client(
    client: Client,
    upload_datasets: Dict[str, Union[UploadRawDataset, UploadDerivedDataset]],
) -> Dict[str, DownloadDataset]:
    download_datasets = {
        key: client.scicat.create_dataset_model(dset)
        for key, dset in upload_datasets.items()
    }
    return download_datasets


def _seed_with_fake_client(
    fake_client: FakeClient,
    upload_datasets: Dict[str, Union[UploadRawDataset, UploadDerivedDataset]],
) -> Dict[str, DownloadDataset]:
    download_datasets = {
        key: fake_client.scicat.create_dataset_model(dset)
        for key, dset in upload_datasets.items()
    }
    return download_datasets


def seed_database(
    *, client: Optional[Client], fake_client: FakeClient, scicat_access: SciCatAccess
) -> None:
    upload_datasets = {
        key: _apply_config_dataset(dset, scicat_access.user)
        for key, dset in _DATASETS.items()
    }
    if client is not None:
        download_datasets = _seed_with_real_client(client, upload_datasets)
    else:
        download_datasets = _seed_with_fake_client(fake_client, upload_datasets)

    INITIAL_DATASETS.update(download_datasets)
