"""Connection protocols for deployment-agnostic database access.

Three protocols, from narrowest to widest:
- ReadCursor: execute/fetch (capabilities, tracking, simple queries)
- Connection: psycopg2-like connection (streaming server-side cursors, commits)
- DatabaseEnv: the combined env object that collectors and orchestrator accept
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class ReadCursor(Protocol):
    """Minimal read-only cursor used by capabilities.probe(), tracking, and _execute()."""

    def execute(self, sql: str, params: Any = None) -> None: ...
    def fetchall(self) -> list[tuple]: ...
    def fetchone(self) -> tuple | None: ...


@runtime_checkable
class Connection(Protocol):
    """Raw psycopg2-like connection for streaming and transaction control."""

    autocommit: bool

    def cursor(self, name: str | None = None) -> Any: ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...


@runtime_checkable
class DatabaseEnv(Protocol):
    """The minimal environment that collectors and orchestrator need.

    Replaces the duck-typed ``env`` that flows through the system.
    Satisfied by: OdooEnvShim (tests), OdooAdapter (Odoo addon), LambdaEnv (Lambda).
    """

    cr: ReadCursor
    conn: Connection
