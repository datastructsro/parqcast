"""Connection protocols for deployment-agnostic database access.

Three protocols, from narrowest to widest:

- :class:`ReadCursor` — execute / fetch. Satisfied by psycopg2's cursor
  and Odoo's ``sql_db.Cursor`` alike. Used by ``capabilities.probe``,
  ``version_gate.assert_supported``, the tracking helpers, and
  ``BaseCollector._execute``.
- :class:`Connection` — transaction control and streaming-cursor factory.
  Used by the orchestrator's commit/rollback gates.
- :class:`DatabaseEnv` — the combined ``env`` object that collectors and
  the orchestrator accept. Satisfied by ``OdooEnvShim`` (tests),
  ``OdooAdapter`` (addon), and similar adapters in sibling repos.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Protocol, runtime_checkable


@runtime_checkable
class ReadCursor(Protocol):
    """Minimal cursor shape used by parqcast.

    The ``params`` argument mirrors psycopg2's DB-API behaviour: a positional
    sequence, a named mapping, or None. Positional-only so callers can't
    pass a keyword (psycopg2 also accepts positional only).
    """

    def execute(
        self,
        sql: str,
        params: Sequence[object] | Mapping[str, object] | None = None,
        /,
    ) -> object: ...

    def fetchone(self) -> tuple[object, ...] | None: ...

    def fetchall(self) -> list[tuple[object, ...]]: ...


@runtime_checkable
class Connection(Protocol):
    """Raw psycopg2-like connection for streaming and transaction control."""

    autocommit: bool

    def cursor(self, name: str | None = None) -> ReadCursor: ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...


@runtime_checkable
class DatabaseEnv(Protocol):
    """The minimal environment that collectors and orchestrator need.

    Replaces the duck-typed ``env`` that flows through the system.
    Satisfied by :class:`OdooEnvShim` (tests), :class:`OdooAdapter` (Odoo
    addon), and any sibling adapter presenting the same two attributes.
    """

    cr: ReadCursor
    conn: Connection
