import os

class Settings:
    def __init__(self):
        self.REDIS_URL = os.getenv("REDIS_URL")
        self.STORAGE_DIR = os.getenv("STORAGE_DIR", "./storage")
        # AWS keys kept for backwards compatibility only; S3 support is not enabled in this repo by default
        self.AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET")
        self.AWS_REGION = os.getenv("AWS_REGION")
        # Azure Blob Storage
        self.AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        self.AZURE_STORAGE_CONTAINER = os.getenv("AZURE_STORAGE_CONTAINER")
        # SAS TTL for generated signed URLs (seconds). If 0 or unset, SAS won't be generated.
        self.AZURE_BLOB_SAS_TTL_SECONDS = int(os.getenv("AZURE_BLOB_SAS_TTL_SECONDS", "0"))

settings = Settings()
