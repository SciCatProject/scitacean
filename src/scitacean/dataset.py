# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 SciCat Project (https://github.com/SciCatProject/scitacean)
"""Main dataset structure."""

from __future__ import annotations

import dataclasses
import itertools
from datetime import datetime, timezone
from pathlib import Path
from typing import (
    Any,
    Dict,
    Generator,
    Iterable,
    List,
    Literal,
    Optional,
    Tuple,
    Type,
    Union,
)

from ._dataset_fields import DatasetBase
from .datablock import OrigDatablock
from .file import File
from .model import (
    BaseUserModel,
    DatasetType,
    DownloadDataset,
    DownloadOrigDatablock,
    Relationship,
    Technique,
    UploadDerivedDataset,
    UploadOrigDatablock,
    UploadRawDataset,
)
from .pid import PID


class Dataset(DatasetBase):
    @classmethod
    def from_download_models(
        cls,
        dataset_model: DownloadDataset,
        orig_datablock_models: List[DownloadOrigDatablock],
    ) -> Dataset:
        """Construct a new dataset from SciCat download models.

        Parameters
        ----------
        dataset_model:
            Model of the dataset.
        orig_datablock_models:
            List of all associated original datablock models for the dataset.

        Returns
        -------
        :
            A new Dataset instance.
        """
        init_args, read_only = DatasetBase._prepare_fields_from_download(dataset_model)
        for mod, key in ((Technique, "techniques"), (Relationship, "relationships")):
            init_args[key] = _list_field_from_download(mod, init_args[key])
        dset = cls(**init_args)
        for key, val in read_only.items():
            setattr(dset, key, val)
        if orig_datablock_models is not None:
            dset._orig_datablocks.extend(
                map(OrigDatablock.from_download_model, orig_datablock_models)
            )
        return dset

    @classmethod
    def fields(
        cls,
        dataset_type: Optional[Union[DatasetType, Literal["derived", "raw"]]] = None,
        read_only: Optional[bool] = None,
    ) -> Generator[Dataset.Field, None, None]:
        """Iterate over dataset fields.

        This is similar to :func:`dataclasses.fields`.

        Parameters
        ----------
        dataset_type:
            If set, return only the fields for this dataset type.
            If unset, do not filter fields.
        read_only:
            If true or false, return only fields which are read-only
            or allow write-access, respectively.
            If unset, do not filter fields.

        Returns
        -------
        :
            Iterable over the fields of datasets.
        """
        it = iter(DatasetBase._FIELD_SPEC)
        if dataset_type is not None:
            attr = (
                "used_by_derived"
                if dataset_type == DatasetType.DERIVED
                else "used_by_raw"
            )
            it = filter(lambda field: getattr(field, attr), it)
        if read_only is not None:
            it = filter(lambda field: field.read_only == read_only, it)
        yield from it

    def __str__(self) -> str:
        args = ", ".join(
            f"{field.name}={value}"
            for field in self.fields()
            if (value := getattr(self, field.name)) is not None
        )
        return f"Dataset({args})"

    def _repr_html_(self) -> str:
        # Import here to prevent cycle.
        from ._html_repr import dataset_html_repr

        return dataset_html_repr(self)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Dataset):
            return False
        eq = all(
            getattr(self, field.name) == getattr(other, field.name)
            for field in Dataset.fields()
        )
        eq = eq and self._orig_datablocks == other._orig_datablocks
        return eq

    @property
    def number_of_files(self) -> int:
        """Number of files in directly accessible storage in the dataset.

        This includes files on both the local and remote filesystems.

        Corresponds to OrigDatablocks.
        """
        return sum(len(tuple(dblock.files)) for dblock in self._orig_datablocks)

    @property
    def number_of_files_archived(self) -> int:
        """Total number of archived files in the dataset.

        Corresponds to Datablocks.
        """
        return 0

    @property
    def packed_size(self) -> int:
        """Total size of all datablock package files created for this dataset."""
        return 0

    @property
    def size(self) -> int:
        """Total size of files in directly accessible storage in the dataset.

        This includes files on both the local and remote filesystems.

        Corresponds to OrigDatablocks.
        """
        return sum(file.size for file in self.files)

    @property
    def files(self) -> Tuple[File, ...]:
        """Files linked with the dataset."""
        return tuple(
            itertools.chain.from_iterable(
                dblock.files for dblock in self._orig_datablocks
            )
        )

    def add_files(self, *files: File, datablock: Union[int, str, PID] = -1) -> None:
        """Add files to the dataset."""
        self._get_or_add_orig_datablock(datablock).add_files(*files)

    def add_local_files(
        self,
        *paths: Union[str, Path],
        base_path: Union[str, Path] = "",
        datablock: Union[int, str] = -1,
    ) -> None:
        """Add files on the local file system to the dataset.

        Parameters
        ----------
        paths:
            Local paths to the files.
        base_path:
            The remote paths will be set up according to

            ``remotes = [path.relative_to(base_path) for path in paths]``.
        datablock:
            Advanced feature, do not set unless you know what this is!

            Select the orig datablock to store the file in.
            If an ``int``, use the datablock with that index.
            If a ``str`` or ``PID``, use the datablock with that id;
            if there is none with matching id, raise ``KeyError``.
        """
        self.add_files(
            *(File.from_local(path, base_path=base_path) for path in paths),
            datablock=datablock,
        )

    def replace(
        self,
        *,
        _read_only: Optional[Dict[str, Any]] = None,
        _orig_datablocks: Optional[List[OrigDatablock]] = None,
        **replacements: Any,
    ) -> Dataset:
        """Return a new dataset with replaced fields.

        Parameters starting with an underscore are for internal use.
        Using them may result in a broken dataset.

        Parameters
        ----------
        replacements:
            New field values.

        Returns
        -------
        :
            The new dataset has the same fields as the input but all fields given
            as keyword arguments are replaced by the given values.
        """
        _read_only = _read_only or {}

        def get_val(source: Dict[str, Any], name: str) -> Any:
            try:
                return source.pop(name)
            except KeyError:
                return getattr(self, name)

        read_only = {
            field.name: get_val(_read_only, field.name)
            for field in Dataset.fields(read_only=True)
        }
        DatasetBase._convert_readonly_fields_in_place(read_only)
        kwargs = {
            **{
                field.name: get_val(replacements, field.name)
                for field in Dataset.fields(read_only=False)
            },
        }
        if replacements or _read_only:
            raise TypeError(
                f"Invalid arguments: {', '.join((*replacements, *_read_only))}"
            )
        dset = Dataset(
            **kwargs,
        )
        dset._orig_datablocks.extend(
            _orig_datablocks if _orig_datablocks is not None else self._orig_datablocks
        )
        for key, val in read_only.items():
            setattr(dset, "_" + key, val)
        return dset

    def as_new(self) -> Dataset:
        """Return a new dataset with lifecycle-related fields erased.

        The returned dataset has the same fields as ``self``.
        But fields that indicate when the dataset was created or
        by who are set to ``None``.
        This if, for example, ``created_at``, ``history``, and ``lifecycle``.

        Returns
        -------
        :
            A new dataset without lifecycle-related fields.
        """
        return self.replace(
            _read_only={field.name: None for field in Dataset.fields(read_only=True)},
            creation_time=datetime.now(tz=timezone.utc),
        )

    def derive(
        self,
        *,
        keep: Iterable[str] = (
            "contact_email",
            "investigator",
            "orcid_of_owner",
            "owner",
            "owner_email",
            "techniques",
        ),
    ) -> Dataset:
        """Return a new dataset that is derived from self.

        The returned dataset has most fields set to ``None``.
        But a number of fields can be carried over from ``self``.
        By default, this assumes that the owner of the derived dataset is the same
        as the owner of the original.
        This can be customized with the ``keep`` argument.

        Parameters
        ----------
        keep:
            Fields to copy over to the derived dataset.

        Returns
        -------
        :
            A new derived dataset.

        Raises
        ------
        ValueError
            If ``self`` has no PID.
            The derived dataset requires a PID in order to link back to ``self``.
        """
        if self.pid is None:
            raise ValueError("Cannot make a derived datasets because self.pid is None.")
        return Dataset(
            type=DatasetType.DERIVED,
            input_datasets=[self.pid],
            creation_time=datetime.now(tz=timezone.utc),
            **{name: getattr(self, name) for name in keep},
        )

    def replace_files(self, *files: File) -> Dataset:
        """Return a new dataset with replaced files.

        For each argument, if the input dataset has a file with the
        same remote path, that file is replaced.
        Otherwise, a new file is added.
        Other existing files are kept in the returned dataset.

        Parameters
        ----------
        files:
            New files for the dataset.

        Returns
        -------
        :
            A new dataset with given files.
        """

        def new_or_old(old: File) -> File:
            for new in files:
                if old.remote_path == new.remote_path:
                    return new
            return old

        return self.replace(
            _orig_datablocks=[
                dataclasses.replace(dblock, init_files=map(new_or_old, dblock.files))
                for dblock in self._orig_datablocks
            ]
        )

    def add_orig_datablock(self, *, checksum_algorithm: Optional[str]) -> OrigDatablock:
        """Append a new orig datablock to the list of orig datablocks.

        Parameters
        ----------
        checksum_algorithm:
            Use this algorithm to compute checksums of files
            associated with this datablock.

        Returns
        -------
        :
            The newly added datablock.
        """
        dblock = OrigDatablock(
            checksum_algorithm=checksum_algorithm, _dataset_id=self.pid
        )
        self._orig_datablocks.append(dblock)
        return dblock

    def _lookup_orig_datablock(self, id_: str) -> OrigDatablock:
        try:
            return next(db for db in self._orig_datablocks if db.datablock_id == id_)
        except StopIteration:
            raise KeyError(f"No OrigDatablock with id {id_}") from None

    def _get_or_add_orig_datablock(self, key: Union[int, str]) -> OrigDatablock:
        if isinstance(key, str):
            return self._lookup_orig_datablock(key)
        # The 0th datablock is implicitly always there and created on demand.
        if key in (0, -1) and not self._orig_datablocks:
            return self.add_orig_datablock(
                checksum_algorithm=self._default_checksum_algorithm
            )
        return self._orig_datablocks[key]

    def make_upload_model(self) -> Union[UploadDerivedDataset, UploadRawDataset]:
        """Construct a SciCat upload model from self."""
        model = (
            UploadRawDataset if self.type == DatasetType.RAW else UploadDerivedDataset
        )
        # Datablocks are not included here because they are handled separately
        # by make_datablock_upload_models and their own endpoints.
        special = ("relationships", "techniques")
        return model(
            numberOfFiles=self.number_of_files,
            numberOfFilesArchived=self.number_of_files_archived,
            size=self.size,
            packedSize=self.packed_size,
            scientificMetadata=self._meta or None,
            techniques=_list_field_for_upload(self.techniques),
            relationships=_list_field_for_upload(self.relationships),
            **{
                field.scicat_name: value
                for field in self.fields()
                if field.name not in special
                and (value := getattr(self, field.name)) is not None
            },
        )

    def make_datablock_upload_models(self) -> DatablockUploadModels:
        """Build models for all contained (orig) datablocks.

        Returns
        -------
        :
            Structure with datablock and orig datablock models.
        """
        if self.number_of_files == 0:
            return DatablockUploadModels(orig_datablocks=None)
        return DatablockUploadModels(
            orig_datablocks=[
                dblock.make_upload_model(self) for dblock in self._orig_datablocks
            ]
        )

    def validate(self) -> None:
        """Validate the fields of the dataset.

        Raises :class:`pydantic.ValidationError` if validation fails.
        Returns normally if it passes.
        """
        self.make_upload_model()


@dataclasses.dataclass
class DatablockUploadModels:
    """Pydantic models for (orig) datablocks."""

    # TODO
    # datablocks: Optional[List[UploadDatablock]]
    orig_datablocks: Optional[List[UploadOrigDatablock]]
    """Orig datablocks"""


def _list_field_for_upload(value: Optional[List[Any]]) -> Optional[List[Any]]:
    if value is None:
        return None
    return [item.make_upload_model() for item in value]


def _list_field_from_download(
    mod: Type[BaseUserModel], value: Optional[List[Any]]
) -> Optional[List[Any]]:
    if value is None:
        return None
    return [mod.from_download_model(item) for item in value]
