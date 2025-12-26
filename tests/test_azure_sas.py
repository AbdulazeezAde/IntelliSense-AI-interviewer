from unittest.mock import patch
import app.storage.azure_blob as az
import app.core.config as cfg


def test_generate_sas_url_parsing(monkeypatch):
    # Create a fake connection string with AccountName and AccountKey
    cs = "DefaultEndpointsProtocol=http;AccountName=testacct;AccountKey=key123;BlobEndpoint=http://127.0.0.1:10000/testacct"
    monkeypatch.setattr(cfg.settings, 'AZURE_STORAGE_CONNECTION_STRING', cs)

    # Monkeypatch generate_blob_sas to return 'sastoken' and ensure base url is constructed
    def fake_generate_blob_sas(account_name, container_name, blob_name, account_key, permission, expiry):
        assert account_name == 'testacct'
        assert account_key == 'key123'
        return 'sastoken123'

    class FakeContainerClient:
        url = 'http://127.0.0.1:10000/testacct'

    class FakeClient:
        def get_container_client(self, container):
            return FakeContainerClient()

    monkeypatch.setattr('app.storage.azure_blob._ensure_client', lambda: FakeClient())
    monkeypatch.setattr('app.storage.azure_blob.generate_blob_sas', fake_generate_blob_sas, raising=False)

    # call generate_sas_url
    sas = az.generate_sas_url('mycontainer', 'file.wav', expiry_seconds=3600)
    assert sas is not None
    assert 'sastoken123' in sas
