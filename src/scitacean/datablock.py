# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 SciCat Project (https://github.com/SciCatProject/scitacean)

"""Wrappers for (Orig)Datablocks."""

from __future__ import annotations

import dataclasses
from datetime import datetime
from typing import TYPE_CHECKING, Iterable, Iterator, List, Optional

from .file import File
from .model import DownloadOrigDatablock, UploadOrigDatablock
from .pid import PID

if TYPE_CHECKING:
    from .dataset import Dataset

# TODO Datablock


@dataclasses.dataclass
class OrigDatablock:
    """Dataclass for an orig datablock.

    Instances of this class are mutable as opposed to
    :class:`scitacean.model.OrigDatablock`.
    They are used for building datasets and get converted to/from pydantic
    models for communication with a server.
    """

    _files: List[File] = dataclasses.field(init=False)
    checksum_algorithm: Optional[str] = None
    access_groups: Optional[List[str]] = None
    instrument_group: Optional[str] = None
    owner_group: Optional[str] = None
    init_files: dataclasses.InitVar[Optional[Iterable[File]]] = None
    _created_at: Optional[datetime] = None
    _created_by: Optional[str] = None
    _dataset_id: Optional[PID] = None
    _id: Optional[str] = None
    _updated_at: Optional[datetime] = None
    _updated_by: Optional[str] = None

    def __post_init__(self, init_files: Optional[Iterable[File]]) -> None:
        self._files = list(init_files) if init_files is not None else []

    @classmethod
    def from_download_model(
        cls,
        orig_datablock_model: DownloadOrigDatablock,
    ) -> OrigDatablock:
        """Construct a new OrigDatablock from pydantic models.

        Parameters
        ----------
        orig_datablock_model:
            Model of the orig datablock to construct.

        Returns
        -------
        :
            A new instance.
        """
        dblock = orig_datablock_model
        return OrigDatablock(
            checksum_algorithm=None,
            owner_group=dblock.ownerGroup,
            access_groups=dblock.accessGroups,
            instrument_group=dblock.instrumentGroup,
            _created_at=dblock.createdAt,
            _created_by=dblock.createdBy,
            _dataset_id=orig_datablock_model.datasetId,
            _id=orig_datablock_model.id,
            _updated_at=dblock.updatedAt,
            _updated_by=dblock.updatedBy,
            init_files=[
                File.from_scicat(file, checksum_algorithm=orig_datablock_model.chkAlg)
                for file in dblock.dataFileList
            ],
        )

    @property
    def files(self) -> Iterator[File]:
        """Iterator over all files."""
        return iter(self._files)

    @property
    def size(self) -> int:
        """Total size of all files."""
        return sum(file.size for file in self.files)

    @property
    def created_at(self) -> Optional[datetime]:
        """Creation time of this orig datablock."""
        return self._created_at

    @property
    def created_by(self) -> Optional[str]:
        """User who created this orig datablock."""
        return self._created_by

    @property
    def updated_at(self) -> Optional[datetime]:
        """Last update time of this orig datablock."""
        return self._updated_at

    @property
    def updated_by(self) -> Optional[str]:
        """User who last updated this datablock."""
        return self._updated_by

    @property
    def dataset_id(self) -> PID:
        """PID of the dataset this datablock belongs to."""
        return self._dataset_id

    @property
    def datablock_id(self) -> Optional[str]:
        """ID of this datablock."""
        return self._id

    def add_files(self, *files: File) -> None:
        """Append files to the datablock.

        Parameters
        ----------
        files:
            File objects to add.
        """
        self._files.extend(
            dataclasses.replace(f, checksum_algorithm=self.checksum_algorithm)
            for f in files
        )

    def make_upload_model(self, dataset: Dataset) -> UploadOrigDatablock:
        """Build a new pydantic model to upload this datablock.

        Parameters
        ----------
        dataset:
            The dataset that this orig datablock belongs to.

        Returns
        -------
        :
            A new model for this orig datablock.
        """
        return UploadOrigDatablock(
            chkAlg=self.checksum_algorithm,
            size=self.size,
            dataFileList=[file.make_model(for_archive=False) for file in self.files],
            datasetId=dataset.pid,
            ownerGroup=self.owner_group or dataset.owner_group,
            accessGroups=self.access_groups or dataset.access_groups,
            instrumentGroup=self.instrument_group or dataset.instrument_group,
        )
