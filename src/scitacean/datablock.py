# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 SciCat Project (https://github.com/SciCatProject/scitacean)

"""Wrappers for (Orig)Datablocks."""

from __future__ import annotations

import dataclasses
from collections.abc import Iterable, Iterator
from datetime import datetime

from .file import File
from .model import DownloadOrigDatablock, UploadOrigDatablock

# TODO Datablock


@dataclasses.dataclass
class OrigDatablock:
    """Dataclass for an orig datablock.

    Instances of this class are mutable as opposed to
    :class:`scitacean.model.OrigDatablock`.
    They are used for building datasets and get converted to/from pydantic
    models for communication with a server.
    """

    _files: list[File] = dataclasses.field(init=False)
    checksum_algorithm: str | None = None
    init_files: dataclasses.InitVar[Iterable[File] | None] = None
    _access_groups: list[str] | None = None
    _created_at: datetime | None = None
    _created_by: str | None = None
    _id: str | None = None
    _is_published: bool | None = None
    _updated_at: datetime | None = None
    _updated_by: str | None = None

    def __post_init__(self, init_files: Iterable[File] | None) -> None:
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
            checksum_algorithm=dblock.chkAlg,
            _access_groups=dblock.accessGroups,
            _created_at=dblock.createdAt,
            _created_by=dblock.createdBy,
            _id=orig_datablock_model.id,
            _is_published=orig_datablock_model.isPublished,
            _updated_at=dblock.updatedAt,
            _updated_by=dblock.updatedBy,
            init_files=[
                File.from_download_model(file, checksum_algorithm=dblock.chkAlg)
                for file in dblock.dataFileList or ()
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
    def access_groups(self) -> list[str] | None:
        """Access groups for this datablock."""
        return self._access_groups

    @property
    def created_at(self) -> datetime | None:
        """Creation time of this orig datablock."""
        return self._created_at

    @property
    def created_by(self) -> str | None:
        """User who created this orig datablock."""
        return self._created_by

    @property
    def updated_at(self) -> datetime | None:
        """Last update time of this orig datablock."""
        return self._updated_at

    @property
    def updated_by(self) -> str | None:
        """User who last updated this datablock."""
        return self._updated_by

    @property
    def datablock_id(self) -> str | None:
        """ID of this datablock."""
        return self._id

    @property
    def is_published(self) -> bool | None:
        """Return whether the datablock is public on SciCat."""
        return self._is_published

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

    def make_upload_model(self) -> UploadOrigDatablock:
        """Build a new pydantic model to upload this datablock.

        Returns
        -------
        :
            A new model for this orig datablock.
        """
        return UploadOrigDatablock(
            chkAlg=self.checksum_algorithm,
            size=self.size,
            dataFileList=[file.make_model(for_archive=False) for file in self.files],
        )
