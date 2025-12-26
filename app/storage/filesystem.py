import os
import base64
from pathlib import Path
from typing import Dict

from ..core.config import settings

STORAGE_DIR = Path(settings.STORAGE_DIR)
STORAGE_DIR.mkdir(parents=True, exist_ok=True)


def save_bytes(filename: str, b: bytes) -> str:
    path = STORAGE_DIR / filename
    with open(path, "wb") as f:
        f.write(b)
    return str(path.resolve())


def save_base64(filename: str, b64: str) -> str:
    b = base64.b64decode(b64)
    return save_bytes(filename, b)


def get_path(filename: str) -> str:
    path = STORAGE_DIR / filename
    if path.exists():
        return str(path.resolve())
    raise FileNotFoundError


def list_files():
    return [str(p) for p in STORAGE_DIR.iterdir() if p.is_file()]
