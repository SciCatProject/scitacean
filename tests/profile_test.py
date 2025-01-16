# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 SciCat Project (https://github.com/SciCatProject/scitacean)

from pathlib import Path

import pytest
from pyfakefs.fake_filesystem import FakeFilesystem

from scitacean._profile import Profile, locate_profile


def test_locate_profile_finds_builtin_ess() -> None:
    profile = locate_profile("ess")
    assert profile.url == "https://scicat.ess.eu/api/v3"


def test_locate_profile_returns_given_profile() -> None:
    initial = Profile(url="https://example.com", file_transfer=None)
    profile = locate_profile(initial)
    assert profile == initial


def test_locate_profile_loads_profile_from_file_in_cwd_path(fs: FakeFilesystem) -> None:
    test_profile_toml = """
url = 'https://example.file.se/'
"""
    fs.create_file("path-test.profile.toml", contents=test_profile_toml)
    profile = locate_profile(Path("path-test.profile.toml"))
    assert profile.url == "https://example.file.se/"


def test_locate_profile_loads_profile_from_file_in_cwd_str(fs: FakeFilesystem) -> None:
    test_profile_toml = """
url = 'https://example.file.se/'
"""
    fs.create_file("str-test.profile.toml", contents=test_profile_toml)
    profile = locate_profile("str-test.profile.toml")
    assert profile.url == "https://example.file.se/"


def test_locate_profile_path_overrides_builtin(fs: FakeFilesystem) -> None:
    test_profile_toml = """
url = 'https://example.file.se/'
"""
    fs.create_file("ess", contents=test_profile_toml)
    profile = locate_profile(Path("ess"))  # asking explicitly for a path
    assert profile.url == "https://example.file.se/"


def test_locate_profile_loads_profile_from_file_in_cwd_name_only_str(
    fs: FakeFilesystem,
) -> None:
    test_profile_toml = """
url = 'https://example.file.se/'
"""
    fs.create_file("str-test.profile.toml", contents=test_profile_toml)
    profile = locate_profile("str-test")  # also tries with default extension
    assert profile.url == "https://example.file.se/"


def test_locate_profile_builtin_overrides_file_name_only_str(
    fs: FakeFilesystem,
) -> None:
    test_profile_toml = """
url = 'https://example.file.se/'
"""
    fs.create_file("ess.profile.toml", contents=test_profile_toml)
    profile = locate_profile("ess")  # could resolve to the file but doesn't
    assert profile.url == "https://scicat.ess.eu/api/v3"


def test_locate_profile_raises_for_unknown_profile() -> None:
    with pytest.raises(ValueError, match="Unknown profile"):
        locate_profile("does-not-exist")
