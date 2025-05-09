# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 SciCat Project (https://github.com/SciCatProject/scitacean)
"""Main dataset structure."""

from __future__ import annotations

import dataclasses
import itertools
import os
from collections import Counter
from collections.abc import Generator, Iterable
from datetime import datetime, timezone
from typing import Any, Literal, TypeVar

from ._base_model import convert_download_to_user_model, convert_user_to_upload_model
from ._dataset_fields import DatasetBase
from .datablock import OrigDatablock
from .file import File
from .model import (
    Attachment,
    DatasetType,
    DownloadAttachment,
    DownloadDataset,
    DownloadOrigDatablock,
    UploadAttachment,
    UploadDerivedDataset,
    UploadOrigDatablock,
    UploadRawDataset,
)
from .pid import PID
from .thumbnail import Thumbnail

_T = TypeVar("_T")


class Dataset(DatasetBase):
    """Metadata and linked data files for a measurement, simulation, or analysis."""

    @classmethod
    def from_download_models(
        cls,
        dataset_model: DownloadDataset,
        orig_datablock_models: list[DownloadOrigDatablock],
        attachment_models: Iterable[DownloadAttachment] | None = None,
    ) -> Dataset:
        """Construct a new dataset from SciCat download models.

        Parameters
        ----------
        dataset_model:
            Model of the dataset.
        orig_datablock_models:
            List of all associated original datablock models for the dataset.
        attachment_models:
            List of all associated attachment models for the dataset.
            Use ``None`` if the attachments were not downloaded.
            Use an empty list if the attachments were downloaded, but there aren't any.

        Returns
        -------
        :
            A new Dataset instance.
        """
        init_args, read_only = DatasetBase._prepare_fields_from_download(dataset_model)
        dset = cls(**init_args)
        for key, val in read_only.items():
            setattr(dset, key, val)
        dset._attachments = convert_download_to_user_model(  # type: ignore[assignment]
            attachment_models
        )
        if orig_datablock_models is not None:
            dset._orig_datablocks.extend(
                map(OrigDatablock.from_download_model, orig_datablock_models)
            )
        return dset

    @classmethod
    def fields(
        cls,
        dataset_type: DatasetType | Literal["derived", "raw"] | None = None,
        read_only: bool | None = None,
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
        eq = (
            eq
            and self._orig_datablocks == other._orig_datablocks
            and self._attachments == other._attachments
        )
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
    def files(self) -> tuple[File, ...]:
        """Files linked with the dataset."""
        return tuple(
            itertools.chain.from_iterable(
                dblock.files for dblock in self._orig_datablocks
            )
        )

    @property
    def attachments(self) -> list[Attachment] | None:
        """List of attachments for this dataset.

        This property can be in two distinct 'falsy' states:

        - ``dset.attachments is None``: It is unknown whether there are attachments.
          This happens when datasets are downloaded without downloading the attachments.
        - ``dset.attachments == []``: It is known that there are no attachments.
          This happens either when downloading datasets or when initializing datasets
          locally without assigning attachments.
        """
        return self._attachments

    @attachments.setter
    def attachments(self, attachments: list[Attachment] | None) -> None:
        """List of attachments for this dataset.

        See the docs of the getter for an explanation of ``None`` vs ``[]``.
        It is unlikely that you ever need to set the attachments to ``None``.
        """
        self._attachments = attachments

    def add_attachment(
        self,
        thumbnail: str | os.PathLike[str] | Thumbnail | None = None,
        *,
        caption: str,
        owner_group: str | None = None,
        access_groups: list[str] | None = None,
        instrument_group: str | None = None,
        proposal_id: str | None = None,
        sample_id: str | None = None,
    ) -> None:
        """Create a new attachment and add it to the dataset.

        Parameters
        ----------
        thumbnail:
            If a :class:`scitacean.thumbnail.Thumbnail` object, it is added to the
            attachment. If a string or path, a thumbnail is loaded from that path.
        caption:
            Caption of the attachment.
        owner_group:
            Owner group of the attachment. Defaults to ``self.owner_group``.
        access_groups:
            Access groups of the attachment. Defaults to ``self.access_groups``.
        instrument_group:
            Instrument group of the attachment. Defaults to ``self.instrument_group``.
        proposal_id:
            Proposal ID of the attachment. Defaults to ``self.proposal_id``.
        sample_id:
            Sample ID of the attachment. Defaults to ``self.sample_id``.
        """
        if self.attachments is None:
            raise ValueError(
                "The attachments have not been initialized. This likely means "
                "that you did not download them from SciCat."
            )

        owner = _select_non_none_value(owner_group, self.owner_group)
        if owner is None:
            raise ValueError("Cannot add attachments without owner group")
        access = _select_non_none_value(access_groups, self.access_groups)
        instrument = _select_non_none_value(instrument_group, self.instrument_group)
        proposal = _select_non_none_value(proposal_id, self.proposal_id)
        sample = _select_non_none_value(sample_id, self.sample_id)

        match thumbnail:
            case None:
                thumb = None
            case Thumbnail() as t:
                thumb = t
            case path:
                thumb = Thumbnail.load_file(path)

        self.attachments.append(
            Attachment(
                thumbnail=thumb,
                caption=caption,
                owner_group=owner,
                access_groups=access,
                instrument_group=instrument,
                proposal_id=proposal,
                sample_id=sample,
            )
        )

    def add_files(self, *files: File, datablock: int | str | PID | None = None) -> None:
        """Add files to the dataset.

        Parameters
        ----------
        files:
            File object to add.
        datablock:
            Advanced feature, do not set unless you know what this is!

            Select the orig datablock to store the file in.

            - ``None``: Use the last datablock in the list if possible
              or add a new one if needed.
            - If an ``int``, use the datablock with that index.
            - If a ``str`` or ``PID``, use the datablock with that id;
              if there is none with matching id, raise ``KeyError``.
        """
        _deny_conflicting_files(files, self._orig_datablocks)
        db = self._get_or_add_orig_datablock(
            datablock, (file.checksum_algorithm for file in files)
        )
        db.add_files(*files)

    def add_local_files(
        self,
        *paths: str | os.PathLike[str],
        datablock: int | str | PID | None = None,
    ) -> None:
        """Add files on the local file system to the dataset.

        The files are set up to be uploaded to the dataset's source folder without
        preserving the local directory structure.
        That is, given

        .. code-block::

            dataset.source_folder = "remote/source"
            dataset.add_local_files("/path/to/file1", "other_path/file2")

        and uploading this dataset to SciCat, the files will be uploaded to::

            remote/source/file1
            remote/source/file2

        Parameters
        ----------
        paths:
            Local paths to the files.
        datablock:
            Advanced feature, do not set unless you know what this is!

            Select the orig datablock to store the file in.

            - ``None``: Use the last datablock in the list if possible
              or add a new one if needed.
            - If an ``int``, use the datablock with that index.
            - If a ``str`` or ``PID``, use the datablock with that id;
              if there is none with matching id, raise ``KeyError``.
        """
        self.add_files(
            *(File.from_local(path) for path in paths),
            datablock=datablock,
        )

    def replace(
        self,
        *,
        _read_only: dict[str, Any] | None = None,
        _orig_datablocks: list[OrigDatablock] | None = None,
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

        def get_val(source: dict[str, Any], name: str) -> Any:
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
        attachments = get_val(replacements, "attachments")
        meta = get_val(replacements, "meta")

        if replacements or _read_only:
            raise TypeError(
                f"Invalid arguments: {', '.join((*replacements, *_read_only))}"
            )
        dset = Dataset(
            **kwargs,
            meta=meta,
        )
        dset._orig_datablocks.extend(
            _orig_datablocks if _orig_datablocks is not None else self._orig_datablocks
        )
        dset._attachments = list(attachments) if attachments is not None else None
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

    def add_orig_datablock(self, *, checksum_algorithm: str | None) -> OrigDatablock:
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
            checksum_algorithm=checksum_algorithm,
        )
        self._orig_datablocks.append(dblock)
        return dblock

    def _get_existing_orig_datablock(self, key: int | str | PID) -> OrigDatablock:
        if isinstance(key, str | PID):
            try:
                return next(
                    db for db in self._orig_datablocks if db.datablock_id == key
                )
            except StopIteration:
                raise KeyError(f"No OrigDatablock with id {key}") from None
        return self._orig_datablocks[key]

    def _get_or_add_orig_datablock(
        self, key: int | str | PID | None, checksum_algorithms: Iterable[str | None]
    ) -> OrigDatablock:
        if algorithms := set(checksum_algorithms) - {None}:
            checksum_algorithm = algorithms.pop()
        else:
            checksum_algorithm = None

        if key is None:
            if self._orig_datablocks:
                last = self._orig_datablocks[-1]
                if (
                    checksum_algorithm is None
                    or checksum_algorithm == last.checksum_algorithm
                ):
                    return last
            return self.add_orig_datablock(
                checksum_algorithm=checksum_algorithm
                or self._default_checksum_algorithm
            )

        existing = self._get_existing_orig_datablock(key)
        if (
            checksum_algorithm is not None
            and existing.checksum_algorithm != checksum_algorithm
        ):
            raise ValueError(
                "Cannot add files, the checksum algorithm does not match the given "
                "data block. Either choose a different algorithm or a different block."
            )
        return existing

    def make_upload_model(self) -> UploadDerivedDataset | UploadRawDataset:
        """Construct a SciCat upload model from self."""
        model: type[UploadRawDataset | UploadDerivedDataset] = (
            UploadRawDataset if self.type == DatasetType.RAW else UploadDerivedDataset
        )
        # Datablocks are not included here because they are handled separately
        # by make_datablock_upload_models and their own endpoints.
        special = ("relationships", "techniques", "input_datasets", "used_software")
        return model(
            numberOfFiles=self.number_of_files,
            numberOfFilesArchived=self.number_of_files_archived,
            size=self.size,
            packedSize=self.packed_size,
            scientificMetadata=self._meta or None,
            techniques=convert_user_to_upload_model(  # type: ignore[arg-type]
                self.techniques
            ),
            relationships=convert_user_to_upload_model(  # type: ignore[arg-type]
                self.relationships
            ),
            inputDatasets=self.input_datasets or [],
            usedSoftware=self.used_software or [],
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
                dblock.make_upload_model() for dblock in self._orig_datablocks
            ]
        )

    def make_attachment_upload_models(self) -> list[UploadAttachment]:
        """Build models for all registered attachments.

        Raises
        ------
        ValueError
            If ``self.attachments`` is ``None``,
            i.e., the attachments are uninitialized.

        Returns
        -------
        :
            List of attachment models.
        """
        if self.attachments is None:
            raise ValueError(
                "Cannot make upload models for attachments because "
                "the attachments are uninitialized."
            )
        return [a.make_upload_model() for a in self.attachments]

    def validate(self) -> None:
        """Validate the fields of the dataset.

        Raises :class:`pydantic.ValidationError` if validation fails.
        Returns normally if it passes.
        """
        self.make_upload_model()

    def keys(self) -> Iterable[str]:
        """Dict-like keys(names of fields) method.

        Returns
        -------
        :
            Generator of names of all fields corresponding to ``self.type``
            and other fields that are not ``None``.


        .. versionadded:: 23.10.0
        """
        from itertools import chain

        all_fields = {field.name for field in self.fields()}
        my_fields = {field.name for field in self.fields(dataset_type=self.type)}
        other_fields = all_fields - my_fields
        invalid_fields = (
            f_name for f_name in other_fields if getattr(self, f_name) is not None
        )

        return chain(my_fields, invalid_fields)

    def values(self) -> Iterable[Any]:
        """Dict-like values(values of fields) method.

        Returns
        -------
        :
            Generator of values of all fields corresponding to ``self.type``
            and other fields that are not ``None``.


        .. versionadded:: 23.10.0
        """
        return (getattr(self, field_name) for field_name in self.keys())

    def items(self) -> Iterable[tuple[str, Any]]:
        """Dict-like items(name and value pairs of fields) method.

        Returns
        -------
        :
            Generator of (Name, Value) pairs of all fields
            corresponding to ``self.type``
            and other fields that are not ``None``.


        .. versionadded:: 23.10.0
        """
        return ((key, getattr(self, key)) for key in self.keys())

    @classmethod
    def _validate_field_name(cls, field_name: str) -> None:
        """Validate ``field_name``.

        If ``field_name`` is a ``name`` of any
        :class:`DatasetBase.Field` objects in ``self.fields()``.

        Parameters
        ----------
        field_name:
            Name of the field to validate.

        Raises
        ------
        KeyError
            If validation fails.
        """
        if field_name not in (field.name for field in cls.fields()):
            raise KeyError(f"{field_name} is not a valid field name.")

    def __getitem__(self, field_name: str) -> Any:
        """Dict-like get-item method.

        Parameters
        ----------
        field_name:
            Name of the field to retrieve.

        Returns
        -------
        :
            Value of the field with the name ``field_name``.

        Raises
        ------
        :
            :class:`KeyError` if ``field_name`` does not mach any names of fields.


        .. versionadded:: 23.10.0
        """
        self._validate_field_name(field_name)
        return getattr(self, field_name)

    def __setitem__(self, field_name: str, field_value: Any) -> None:
        """Dict-like set-item method.

        Set the value of the field with name ``field_name`` as ``field_value``.

        Parameters
        ----------
        field_name:
            Name of the field to set.

        field_value:
            Value of the field to set.

        Raises
        ------
        :
            :class:`KeyError` if ``field_name`` does not mach any names of fields.


        .. versionadded:: 23.10.0
        """
        self._validate_field_name(field_name)
        setattr(self, field_name, field_value)


