# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 SciCat Project (https://github.com/SciCatProject/scitacean)

"""Wrappers for (Orig)Datablocks."""

from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING, Iterator, List, Optional, Union

from .file import File
from .model import DerivedDataset, OrigDatablock, RawDataset
from .pid import PID

if TYPE_CHECKING:
    from .dataset import Dataset

# TODO DatablockProxy


@dataclasses.dataclass
class OrigDatablockProxy:
    """Dataclass for an orig datablock.

    Instances of this class are mutable as opposed to
    :class:`scitacean.model.OrigDatablock`.
    They are used for building datasets and get converted to/from pydantic
    models for communication with a server.
    """

    _files: List[File] = dataclasses.field(init=False)
    _files_modified: bool = dataclasses.field(default=False, init=False)
    checksum_algorithm: Optional[str] = None
    pid: Optional[PID] = None
    owner_group: Optional[str] = None
    access_groups: Optional[List[str]] = None
    instrument_group: Optional[str] = None
    init_files: dataclasses.InitVar[Optional[List[File]]] = None

    def __post_init__(self, init_files: Optional[List[File]]) -> None:
        self._files = list(init_files) if init_files is not None else []

    @classmethod
    def from_model(
        cls,
        *,
        dataset_model: Union[DerivedDataset, RawDataset],
        orig_datablock_model: OrigDatablock,
    ) -> OrigDatablockProxy:
        """Construct a new OrigDatablockProxy from pydantic models.

        Parameters
        ----------
        dataset_model:
            Model of the dataset that this orig datablock belongs to.
        orig_datablock_model:
            Model of the orig datablock to construct.

        Returns
        -------
        :
            A new instance.
        """
        dblock = orig_datablock_model
        # TODO store checksum once implemented
        #   AND overwrite in Files
        return OrigDatablockProxy(
            pid=dblock.id,
            checksum_algorithm=None,
            owner_group=dblock.ownerGroup,
            access_groups=dblock.accessGroups,
            instrument_group=dblock.instrumentGroup,
            init_files=[File.from_scicat(file) for file in dblock.dataFileList],
        )

    @property
    def files(self) -> Iterator[File]:
        """Iterator over all files."""
        return iter(self._files)

    @property
    def size(self) -> int:
        """Total size of all files."""
        return sum(file.size for file in self.files)

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
        self._files_modified = True

    def make_model(self, dataset: Dataset) -> OrigDatablock:
        """Build a new pydantic model for this datablock.

        Parameters
        ----------
        dataset:
            The dataset that this orig datablock belongs to.

        Returns
        -------
        :
            A new model for this orig datablock.
        """
        # TODO set checksum_algorithm once implemented
        return OrigDatablock(
            id=self.pid,
            size=self.size,
            dataFileList=[file.make_model(for_archive=False) for file in self.files],
            datasetId=dataset.pid,
            ownerGroup=self.owner_group or dataset.owner_group,
            accessGroups=self.access_groups or dataset.access_groups,
            instrumentGroup=self.instrument_group or dataset.instrument_group,
        )
