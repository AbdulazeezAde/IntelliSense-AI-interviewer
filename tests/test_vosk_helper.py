import io
import zipfile
from pathlib import Path
from unittest.mock import patch
import app.stt.vosk_helper as vh


def make_model_zip():
    b = io.BytesIO()
    with zipfile.ZipFile(b, 'w') as z:
        z.writestr('vosk-model-test/readme.txt', 'test')
    b.seek(0)
    return b.read()


def test_download_and_extract_model(tmp_path, monkeypatch):
    data = make_model_zip()

    class FakeResp:
        def __init__(self, data):
            self._data = data
            self.status_code = 200
        def raise_for_status(self):
            return
        def iter_content(self, chunk_size=8192):
            for i in range(0, len(self._data), chunk_size):
                yield self._data[i:i+chunk_size]

    monkeypatch.setattr('requests.get', lambda url, stream, timeout: FakeResp(data))

    out = vh.download_and_extract_model(dest_dir=tmp_path)
    p = Path(out)
    # Expect a folder starting with 'vosk-model'
    assert p.name.startswith('vosk-model') or any(child.name.startswith('vosk-model') for child in p.iterdir())
