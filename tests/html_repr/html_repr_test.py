# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 SciCat Project (https://github.com/SciCatProject/scitacean)

from scitacean import Attachment, Dataset, RemotePath, Thumbnail


# We don't want to test the concrete layout as that may change
# without breaking anything. So just make sure that the result
# contains the relevant data.
def test_dataset_html_repr() -> None:
    ds = Dataset(
        type="raw",
        name="My dataset",
        contact_email="devsci.cat",
        owner="The People",
        instrument_id="the-peoples-neutron-gun",
        used_software=["scitacean"],
        source_folder=RemotePath("/remote/dir/"),
        meta={
            "temperature": {"value": 5, "unit": "C"},
            "mood": "has been better",
        },
    )

    res = ds._repr_html_()

    assert "My dataset" in res
    assert "used_software" in res
    assert "temperature" in res
    assert "unit" in res


def test_attachment_html_repr() -> None:
    att = Attachment(
        caption="THE_CAPTION.jpg",
        owner_group="ThePeople",
        thumbnail=Thumbnail(mime="image/jpeg", _encoded_data="YWJjZA=="),
    )

    res = att._repr_html_()
    assert isinstance(res, str)

    assert "THE_CAPTION.jpg" in res
    assert "ThePeople" in res
    assert "YWJjZA==" in res
