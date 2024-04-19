# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 SciCat Project (https://github.com/SciCatProject/scitacean)
"""Common utilities for file transfers."""

from uuid import uuid4

from ..dataset import Dataset
from ..filesystem import RemotePath
from ..util.formatter import DatasetPathFormatter


def source_folder_for(dataset: Dataset, pattern: str | RemotePath | None) -> RemotePath:
    """Get or build the source folder for a dataset.

    Parameters
    ----------
    dataset:
        Build the source folder for this dataset.
    pattern:
        A string for constructing a source folder.
        Can have placeholders to be used by ``DatasetPathFormatter``.

    Returns
    -------
    :
        The source folder for the dataset.
    """
    if pattern is None:
        if dataset.source_folder is None:
            raise ValueError(
                "Cannot determine source_folder for dataset. "
                "Either the dataset's source_folder or the "
                "file transfer's source_folder must be set."
            )
        return dataset.source_folder

    if isinstance(pattern, RemotePath):
        pattern = pattern.posix
    return RemotePath(
        DatasetPathFormatter().format(pattern, dset=dataset, uid=str(uuid4()))
    )
