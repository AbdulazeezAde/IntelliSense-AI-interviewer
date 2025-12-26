from app.storage.filesystem import save_base64, list_files, STORAGE_DIR
import base64

def test_filesystem_save_and_list(tmp_path, monkeypatch):
    # Use tmp storage dir
    monkeypatch.setenv('STORAGE_DIR', str(tmp_path))
    # reload module to pick up new env
    from importlib import reload
    import app.storage.filesystem as fs
    reload(fs)

    sample = base64.b64encode(b"hello audio").decode('ascii')
    filename = "test.wav"
    path = fs.save_base64(filename, sample)
    assert filename in path
    files = fs.list_files()
    assert any('test.wav' in f for f in files)
