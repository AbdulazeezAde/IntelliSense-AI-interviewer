import os
import tempfile
import time
from typing import Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def _guess_suffix_from_url(url: str) -> str:
    path = url.split('?')[0]
    base = os.path.basename(path)
    if '.' in base:
        ext = base.split('.')[-1]
        return f'.{ext}'
    return '.wav'


def _create_session_with_retries(retries: int = 3, backoff_factor: float = 0.5, status_forcelist=(500, 502, 503, 504)) -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
        allowed_methods=["GET", "HEAD"]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def fetch_audio_to_temp(audio_url: str, timeout: int = 10, max_bytes: int = 50 * 1024 * 1024, retries: int = 3, backoff_factor: float = 0.5) -> Optional[str]:
    """Fetch an audio URL or cloud identifier to a local temp file.

    Supports:
      - http(s) URLs (including signed URLs/SAS)
      - s3://bucket/key (uses boto3 if available)
      - azure://container/blob_path (uses azure-storage-blob if available)

    Retries with exponential backoff on transient HTTP errors.

    Returns a local file path on success, raises an Exception on failure.
    """
    # S3 support removed. This project uses HTTP(S) and Azure blob sources for remote audio.
    # If S3 support is required in the future, reintroduce it behind an optional dependency and tests.

    # Azure direct fetch helper (azure://container/blob_path)
    if audio_url.startswith('azure://'):
        try:
            from azure.storage.blob import BlobServiceClient
        except Exception as e:
            raise RuntimeError("azure-storage-blob required for azure:// downloads") from e
        _, _, rest = audio_url.partition('azure://')
        parts = rest.split('/', 1)
        if len(parts) != 2:
            raise ValueError('azure URL must be of form azure://container/blob')
        container, blob = parts[0], parts[1]
        client = BlobServiceClient.from_connection_string(os.getenv('AZURE_STORAGE_CONNECTION_STRING'))
        container_client = client.get_container_client(container)
        blob_client = container_client.get_blob_client(blob)
        downloader = blob_client.download_blob()
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=_guess_suffix_from_url(blob))
        try:
            total = 0
            stream = downloader.chunks()
            for chunk in stream:
                total += len(chunk)
                if total > max_bytes:
                    raise ValueError('downloaded data exceeds max_bytes limit')
                tmp.write(chunk)
            tmp.flush()
            return tmp.name
        finally:
            try:
                tmp.close()
            except Exception:
                pass

    # Otherwise, treat as an HTTP/HTTPS resource and use requests with retries
    session = _create_session_with_retries(retries=retries, backoff_factor=backoff_factor)

    attempt = 0
    last_exc = None
    while attempt <= retries:
        try:
            resp = session.get(audio_url, stream=True, timeout=timeout)
            resp.raise_for_status()
            suffix = _guess_suffix_from_url(audio_url)
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
            total = 0
            try:
                for chunk in resp.iter_content(chunk_size=8192):
                    if not chunk:
                        continue
                    total += len(chunk)
                    if total > max_bytes:
                        raise ValueError("downloaded data exceeds max_bytes limit")
                    tmp.write(chunk)
                tmp.flush()
                return tmp.name
            finally:
                try:
                    tmp.close()
                except Exception:
                    pass
        except Exception as e:
            last_exc = e
            if attempt == retries:
                break
            sleep = backoff_factor * (2 ** attempt)
            time.sleep(sleep)
            attempt += 1
    raise last_exc

