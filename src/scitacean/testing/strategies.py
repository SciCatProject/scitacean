# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2022 Scitacean contributors (https://github.com/SciCatProject/scitacean)
# @author Jan-Lukas Wynen

from typing import Any, Dict, Tuple

from hypothesis import infer, strategies as st
from pyscicat import model as m


def builds_model(
    model, to_infer: Tuple[str, ...], user_kwargs: Dict[str, Any]
) -> st.SearchStrategy:
    """Return a SearchStrategy for a given Pydantic model.

    ``hypothesis.strategies.builds`` cannot be used here because it always sets
    ``Optional`` fields to ``None``,
    see https://github.com/pydantic/pydantic/issues/3126
    As a workaround, ``st.from_type`` does work with ``Optional`` but does
    allow specifying individual fields.
    """
    inferred = {name: infer for name in to_infer}
    customized = {
        name: arg if isinstance(arg, st.SearchStrategy) else st.just(arg)
        for name, arg in user_kwargs.items()
    }
    return st.builds(model, **{**inferred, **customized})


# TODO implement both for model and Dataset class
def datasets(**kwargs) -> st.SearchStrategy[m.Dataset]:
    """Returns a SearchStrategy for a dataset model."""
    # TODO add all other optional fields
    return builds_model(m.Dataset, ("classification", "isPublished"), kwargs)


def derived_datasets(**kwargs) -> st.SearchStrategy[m.DerivedDataset]:
    return builds_model(m.DerivedDataset, ("classification", "isPublished"), kwargs)


def raw_datasets(**kwargs) -> st.SearchStrategy[m.RawDataset]:
    return builds_model(m.RawDataset, ("classification", "isPublished"), kwargs)
