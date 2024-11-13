# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 SciCat Project (https://github.com/SciCatProject/scitacean)

"""Types and functions to implement models for communication with SciCat."""

from __future__ import annotations

import dataclasses
from collections.abc import Iterable
from datetime import datetime
from typing import (
    Any,
    ClassVar,
    TypeVar,
    overload,
)

import pydantic
from dateutil.parser import parse as parse_datetime

from ._internal.orcid import is_valid_orcid
from .logging import get_logger

try:
    # Python 3.11+
    from enum import StrEnum

    class DatasetType(StrEnum):
        """Type of Dataset."""

        RAW = "raw"
        DERIVED = "derived"

    del StrEnum

except ImportError:
    from enum import Enum

    class DatasetType(str, Enum):  # type: ignore[no-redef]
        """Enum representing the type of datasets."""

        RAW = "raw"
        DERIVED = "derived"

    del Enum


class BaseModel(pydantic.BaseModel):
    """Base class for Pydantic models for communication with SciCat."""

    model_config = pydantic.ConfigDict(
        extra="forbid",
    )

    _user_mask: ClassVar[tuple[str, ...]]
    _masked_fields: ClassVar[tuple[str, ...] | None] = None

    # Some schemas contain fields that we don't want to use in Scitacean.
    # Normally, omitting them from the model would result in an error when
    # building a model from the JSON returned by SciCat.
    # The following subclass hook allows models to mark fields as masked.
    # Those will be silently dropped by __init__.
    # Note also the comment for _IGNORED_KWARGS below.
    def __init_subclass__(
        cls, /, masked: Iterable[str] | None = None, **kwargs: Any
    ) -> None:
        super().__init_subclass__(**kwargs)
        cls._user_mask = tuple(masked) if masked is not None else ()

    def __init__(self, **kwargs: Any) -> None:
        self._delete_ignored_args(kwargs)
        super().__init__(**kwargs)

    def _delete_ignored_args(self, args: dict[str, Any]) -> None:
        if self._masked_fields is None:
            self._init_mask(self)
        for key in self._masked_fields:  # type: ignore[union-attr]
            args.pop(key, None)

    # Initializing the mask requires the field names which
    # are only available on instances.
    # So initialization needs to be deferred until the first instantiation of the model.
    # The mask is cached afterward.
    @classmethod
    def _init_mask(cls: type[ModelType], instance: ModelType) -> None:
        def get_name(name: str, field: Any) -> Any:
            return field.alias if field.alias is not None else name

        field_names = {
            get_name(name, field) for name, field in instance.model_fields.items()
        }
        default_mask = tuple(key for key in _IGNORED_KWARGS if key not in field_names)
        cls._masked_fields = cls._user_mask + default_mask

    @classmethod
    def user_model_type(cls) -> type[BaseUserModel] | None:
        """Return the user model type for this model.

        Returns ``None`` if there is no user model, e.g., for ``Dataset``
        where there is a custom class instead of a plain model.
        """
        return None

    @classmethod
    def upload_model_type(cls) -> type[BaseModel] | None:
        """Return the upload model type for this model.

        Returns ``None`` if the model cannot be uploaded or this is an upload model.
        """
        return None

    @classmethod
    def download_model_type(cls) -> type[BaseModel] | None:
        """Return the download model type for this model.

        Returns ``None`` if this is a download model.
        """
        return None


@dataclasses.dataclass
class BaseUserModel:
    """Base class for user models.

    Child classes must be dataclasses.
    """

    @classmethod
    def _download_model_dict(cls, download_model: Any) -> dict[str, Any]:
        return {
            field.name: getattr(
                download_model, _model_field_name_of(cls.__name__, field.name)
            )
            for field in dataclasses.fields(cls)
        }

    def _upload_model_dict(self) -> dict[str, Any]:
        _check_ready_for_upload(self)
        return {
            _model_field_name_of(self.__class__.__name__, field.name): getattr(
                self, field.name
            )
            for field in dataclasses.fields(self)
            if not field.name.startswith("_")
        }

    @classmethod
    def from_download_model(cls, download_model: Any) -> BaseUserModel:
        raise NotImplementedError("Function does not exist for BaseUserModel")

    def make_upload_model(self) -> BaseModel:
        raise NotImplementedError("Function does not exist for BaseUserModel")

    @classmethod
    def upload_model_type(cls) -> type[BaseModel] | None:
        """Return the upload model type for this user model.

        Returns ``None`` if the model cannot be uploaded.
        """
        return None

    @classmethod
    def download_model_type(cls) -> type[BaseModel]:
        """Return the download model type for this user model."""
        # There is no sensible default value here as there always exists a download
        # model.
        # All child classes must implement this function.
        raise NotImplementedError("Function does not exist for BaseUserModel")

    def _repr_html_(self) -> str | None:
        """Return an HTML representation of the model if possible."""
        from ._html_repr import user_model_html_repr

        return user_model_html_repr(self)


