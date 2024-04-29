# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 SciCat Project (https://github.com/SciCatProject/scitacean)
"""Thumbnail type for encoding images."""

from __future__ import annotations

import base64
import mimetypes
import os
import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from pydantic import GetCoreSchemaHandler
from pydantic_core import core_schema


@dataclass(init=False, kw_only=True, slots=True)
class Thumbnail:
    """Encodes an image to be used as a thumbnail in SciCat.

    Thumbnails are *small* images used, e.g., in attachments.
    In SciCat, they are base64-encoded strings and have a size limit.

    This class handles the encoding but does not enforce a size limit
    or content type.

    Currently, data is stored in encoded form.
    This means that creating a thumbnail object in a SciCat download is cheap.
    But creating one from local data and throwing it away without uploading it
    has some small overhead.

    Examples
    --------
    Given some raw bytes from a PNG, create a thumbnail using

    .. code-block:: python

        from scitacean import Thumbnail
        data = ... # the bytes of the PNG
        thumbnail = Thumbnail(mime="image/png", data=data)

    Or load the data directly from a file:

    .. code-block:: python

        thumbnail = Thumbnail.load_file("file_path.png")

    Access the raw bytes:

    .. code-block:: python

        data: bytes = thumbnail.decoded_data()
    """

    mime: str | None
    """Complete MIME type in the form ``type/subtype``."""
    _encoded_data: str

    def __init__(
        self,
        mime: str | None,
        data: bytes | None = None,
        _encoded_data: str | None = None,
    ) -> None:
        """Create a new thumbnail object.

        Parameters
        ----------
        mime:
            The MIME type of the thumbnail.
            Must be a string of the form ``image/png``.
            Parameters are not allowed.
        data:
            The raw bytes of the thumbnail.
            Will be encoded automatically.
        _encoded_data:
            Primarily for internal use.
            Base64-encoded data of the thumbnail.
            Mutually exclusive with ``data``.
        """
        if data is None:
            if _encoded_data is None:
                raise TypeError("No thumbnail data specified")
            self._encoded_data = _encoded_data
        else:
            if _encoded_data is None:
                self._encoded_data = base64.b64encode(data).decode("utf-8")
            else:
                raise TypeError("Only only of data and _encoded_data may be given")

        self.mime = mime

    @classmethod
    def load_file(cls, path: os.PathLike[str] | str) -> Thumbnail:
        """Construct a thumbnail from data loaded from a file.

        Parameters
        ----------
        path:
            The path to the file.

        Returns
        -------
        :
            A new thumbnail with MIME type guessed from the file
            and data loaded from disk.
        """
        with open(path, "rb") as f:
            data = f.read()
        encoded_data = base64.b64encode(data).decode("utf-8")
        return Thumbnail(mime=mimetypes.guess_type(path)[0], _encoded_data=encoded_data)

    @classmethod
    def parse(cls, encoded: str | Thumbnail, /) -> Thumbnail:
        """Construct a thumbnail from a string as used by SciCat.

        Parameters
        ----------
        encoded:
            A string containing a MIME content-header and the thumbnail
            in base64 encoding.
            Or an existing ``Thumbnail`` instance which is copied on return.

        Returns
        -------
        :
            A new thumbnail with MIME type and data extracted from the string.

        See Also
        --------
        Thumbnail.serialize:
            The inverse operation.
        """
        if isinstance(encoded, Thumbnail):
            return Thumbnail(mime=encoded.mime, _encoded_data=encoded._encoded_data)

        if (match := _MESSAGE_REGEX.match(encoded)) is None:
            mime = None
            encoded_data = encoded
        else:
            mime = match[1]
            encoded_data = match[2]

        return Thumbnail(mime=mime, _encoded_data=encoded_data)

    def serialize(self) -> str:
        """Format the thumbnail into a string in the format expected by SciCat.

        Returns
        -------
        :
            A string containing the MIME content-header and the thumbnail
            in base64 encoding.

        See Also
        --------
        Thumbnail.parse:
            The inverse operation.
        """
        mime_str = f"data:{self.mime};base64," if self.mime is not None else ""
        return mime_str + self.encoded_data()

    @property
    def mime_type(self) -> str | None:
        """The MIME type, i.e., the first part of ``type/subtype``."""
        if self.mime is None:
            return None
        return self.mime.split("/", 1)[0]

    @property
    def mime_subtype(self) -> str | None:
        """The MIME subtype, i.e., the second part of ``type/subtype``."""
        if self.mime is None:
            return None
        return self.mime.split("/", 1)[1]

    def encoded_data(self) -> str:
        """Return the base64-encoded data of the thumbnail."""
        return self._encoded_data

    def decoded_data(self) -> bytes:
        """Return the raw bytes of the thumbnail."""
        return base64.b64decode(self._encoded_data)

    def __str__(self) -> str:
        return f"Thumbnail({self.mime}, len:{len(self.encoded_data())}B)"

    def __repr__(self) -> str:
        return f"Thumbnail(mime={self.mime}, data={self.decoded_data()!r})"

    def _repr_mimebundle_(
        self, include: Any = None, exclude: Any = None
    ) -> dict[str, bytes | str]:
        def decoded() -> bytes:
            return self.decoded_data()

        repr_fns: dict[str, Callable[[], bytes | str]] = {
            "image/png": decoded,
            "image/jpeg": decoded,
            "image/svg+xml": decoded,
            "application/pdf": decoded,
            "text/html": lambda: f"<img src={self.serialize()}>",
            "text/plain": self.__str__,
        }
        if include is not None:
            repr_fns = {k: v for k, v in repr_fns.items() if k in include}
        if exclude is not None:
            repr_fns = {k: v for k, v in repr_fns.items() if k not in exclude}

        if self.mime in repr_fns:
            return {self.mime: repr_fns[self.mime]()}
        return {
            mime: fn()
            for mime in {"text/html", "text/plain"}
            if (fn := repr_fns.get(mime))
        }

    @classmethod
    def __get_pydantic_core_schema__(
        cls, _source_type: Any, _handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        return core_schema.no_info_after_validator_function(
            cls.parse,
            core_schema.union_schema(
                [core_schema.is_instance_schema(Thumbnail), core_schema.str_schema()]
            ),
            serialization=core_schema.plain_serializer_function_ser_schema(
                cls.serialize, info_arg=False, return_schema=core_schema.str_schema()
            ),
        )


# A regex that matches encoded thumbnails with header.
# Expected form: data:image/png;base64,the-data
_MESSAGE_REGEX = re.compile(
    r"^(?:data:)?"  # optional data: prefix
    "(?:([^/]+/[^;]+)(?:;.*)?,)?"  # MIME content-header
    "(.*)$"  # data
)
