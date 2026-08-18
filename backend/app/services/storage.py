"""Document storage.

Files never live in the database. Keys are content-addressed under the firm so a leaked
key from one tenant cannot name another tenant's object.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from app.core.config import settings


@dataclass
class StoredObject:
    key: str
    sha256: str
    byte_size: int


def content_key(firm_id: str, engagement_id: str, filename: str, digest: str) -> str:
    safe = filename.replace("/", "_")[:120]
    return f"firms/{firm_id}/engagements/{engagement_id}/{digest[:16]}/{safe}"


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


class ObjectStore:
    def __init__(self) -> None:
        self._client = None

    def _s3(self):
        if self._client is None:
            import boto3

            self._client = boto3.client(
                "s3",
                endpoint_url=settings.s3_endpoint,
                aws_access_key_id=settings.s3_access_key,
                aws_secret_access_key=settings.s3_secret_key,
                region_name=settings.s3_region,
            )
        return self._client

    def put(self, firm_id: str, engagement_id: str, filename: str, raw: bytes) -> StoredObject:
        sha = digest(raw)
        key = content_key(firm_id, engagement_id, filename, sha)
        self._s3().put_object(Bucket=settings.s3_bucket, Key=key, Body=raw)
        return StoredObject(key=key, sha256=sha, byte_size=len(raw))

    def get(self, key: str) -> bytes:
        return self._s3().get_object(Bucket=settings.s3_bucket, Key=key)["Body"].read()

    def presign(self, key: str, expires: int = 900) -> str:
        return self._s3().generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.s3_bucket, "Key": key},
            ExpiresIn=expires,
        )


class InMemoryStore(ObjectStore):
    """Test and offline double. Same interface, no network."""

    def __init__(self) -> None:
        super().__init__()
        self.objects: dict[str, bytes] = {}

    def put(self, firm_id: str, engagement_id: str, filename: str, raw: bytes) -> StoredObject:
        sha = digest(raw)
        key = content_key(firm_id, engagement_id, filename, sha)
        self.objects[key] = raw
        return StoredObject(key=key, sha256=sha, byte_size=len(raw))

    def get(self, key: str) -> bytes:
        return self.objects[key]

    def presign(self, key: str, expires: int = 900) -> str:
        return f"memory://{key}"
