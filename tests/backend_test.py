from .common.backend import scicat_backend  # noqa

from scitacean import Client


def test_asd(scicat_backend):
    client = Client.from_credentials(
        url="http://localhost/api/v3", username="ingestor", password="aman"
    )
    ds = client.get_dataset_model("PID.SAMPLE.PREFIX/desy_ds1")
    print(ds)
    assert False
