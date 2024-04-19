# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 SciCat Project (https://github.com/SciCatProject/scitacean)
"""Handler for packaged assets."""

import importlib.resources
from functools import lru_cache
from string import Template


def _read_text(filename: str, group: str) -> str:
    return (
        importlib.resources.files(f"scitacean._html_repr.{group}")
        .joinpath(filename)
        .read_text()
    )


def _preprocess_style(css: str) -> str:
    import re

    # line breaks are not needed
    css = css.replace("\n", "")
    # remove comments
    css = re.sub(r"/\*(\*(?!/)|[^*])*\*/", "", css)
    # remove space around special characters
    css = re.sub(r"\s*([;{}:,])\s*", r"\1", css)
    return css


@lru_cache(maxsize=1)
def dataset_repr_template() -> Template:
    return Template(_read_text("dataset_repr.html.template", "templates"))


@lru_cache(maxsize=1)
def dataset_field_repr_template() -> Template:
    return Template(_read_text("dataset_field_repr.html.template", "templates"))


@lru_cache(maxsize=1)
def files_repr_template() -> Template:
    return Template(_read_text("files_repr.html.template", "templates"))


@lru_cache(maxsize=1)
def metadata_template() -> Template:
    return Template(_read_text("metadata_repr.html.template", "templates"))


@lru_cache(maxsize=1)
def attachment_repr_template() -> Template:
    return Template(_read_text("attachment_repr.html.template", "templates"))


@lru_cache(maxsize=1)
def attachment_field_repr_template() -> Template:
    return Template(_read_text("attachment_field_repr.html.template", "templates"))


@lru_cache(maxsize=1)
def common_style() -> str:
    sheet = _preprocess_style(_read_text("common.css", "styles"))
    return f"<style>{sheet}</style>"


@lru_cache(maxsize=1)
def dataset_style() -> str:
    sheet = _preprocess_style(_read_text("dataset.css", "styles"))
    return f"{common_style()}<style>{sheet}</style>"


@lru_cache(maxsize=1)
def attachment_style() -> str:
    sheet = _preprocess_style(_read_text("attachment.css", "styles"))
    return f"{common_style()}<style>{sheet}</style>"


@lru_cache
def image(name: str) -> str:
    return _read_text(name, "images")
