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

import re
from typing import Any, Dict, Optional, Type, TypeVar

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
    class Config:
        extra = pydantic.Extra.forbid
        json_encoders = {
            PID: lambda v: str(v),
            RemotePath: lambda v: v.posix,
        }

    def camel_case_dict(self, *args, **kwargs) -> Dict[str, Any]:
        """Return a dict representation of the model with camelCase names.

        Arguments are forwarded to ``pydantic.BaseModel.dict()``.
        """
        return {
            _snake_case_to_camel_case(key): value
            for key, value in self.dict(*args, **kwargs)
        }


def validate_emails(value: Optional[str]) -> Optional[str]:
    if value is None:
        return value
    return ";".join(pydantic.EmailStr.validate(item) for item in value.split(";"))


def validate_orcid(value: Optional[str]) -> Optional[str]:
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


def construct(
    model: Type[ModelType],
    *,
    _strict_validation: bool = True,
    _from_camel_case: bool = False,
    **fields: Any,
) -> ModelType:
    """Instantiate a model.

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
    _from_camel_case:
        If ``True``, file names are converted from camelCase to snake_case.
    fields:
        Field values to pass to the model initializer.

    Returns
    -------
    :
        An initialized model.
    """
    if _from_camel_case:
        fields = {
            _camel_case_to_snake_case(key): value for key, value in fields.items()
        }

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


def _snake_case_to_camel_case(string: str) -> str:
    """Convert a string from snake_case to camelCase."""
    first, *remainder = string.split("_")
    return first + "".join(word.capitalize() for word in remainder)


def _camel_case_to_snake_case(string: str) -> str:
    """Convert a string from camelCase to snake_case."""

    def repl(match):
        return "_" + match[1].lower()

    return re.sub(r"([A-Z])", repl, string)
