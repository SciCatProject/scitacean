# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2026 SciCat Project (https://github.com/SciCatProject/scitacean)

from scitacean import Dataset, merge_datasets


def test_merge_datasets() -> None:
    a = Dataset(
        type="raw",
        name="A",
        owner="Ponder",
        owner_email="ponder.stibbons@ee.edu",
        used_software=["Program 2", "Program 1"],
    )
    b = Dataset(
        type="raw", name="B", owner="Ponder", used_software=["Program 1", "Program 3"]
    )

    merged = merge_datasets([a, b])
    expected = Dataset(
        type="raw",
        creation_time=None,
        owner="Ponder",
        used_software=["Program 2", "Program 1", "Program 3"],
    )

    for field in Dataset.fields():
        assert merged[field.name] == expected[field.name], field.name


# TODO complex fields (lists, owner)
# TODO files
# TODO attachments
# TODO hypothesis: merge(a, a) == a to check that all fields are processed