def construct(
    model: type[PydanticModelType],
    *,
    _strict_validation: bool = True,
    _quiet: bool = False,
    **fields: Any,
) -> PydanticModelType:
    """Instantiate a SciCat model.

    Warning
    -------
    If the model is created without validation, no fields will be converted
    to their proper type but will simply be whatever arguments are passed.
    See ``model_construct`` or :class:`pydantic.BaseModel` for more information.

    A warning will be emitted in this case.

    Parameters
    ----------
    model:
        Class of the model to create.
    _strict_validation:
        If ``True``, the model must pass validation.
        If ``False``, a model is still returned if validation fails.
    _quiet:
        If ``False``, logs a warning on validation failure.
    fields:
        Field values to pass to the model initializer.

    Returns
    -------
    :
        An initialized model.
    """
    try:
        return model(**fields)
    except pydantic.ValidationError as e:
        if _strict_validation:
            raise
        if not _quiet:
            get_logger().warning(
                "Validation of metadata failed: %s\n"
                "The returned object may be incomplete or broken. "
                "In particular, some fields may not have the correct type",
                str(e),
            )
        return model.model_construct(**fields)


def validate_datetime(value: str | datetime | None) -> datetime | None:
    """Convert strings to datetimes.

    This uses dateutil.parser.parse instead of Pydantic's builtin parser in order to
    produce results that are consistent with user inputs.
    Pydantic uses a custom type for timezones which is not fully compatible with
    dateutil's.
    """
    if not isinstance(value, str):
        return value
    return parse_datetime(value)


def validate_emails(value: str | None) -> str | None:
    if value is None:
        return value
    return ";".join(pydantic.validate_email(item)[1] for item in value.split(";"))


def validate_orcids(value: str | None) -> str | None:
    if value is None:
        return value
    try:
        if is_valid_orcid(value):
            return value
    except (RuntimeError, ValueError, TypeError):
        pass
    raise ValueError(
        "value is not a valid ORCID, "
        "note that ORCIDs must be prefixed with 'https://orcid.org'."
    )


@overload
def convert_download_to_user_model(download_model: None) -> None: ...


@overload
def convert_download_to_user_model(download_model: BaseModel) -> BaseUserModel: ...


@overload
def convert_download_to_user_model(
    download_model: Iterable[BaseModel],
) -> list[BaseUserModel]: ...


def convert_download_to_user_model(
    download_model: BaseModel | Iterable[BaseModel] | None,
) -> BaseUserModel | list[BaseUserModel] | None:
    """Construct user models from download models."""
    if download_model is None:
        return download_model
    if isinstance(download_model, BaseModel):
        if (user_type := download_model.user_model_type()) is None:
            raise TypeError("Cannot convert to user model in this way.")
        return user_type.from_download_model(download_model)
    return list(map(convert_download_to_user_model, download_model))


@overload
def convert_user_to_upload_model(user_model: None) -> None: ...


@overload
def convert_user_to_upload_model(user_model: BaseUserModel) -> BaseModel: ...


@overload
def convert_user_to_upload_model(
    user_model: Iterable[BaseUserModel],
) -> list[BaseModel]: ...


def convert_user_to_upload_model(
    user_model: BaseUserModel | Iterable[BaseUserModel] | None,
) -> BaseModel | list[BaseModel] | None:
    """Construct upload models from user models."""
    if user_model is None:
        return None
    if isinstance(user_model, BaseUserModel):
        return user_model.make_upload_model()
    return list(map(convert_user_to_upload_model, user_model))


def _model_field_name_of(cls_name: str, name: str) -> str:
    """Convert a user model field name to a SciCat model field name.

    Converts snake_case to camelCase and strips leading underscores.
    E.g.,
    `proposal_ids` -> `proposalIds`,
    `_created_at` -> `createdAt`,
    `_History__id` -> `id`.
    """
    name = name.lstrip("_")
    if name.startswith(cls_name):
        # Field names with two leading underscores are prefixed with `_cls_name`
        # by dataclasses, e.g. `__id` -> `_History__id`.
        # Strip this prefix plus underscores.
        name = name[len(cls_name) + 2 :]
    first, *remainder = name.split("_")
    return first + "".join(word.capitalize() for word in remainder)


def _check_ready_for_upload(user_model: BaseUserModel) -> None:
    download_only = {
        field.name: value
        for field in dataclasses.fields(user_model)
        if (value := getattr(user_model, field.name)) is not None
        and field.name.startswith("_")
    }
    if download_only:
        raise ValueError(
            f"These fields of {user_model.__class__.__name__} "
            "must not be set during upload:\n"
            + "\n".join(f"  {name} = {value}" for name, value in download_only.items())
        )


# These fields are auto generated by MongoDB/Mongoose,
# but we don't want them in Scitacean.
# Drop them in the constructor if they are not in the model explicitly.
# - id is a unique ID used by backend v3.*.
#   Used to be hidden in the API for datasets in favor of pid.
#   (Should be the same as pid where applicable.)
# - _id is MongoDB's unique ID for the entry.
#   (Should be the same as id/pid where applicable.)
# - _v or __v is some version added by Mongoose.
_IGNORED_KWARGS = ("id", "_id", "_v", "__v")

ModelType = TypeVar("ModelType", bound=BaseModel)
PydanticModelType = TypeVar("PydanticModelType", bound=pydantic.BaseModel)
