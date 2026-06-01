# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2026 SciCat Project (https://github.com/SciCatProject/scitacean)

import pytest

from scitacean._profile import Profile, locate_profile


def test_locate_profile_finds_builtin_ess() -> None:
    profile = locate_profile("ess")
    assert profile.url == "https://scicat.ess.eu/api/v3"


def test_locate_profile_returns_given_profile() -> None:
    initial = Profile(url="https://example.com", file_transfer=None)
    profile = locate_profile(initial)
    assert profile == initial


def test_locate_profile_raises_for_unknown_profile() -> None:
    with pytest.raises(ValueError, match="Unknown profile"):
        locate_profile("does-not-exist")