@dataclasses.dataclass
class DatablockUploadModels:
    """Pydantic models for (orig) datablocks."""

    # TODO
    # datablocks: Optional[List[UploadDatablock]]
    orig_datablocks: list[UploadOrigDatablock] | None
    """Orig datablocks"""


def _deny_conflicting_files(
    files: tuple[File, ...], orig_datablocks: list[OrigDatablock]
) -> None:
    _deny_conflicting_file_names(files, orig_datablocks)
    _deny_conflicting_file_checksum_algorithms(files, orig_datablocks)


def _deny_conflicting_file_names(
    files: tuple[File, ...], orig_datablocks: list[OrigDatablock]
) -> None:
    names = Counter(f.remote_path.posix for f in files)
    duplicates = [name for name, count in names.items() if count > 1]
    if duplicates:
        raise ValueError(f"Duplicate file names: {duplicates!r}")

    for db in orig_datablocks:
        names.update(Counter(f.remote_path.posix for f in db.files))
    duplicates = [name for name, count in names.items() if count > 1]
    if duplicates:
        raise ValueError(
            f"Cannot add files with names {duplicates!r} because "
            "they already exist in the dataset."
        )


def _deny_conflicting_file_checksum_algorithms(
    files: tuple[File, ...], orig_datablocks: list[OrigDatablock]
) -> None:
    algorithms = {file.checksum_algorithm for file in files} - {None}
    if len(algorithms) > 1:
        raise ValueError(
            "Cannot add files with different checksum algorithms."
            "Either use the same algorithm for all or add the files to separate "
            "data blocks by calling `dataset.add_files` separately for each data block."
            f" Got algorithms {algorithms!r}."
        )


def _select_non_none_value(a: _T | None, b: _T | None) -> _T | None:
    match (a, b):
        case (None, None):
            return None
        case (None, x):
            return x
        case (x, None):
            return x
        case (x, _):  # Prefer a over b
            return x
    return None  #  This should be unreachable but Mypy complains without it.
