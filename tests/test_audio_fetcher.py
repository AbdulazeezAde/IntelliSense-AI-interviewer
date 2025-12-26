import io
import os
import types
from unittest.mock import Mock
import pytest

from app.stt.audio_fetcher import fetch_audio_to_temp


class FakeResponse:
    def __init__(self, content: bytes, status_code=200):
        self._content = content
        self.status_code = status_code
        self.headers = {"content-type": "audio/wav"}
    def raise_for_status(self):
        if not (200 <= self.status_code < 300):
            raise Exception("HTTP error")
    def iter_content(self, chunk_size=8192):
        for i in range(0, len(self._content), chunk_size):
            yield self._content[i:i+chunk_size]


def test_fetch_audio_to_temp_success(monkeypatch, tmp_path):
    data = b"RIFF....WAVE" * 10
    fake = FakeResponse(data)
    class FakeSession:
        def get(self, url, stream=True, timeout=10):
            return fake
    monkeypatch.setattr('app.stt.audio_fetcher._create_session_with_retries', lambda retries, backoff_factor: FakeSession())

    path = fetch_audio_to_temp("http://example.com/some_audio.wav")
    assert os.path.exists(path)
    with open(path, 'rb') as f:
        content = f.read()
    assert content == data
    os.unlink(path)


def test_fetch_audio_too_large(monkeypatch):
    data = b"0" * (60 * 1024 * 1024)
    fake = FakeResponse(data)
    class FakeSession:
        def get(self, url, stream=True, timeout=10):
            return fake
    monkeypatch.setattr('app.stt.audio_fetcher._create_session_with_retries', lambda retries, backoff_factor: FakeSession())
    with pytest.raises(ValueError):
        fetch_audio_to_temp("http://example.com/huge.wav", max_bytes=5*1024*1024)


def test_fetch_non_200(monkeypatch):
    fake = FakeResponse(b"", status_code=404)
    monkeypatch.setattr('requests.get', lambda url, stream=True, timeout=10: fake)
    with pytest.raises(Exception):
        fetch_audio_to_temp("http://example.com/missing.wav")


def test_fetch_with_retries(monkeypatch, tmp_path):
    # Simulate two transient failures followed by success
    data = b"RIFF....WAVE" * 5
    calls = {'n': 0}

    class MaybeFail:
        def __init__(self, content, status_code=200):
            self._content = content
            self.status_code = status_code
        def raise_for_status(self):
            if not (200 <= self.status_code < 300):
                raise Exception("HTTP error")
        def iter_content(self, chunk_size=8192):
            for i in range(0, len(self._content), chunk_size):
                yield self._content[i:i+chunk_size]

    def fake_session_get(url, stream=True, timeout=10):
        calls['n'] += 1
        if calls['n'] < 3:
            return MaybeFail(b"", status_code=500)
        return MaybeFail(data, status_code=200)

    # Patch requests.Session.get used by _create_session_with_retries
    class FakeSession:
        def get(self, *args, **kwargs):
            return fake_session_get(*args, **kwargs)

    monkeypatch.setattr('app.stt.audio_fetcher._create_session_with_retries', lambda retries, backoff_factor: FakeSession())

    path = fetch_audio_to_temp("http://example.com/retry.wav", retries=3, backoff_factor=0.01)
    assert os.path.exists(path)
    with open(path, 'rb') as f:
        content = f.read()
    assert content == data
    os.unlink(path)





def test_fetch_azure(monkeypatch, tmp_path):
    data = b"AZDATA"
    class FakeDownloader:
        def chunks(self):
            yield data
    class FakeBlobClient:
        def download_blob(self):
            return FakeDownloader()
    class FakeContainer:
        def get_blob_client(self, blob):
            assert blob == 'a/b.wav'
            return FakeBlobClient()
    class FakeService:
        def get_container_client(self, container):
            assert container == 'mycont'
            return FakeContainer()
    monkeypatch.setattr('azure.storage.blob.BlobServiceClient.from_connection_string', lambda cs: FakeService())

    path = fetch_audio_to_temp('azure://mycont/a/b.wav')
    assert os.path.exists(path)
    with open(path, 'rb') as f:
        content = f.read()
    assert content == data
    os.unlink(path)
