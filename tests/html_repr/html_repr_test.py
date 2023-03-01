# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 SciCat Project (https://github.com/SciCatProject/scitacean)

from scitacean import Dataset, RemotePath


# We don't want to test the concrete layout as that may change
# without breaking anything. So just make sure that the result
# contains the relevant data.
def test_dataset_html_repr():
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
