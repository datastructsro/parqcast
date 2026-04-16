from abc import ABC, abstractmethod
from typing import BinaryIO


class BaseTransport(ABC):
    @abstractmethod
    def upload_file(self, prefix: str, filename: str, data: BinaryIO) -> None:
        """Upload a single file. data is a readable binary stream."""
        ...

    @abstractmethod
    def download_file(self, prefix: str, filename: str) -> bytes:
        """Download a single file, return its bytes."""
        ...

    @abstractmethod
    def list_files(self, prefix: str) -> list[str]:
        """List filenames under a prefix."""
        ...
