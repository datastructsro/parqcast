from pathlib import Path
from typing import BinaryIO

from .base import BaseTransport


class LocalFSTransport(BaseTransport):
    def __init__(self, base_path: str | Path):
        self.base = Path(base_path)
        self.base.mkdir(parents=True, exist_ok=True)

    def upload_file(self, prefix: str, filename: str, data: BinaryIO) -> None:
        dest = self.base / prefix / filename
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data.read())

    def download_file(self, prefix: str, filename: str) -> bytes:
        path = self.base / prefix / filename
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        return path.read_bytes()

    def list_files(self, prefix: str) -> list[str]:
        d = self.base / prefix
        if not d.exists():
            return []
        return sorted(f.name for f in d.iterdir() if f.is_file())
