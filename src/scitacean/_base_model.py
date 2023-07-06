# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 SciCat Project (https://github.com/SciCatProject/scitacean)

"""Types and functions to implement models for communication with SciCat."""

try:
    # Python 3.11+
    from enum import StrEnum as _StrEnum

    _DatasetTypeBases = (_StrEnum,)
except ImportError:
    from enum import Enum as _Enum

    _DatasetTypeBases = (
        str,
        _Enum,
    )

import dataclasses
from datetime import datetime
from typing import Any, Dict, Iterable, Optional, Type, TypeVar, Union

import pydantic
from dateutil.parser import parse as parse_datetime

from ._internal.orcid import is_valid_orcid
from ._internal.pydantic_compat import is_pydantic_v1
from .filesystem import RemotePath
from .logging import get_logger
from .pid import PID

ModelType = TypeVar("ModelType", bound=pydantic.BaseModel)


class DatasetType(*_DatasetTypeBases):
    """Type of Dataset."""

    RAW = "raw"
    DERIVED = "derived"


class BaseModel(pydantic.BaseModel):
    """Base class for Pydantic models for communication with SciCat."""

    if is_pydantic_v1():

        class Config:
            extra = pydantic.Extra.forbid
            json_encoders = {
                PID: lambda v: str(v),
                RemotePath: lambda v: v.posix,
            }

    else:
        model_config = pydantic.ConfigDict(
            extra="forbid",
        )

    # Some schemas contain fields that we don't want to use in Scitacean.
    # Normally, omitting them from the model would result in an error when
    # building a model from the JSON returned by SciCat.
    # The following subclass hook allows models to mark fields as masked.
    # Those will be silently dropped by __init__.
    # Note also the comment for _IGNORED_KWARGS below.
    def __init_subclass__(
        cls, /, masked: Optional[Iterable[str]] = None, **kwargs: Any
    ) -> None:
        super().__init_subclass__(**kwargs)

        masked = list(masked) if masked is not None else []
        field_names = {field.alias for field in cls.get_model_fields().values()}
        masked.extend(key for key in _IGNORED_KWARGS if key not in field_names)
        cls._masked_fields = tuple(masked)

    def __init__(self, **kwargs: Any) -> None:
        self._delete_ignored_args(kwargs)
        super().__init__(**kwargs)

    def _delete_ignored_args(self, args: Dict[str, Any]) -> None:
        for key in self._masked_fields:
            args.pop(key, None)

    if is_pydantic_v1():

        @classmethod
        def get_model_fields(cls) -> Dict[str, pydantic.fields.ModelField]:
            return cls.__fields__

        def model_dump(self, *args, **kwargs) -> Dict[str, Any]:
            return self.dict(*args, **kwargs)

        def model_dump_json(self, *args, **kwargs) -> str:
            return self.json(*args, **kwargs)

        @classmethod
        def model_construct(cls: Type[ModelType], *args, **kwargs) -> ModelType:
            return cls.construct(*args, **kwargs)

        @classmethod
        def model_rebuild(cls, *args, **kwargs) -> Optional[bool]:
            return cls.update_forward_refs(*args, **kwargs)

    else:

        @classmethod
        def get_model_fields(cls) -> Dict[str, pydantic.fields.FieldInfo]:
            return cls.model_fields


class BaseUserModel:
    """Base class for user models.

    Child classes must be dataclasses.
    """

    @classmethod
    def _download_model_dict(cls, download_model: Any) -> Dict[str, Any]:
        return {
            field.name: getattr(
                download_model, _model_field_name_of(cls.__name__, field.name)
            )
            for field in dataclasses.fields(cls)
        }

    def _upload_model_dict(self) -> Dict[str, Any]:
        _check_ready_for_upload(self)
        return {
            _model_field_name_of(self.__class__.__name__, field.name): getattr(
                self, field.name
            )
            for field in dataclasses.fields(self)
            if not field.name.startswith("_")
        }


def construct(
    model: Type[ModelType],
    *,
    _strict_validation: bool = True,
    _quiet: bool = False,
    **fields: Any,
) -> ModelType:
    """Instantiate a SciCat model.

    Warning
    -------
    If the model is created without validation, no fields will be converted
    to their proper type but will simply be whatever arguments are passed.

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


def validate_datetime(value: Optional[Union[str, datetime]]) -> Optional[datetime]:
    """Convert strings to datetimes.

    This uses dateutil.parser.parse instead of Pydantic's builtin parser in order to
    produce results that are consistent with user inputs.
    Pydantic uses a custom type for timezones which is not fully compatible with
    dateutil's.
    """
    if not isinstance(value, str):
        return value
    return parse_datetime(value)


def validate_drop(_: Any) -> None:
    """Return ``None``."""
    return None


def validate_emails(value: Optional[str]) -> Optional[str]:
    if value is None:
        return value
    return ";".join(pydantic.validate_email(item)[1] for item in value.split(";"))


def validate_orcids(value: Optional[str]) -> Optional[str]:
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


def _model_field_name_of(cls_name: str, name: str) -> str:
    """Convert a user model field name to a SciCat model field name.

    Converts snake_case to camelCase and strips leading underscores.
    E.g.,
    `proposal_id` -> `proposalId`,
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
