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
from typing import Any, Dict, Optional, Tuple, Type, TypeVar

import pydantic

from ._internal.orcid import is_valid_orcid
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

    class Config:
        extra = pydantic.Extra.forbid
        json_encoders = {
            PID: lambda v: str(v),
            RemotePath: lambda v: v.posix,
        }

    # Some schemas contain fields that we don't want to use in Scitacean.
    # Normally, omitting them from the model would result in an error when
    # building a model from the JSON returned by SciCat.
    # The following subclass hook allows models to mark fields as masked.
    # Those will be silently dropped by __init__.
    # Note also the comment for _IGNORED_KWARGS below.
    def __init_subclass__(
        cls, /, masked: Optional[Tuple[str, ...]] = None, **kwargs: Any
    ) -> None:
        super().__init_subclass__(**kwargs)
        if masked is not None:
            cls._masked_fields = masked

    def __init__(self, **kwargs: Any) -> None:
        self._delete_ignored_args(kwargs)
        super().__init__(**kwargs)

    def _delete_ignored_args(self, args: Dict[str, Any]) -> None:
        for key in _IGNORED_KWARGS:
            if key not in self.__fields__:
                args.pop(key, None)
        if hasattr(self, "_masked_fields"):
            for key in self._masked_fields:
                args.pop(key, None)


class BaseUserModel:
    """Base class for user models.

    Child classes must be dataclasses.
    """

    @classmethod
    def _download_model_dict(cls, download_model: Any) -> Dict[str, Any]:
        return {
            field.name: getattr(download_model, _model_field_name_of(field.name))
            for field in dataclasses.fields(cls)
        }

    def _upload_model_dict(self) -> Dict[str, Any]:
        _check_ready_for_upload(self)
        return {
            _model_field_name_of(field.name): getattr(self, field.name)
            for field in dataclasses.fields(self)
            if not field.name.startswith("_")
        }


def construct(
    model: Type[ModelType],
    *,
    _strict_validation: bool = True,
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
        get_logger().warning(
            "Validation of metadata failed: %s\n"
            "The returned object may be incomplete or broken. "
            "In particular, some fields may not have the correct type",
            str(e),
        )
        return model.construct(**fields)


def validate_emails(value: Optional[str]) -> Optional[str]:
    if value is None:
        return value
    return ";".join(pydantic.EmailStr.validate(item) for item in value.split(";"))


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


def _model_field_name_of(name: str) -> str:
    """Convert a user model field name to a SciCat model field name.

    Converts snake_case to camelCase and strips leading underscores.
    """
    first, *remainder = name.lstrip("_").split("_")
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
