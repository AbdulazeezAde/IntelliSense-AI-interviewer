import base64
import os
from unittest.mock import patch
from app.tts.provider import MockTTSProvider


def test_mock_tts_uses_azure_when_available(monkeypatch, tmp_path):
    # Set env vars for Azure config
    import app.core.config as cfg
    # Set settings on the live Settings instance (monkeypatching env after import won't affect Settings)
    monkeypatch.setattr(cfg.settings, 'AZURE_STORAGE_CONNECTION_STRING', 'UseDevelopmentStorage=true')
    monkeypatch.setattr(cfg.settings, 'AZURE_STORAGE_CONTAINER', 'testcontainer')

    # Monkeypatch upload_base64 to simulate Azure upload
    called = {}
    def fake_upload(container, blob_name, b64):
        called['container'] = container
        called['blob_name'] = blob_name
        return f"https://fake.blob/{container}/{blob_name}"

    monkeypatch.setattr('app.storage.azure_blob.upload_base64', fake_upload)

    provider = MockTTSProvider()
    import asyncio
    res = asyncio.run(provider.generate('s1','hello azure','neutral',None,'wav'))
    assert res['audio_url'].startswith('https://fake.blob/')
    assert called['container'] == 'testcontainer'
