"""S3 transport — supports AWS S3 and S3-compatible stores (MinIO, LocalStack)."""

import io
from typing import BinaryIO

import boto3

from parqcast.transport.base import BaseTransport


class S3Transport(BaseTransport):
    """Upload/download files via S3 or S3-compatible API.

    Args:
        bucket: S3 bucket name
        prefix: Key prefix within bucket (default: "parqcast")
        endpoint_url: Override endpoint for S3-compatible stores (MinIO, LocalStack).
                      None for real AWS S3.
    """

    def __init__(
        self,
        bucket: str,
        prefix: str = "parqcast",
        endpoint_url: str | None = None,
        aws_access_key_id: str | None = None,
        aws_secret_access_key: str | None = None,
        region_name: str | None = None,
    ):
        self.bucket = bucket
        self.prefix = prefix
        kwargs = {}
        if endpoint_url:
            kwargs["endpoint_url"] = endpoint_url
        if aws_access_key_id:
            kwargs["aws_access_key_id"] = aws_access_key_id
        if aws_secret_access_key:
            kwargs["aws_secret_access_key"] = aws_secret_access_key
        if region_name:
            kwargs["region_name"] = region_name
        self.s3 = boto3.client("s3", **kwargs)

    def _key(self, prefix: str, filename: str) -> str:
        return f"{self.prefix}/{prefix}/{filename}"

    def upload_file(self, prefix: str, filename: str, data: BinaryIO) -> None:
        key = self._key(prefix, filename)
        self.s3.upload_fileobj(data, self.bucket, key)

    def download_file(self, prefix: str, filename: str) -> bytes:
        key = self._key(prefix, filename)
        buf = io.BytesIO()
        self.s3.download_fileobj(self.bucket, key, buf)
        return buf.getvalue()

    def list_files(self, prefix: str) -> list[str]:
        full_prefix = f"{self.prefix}/{prefix}/"
        resp = self.s3.list_objects_v2(Bucket=self.bucket, Prefix=full_prefix)
        files = []
        for obj in resp.get("Contents", []):
            filename = obj["Key"].removeprefix(full_prefix)
            if filename and "/" not in filename:
                files.append(filename)
        return sorted(files)
