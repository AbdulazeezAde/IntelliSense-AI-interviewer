import os
import shutil
import zipfile
from pathlib import Path
from typing import Optional

import requests

DEFAULT_VOSK_MODEL_URL = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
DEFAULT_MODEL_DIR = Path("models")


def download_and_extract_model(url: str = DEFAULT_VOSK_MODEL_URL, dest_dir: Optional[str] = None, chunk_size: int = 8192) -> str:
    """Downloads a VOSK model zip and extracts it to `dest_dir` (or ./models by default).
    Returns the path to the extracted model directory.

    Note: this function will raise on network errors. It's intended for developer setup only.
    """
    if dest_dir is None:
        dest_dir = DEFAULT_MODEL_DIR
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)

    # Download to a temp file
    resp = requests.get(url, stream=True, timeout=30)
    resp.raise_for_status()

    tmp_zip = dest_dir / "model_tmp.zip"
    with open(tmp_zip, "wb") as f:
        for chunk in resp.iter_content(chunk_size=chunk_size):
            if chunk:
                f.write(chunk)

    # Extract
    with zipfile.ZipFile(tmp_zip, 'r') as z:
        # Extract into dest_dir; the zip usually contains a single top-level folder
        z.extractall(dest_dir)

    # remove tmp zip
    tmp_zip.unlink()

    # attempt to locate a model folder under dest_dir
    for child in dest_dir.iterdir():
        if child.is_dir() and child.name.startswith("vosk-model"):
            return str(child.resolve())

    # fallback: return dest_dir
    return str(dest_dir.resolve())
