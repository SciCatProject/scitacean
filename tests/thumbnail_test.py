# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 SciCat Project (https://github.com/SciCatProject/scitacean)

import pytest
from pyfakefs.fake_filesystem import FakeFilesystem

from scitacean import Thumbnail


def test_mime_type() -> None:
    thumbnail = Thumbnail(data=b"", mime="image/png")
    assert thumbnail.mime == "image/png"
    assert thumbnail.mime_type == "image"
    assert thumbnail.mime_subtype == "png"


def test_no_mime_type() -> None:
    thumbnail = Thumbnail(data=b"", mime=None)
    assert thumbnail.mime is None
    assert thumbnail.mime_type is None
    assert thumbnail.mime_subtype is None


def test_parse_mime_prefix() -> None:
    thumbnail = Thumbnail.parse("data:image/png,YWJj")
    assert thumbnail.mime == "image/png"
    assert thumbnail.encoded_data() == "YWJj"


def test_parse_mime_encoding() -> None:
    thumbnail = Thumbnail.parse("image/png;base64,YWJj")
    assert thumbnail.mime == "image/png"
    assert thumbnail.encoded_data() == "YWJj"


def test_parse_mime_param() -> None:
    thumbnail = Thumbnail.parse("text/html; charset=utf-8,YWEzMzQ=")
    assert thumbnail.mime == "text/html"
    assert thumbnail.encoded_data() == "YWEzMzQ="


def test_parse_mime_2_param2() -> None:
    thumbnail = Thumbnail.parse("image/svg+xml; charset=utf-8;base64,eXEzeGE=")
    assert thumbnail.mime == "image/svg+xml"
    assert thumbnail.encoded_data() == "eXEzeGE="


def test_parse_empty_params() -> None:
    thumbnail = Thumbnail.parse("image/jpeg;,amY7YQ==")
    assert thumbnail.mime == "image/jpeg"
    assert thumbnail.encoded_data() == "amY7YQ=="


def test_parse_no_params() -> None:
    thumbnail = Thumbnail.parse("image/svg,OGZh")
    assert thumbnail.mime == "image/svg"
    assert thumbnail.encoded_data() == "OGZh"


def test_parse_no_mime() -> None:
    thumbnail = Thumbnail.parse("amE5MHM4aA==")
    assert thumbnail.mime is None
    assert thumbnail.encoded_data() == "amE5MHM4aA=="


def test_parse_thumbnail_argument() -> None:
    thumbnail1 = Thumbnail(mime="image/png", data=b"jak2kcna")
    thumbnail2 = Thumbnail.parse(thumbnail1)
    assert thumbnail1 == thumbnail2
    assert thumbnail1 is not thumbnail2


def test_init_encode() -> None:
    thumbnail = Thumbnail(mime=None, data=b"abc")
    assert thumbnail.decoded_data() == b"abc"
    assert thumbnail.encoded_data() == "YWJj"


def test_init_decode() -> None:
    thumbnail = Thumbnail(mime=None, _encoded_data="YWEzMzQ=")
    assert thumbnail.decoded_data() == b"aa334"
    assert thumbnail.encoded_data() == "YWEzMzQ="


def test_init_no_data_raises() -> None:
    with pytest.raises(TypeError):
        Thumbnail(mime=None)


def test_init_both_data_raises() -> None:
    with pytest.raises(TypeError):
        Thumbnail(mime=None, data=b"jalks", _encoded_data="YWEzMzQ=")


def test_load_file(fs: FakeFilesystem) -> None:
    fs.create_file("fingers.jpg", contents=b"jal2l9vun2")
    thumbnail = Thumbnail.load_file("fingers.jpg")
    assert thumbnail.mime == "image/jpeg"
    assert thumbnail.decoded_data() == b"jal2l9vun2"
    assert thumbnail.encoded_data() == "amFsMmw5dnVuMg=="


def test_load_file_unknown_mime_type(fs: FakeFilesystem) -> None:
    fs.create_file("bad.xxx", contents=b"f9gas03n")
    thumbnail = Thumbnail.load_file("bad.xxx")
    assert thumbnail.mime is None
    assert thumbnail.decoded_data() == b"f9gas03n"
    assert thumbnail.encoded_data() == "ZjlnYXMwM24="


def test_serialize() -> None:
    thumbnail = Thumbnail(mime="image/jpeg", data=b"ags9da0")
    assert thumbnail.serialize() == "data:image/jpeg;base64,YWdzOWRhMA=="


def test_serialize_parse_roundtrip() -> None:
    thumbnail = Thumbnail(mime="image/svg+xml", data=b"412897a897s")
    serialized = thumbnail.serialize()
    reconstructed = Thumbnail.parse(serialized)
    assert reconstructed == thumbnail
