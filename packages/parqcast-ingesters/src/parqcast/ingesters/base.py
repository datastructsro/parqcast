from abc import ABC, abstractmethod

import pyarrow as pa


class IngestResult:
    def __init__(self, created: int = 0, updated: int = 0, errors: int = 0, messages: list[str] | None = None):
        self.created = created
        self.updated = updated
        self.errors = errors
        self.messages = messages or []

    def __repr__(self):
        return f"IngestResult(created={self.created}, updated={self.updated}, errors={self.errors})"


class BaseIngester(ABC):
    decision_type: str

    @abstractmethod
    def apply(self, decisions: pa.Table, env) -> IngestResult: ...

    @abstractmethod
    def cleanup_previous(self, env, company_id: int) -> int: ...
