# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 SciCat Project (https://github.com/SciCatProject/scitacean)
"""HTML representations for Jupyter."""

from __future__ import annotations

from collections.abc import Callable
from functools import lru_cache
from typing import TYPE_CHECKING, Any

from ._attachment_html import attachment_html_repr
from ._dataset_html import dataset_html_repr

if TYPE_CHECKING:
    from ..model import BaseUserModel


@lru_cache(maxsize=1)
def _user_model_reprs() -> dict[type, Callable[[Any], str]]:
    from ..model import Attachment

    return {Attachment: attachment_html_repr}


def user_model_html_repr(user_model: BaseUserModel) -> str | None:
    """HTML representation of a user model f implemented."""
    if (repr_fn := _user_model_reprs().get(type(user_model))) is not None:
        return repr_fn(user_model)
    return None


__all__ = ["dataset_html_repr", "user_model_html_repr"]
