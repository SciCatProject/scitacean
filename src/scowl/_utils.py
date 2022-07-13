# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2022 Scowl contributors (https://github.com/SciCatProject/scowl)
# @author Jan-Lukas Wynen

from typing import Tuple


def _make_model_accessor(field_name: str, model_name: str):
    return property(
        lambda self: getattr(getattr(self, model_name), field_name),
        lambda self, val: setattr(getattr(self, model_name), field_name, val),
    )


def _make_raising_accessor(field_name: str):
    # Prevent access to some attributes which are managed automatically.
    # Using a property that always raises here,
    # because that also prevents accidental assignments.
    def impl(_self):
        raise AttributeError(f"Attribute '{field_name}' is not accessible")

    return property(impl)


def wrap_model(model, model_name: str, exclude: Tuple[str, ...]):
    def impl(cls):
        for field in model.__fields__:
            if field in exclude:
                setattr(cls, field, _make_raising_accessor(field))
            else:
                setattr(
                    cls,
                    field,
                    _make_model_accessor(field_name=field, model_name=model_name),
                )
        return cls

    return impl
