import base64
from typing import Optional
from urllib.parse import quote_plus

from ..core.config import settings
import datetime

# Lazy import for azure SDK to avoid hard dependency during lightweight runs
_blob_service_client = None


def _ensure_client():
    global _blob_service_client
    if _blob_service_client is None:
        try:
            from azure.storage.blob import BlobServiceClient
            _blob_service_client = BlobServiceClient.from_connection_string(settings.AZURE_STORAGE_CONNECTION_STRING)
        except Exception:
            _blob_service_client = None
    return _blob_service_client


def generate_sas_url(container: str, blob_name: str, expiry_seconds: int = 3600) -> Optional[str]:
    """Generate a read-only SAS URL for the given blob. Returns None on failure or if SDK not installed."""
    if not settings.AZURE_STORAGE_CONNECTION_STRING:
        return None
    try:
        # Parse connection string for account name & key
        cs = settings.AZURE_STORAGE_CONNECTION_STRING
        parts = dict(p.split('=', 1) for p in cs.split(';') if '=' in p)
        account_name = parts.get('AccountName')
        account_key = parts.get('AccountKey')
        if not account_name or not account_key:
            return None
        # Prefer a module-level generate_blob_sas if present (useful for tests/mocking)
        gen = globals().get('generate_blob_sas')
        BlobSasPermissions_local = None
        if not gen:
            try:
                from azure.storage.blob import generate_blob_sas as _gen, BlobSasPermissions as _perm
                gen = _gen
                BlobSasPermissions_local = _perm
            except Exception:
                # SDK not available and no module-level generator -> cannot create SAS
                return None

        expiry = datetime.datetime.utcnow() + datetime.timedelta(seconds=expiry_seconds)
        if BlobSasPermissions_local is not None:
            sas = gen(
                account_name=account_name,
                container_name=container,
                blob_name=blob_name,
                account_key=account_key,
                permission=BlobSasPermissions_local(read=True),
                expiry=expiry,
            )
        else:
            # Call generator without real permission object (test fakes can accept it)
            sas = gen(
                account_name=account_name,
                container_name=container,
                blob_name=blob_name,
                account_key=account_key,
                permission=None,
                expiry=expiry,
            )
        if not sas:
            return None
        client = _ensure_client()
        if client is None:
            return None
        container_client = client.get_container_client(container)
        base_url = f"{container_client.url}/{quote_plus(blob_name)}"
        return f"{base_url}?{sas}"
    except Exception:
        return None


def upload_base64(container: str, blob_name: str, b64: str) -> Optional[str]:
    """Upload base64 audio to Azure Blob and return the blob URL (SAS-protected if configured).
    Returns None on error or if Azure not configured.
    """
    if not settings.AZURE_STORAGE_CONNECTION_STRING or not settings.AZURE_STORAGE_CONTAINER:
        return None
    client = _ensure_client()
    if client is None:
        return None
    try:
        container_client = client.get_container_client(container)
        # ensure container exists (idempotent)
        try:
            container_client.create_container()
        except Exception:
            pass
        blob_bytes = base64.b64decode(b64)
        blob_client = container_client.get_blob_client(blob_name)
        blob_client.upload_blob(blob_bytes, overwrite=True)
        # Construct URL (SAS may be added depending on settings)
        base_url = f"{container_client.url}/{quote_plus(blob_name)}"
        # Optionally generate SAS if configured
        try:
            ttl = int(getattr(settings, "AZURE_BLOB_SAS_TTL_SECONDS", 0) or 0)
        except Exception:
            ttl = 0
        if ttl > 0:
            sas_url = generate_sas_url(container, blob_name, expiry_seconds=ttl)
            if sas_url:
                return sas_url
        return base_url
    except Exception:
        return None
