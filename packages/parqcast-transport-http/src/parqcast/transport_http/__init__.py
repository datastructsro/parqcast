"""HTTP transport — uploads raw Parquet files to parqcast-server."""

import json
from typing import BinaryIO
from urllib import request as urllib_request
from urllib.error import HTTPError

from parqcast.transport.base import BaseTransport


class HttpTransport(BaseTransport):
    """Upload/download raw files via the parqcast-server HTTP API.

    Args:
        server_url: Base URL of the parqcast-server (e.g. "http://localhost:8420")
        api_key: Static API key for X-API-Key header
        namespace: Top-level namespace for data organization
    """

    def __init__(self, server_url: str, api_key: str, namespace: str = "parqcast"):
        self.server_url = server_url.rstrip("/")
        self.api_key = api_key
        self.namespace = namespace

    def _request(self, method: str, path: str, data: bytes, content_type: str) -> bytes:
        url = f"{self.server_url}{path}"
        headers = {"X-API-Key": self.api_key, "Content-Type": content_type}
        req = urllib_request.Request(url, data=data, headers=headers, method=method)
        with urllib_request.urlopen(req, timeout=60) as resp:
            return resp.read()

    def upload_file(self, prefix: str, filename: str, data: BinaryIO) -> None:
        raw = data.read()
        if filename.endswith(".json"):
            self._request("POST", f"/upload/{self.namespace}/_manifest", raw, "application/json")
        else:
            self._request("POST", f"/upload/{self.namespace}/{prefix}", raw, "application/octet-stream")

    def download_file(self, prefix: str, filename: str) -> bytes:
        url = f"{self.server_url}/download/{self.namespace}/{prefix}/{filename}"
        headers = {"X-API-Key": self.api_key}
        req = urllib_request.Request(url, headers=headers)
        try:
            with urllib_request.urlopen(req, timeout=60) as resp:
                return resp.read()
        except HTTPError as e:
            if e.code == 404:
                raise FileNotFoundError(f"Not found: {prefix}/{filename}") from e
            raise

    def list_files(self, prefix: str) -> list[str]:
        url = f"{self.server_url}/browse/{self.namespace}/{prefix}"
        headers = {"X-API-Key": self.api_key}
        req = urllib_request.Request(url, headers=headers)
        try:
            with urllib_request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode())
        except HTTPError as e:
            if e.code == 404:
                return []
            raise
        return [entry["name"] for entry in data.get("entries", []) if entry["type"] == "file"]
