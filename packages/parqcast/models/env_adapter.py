# Copyright 2025 DataStruct s.r.o.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

"""Adapt Odoo's env object to satisfy the DatabaseEnv protocol.

The key subtlety: Odoo's cursor .commit() manages savepoints, so we
delegate commit/rollback through the cursor rather than hitting the
raw psycopg2 connection directly.
"""

from typing import Any

from parqcast.core.protocols import Connection, ReadCursor


class _OdooConnection:
    """Wraps Odoo's cursor and its underlying psycopg2 connection.

    Presents the Connection protocol while preserving Odoo savepoint semantics.
    The underlying psycopg2 connection is opaque (Any) because we probe for
    it through several version-specific attributes that aren't reflected in
    the ``ReadCursor`` Protocol.
    """

    def __init__(self, odoo_cr: ReadCursor) -> None:
        self._cr: ReadCursor = odoo_cr
        self._raw: Any = self._resolve_raw(odoo_cr)

    @staticmethod
    def _resolve_raw(cr: ReadCursor) -> Any:
        """Extract the underlying psycopg2 connection.

        Odoo's cursor wraps psycopg2 in different ways across versions
        (``_cnx`` on classic cursors, ``connection`` on newer wrappers,
        ``_obj.connection`` on test cursors). We probe each in turn.
        """
        cr_any: Any = cr
        if hasattr(cr_any, "_cnx"):
            return cr_any._cnx
        if hasattr(cr_any, "connection"):
            return cr_any.connection
        if hasattr(cr_any, "_obj") and hasattr(cr_any._obj, "connection"):
            return cr_any._obj.connection
        raise RuntimeError("Cannot resolve psycopg2 connection from Odoo cursor")

    @property
    def autocommit(self) -> bool:
        return bool(self._raw.autocommit)

    @autocommit.setter
    def autocommit(self, value: bool) -> None:
        self._raw.autocommit = value

    def cursor(self, name: str | None = None) -> ReadCursor:
        """Return a psycopg2 cursor (named for server-side streaming)."""
        if name:
            return self._raw.cursor(name=name)
        return self._raw.cursor()

    def commit(self) -> None:  # pylint: disable=invalid-commit
        """Commit via Odoo cursor to preserve savepoint semantics."""
        cr_any: Any = self._cr
        if hasattr(cr_any, "commit"):
            cr_any.commit()  # pylint: disable=invalid-commit
        elif not self._raw.autocommit:
            self._raw.commit()  # pylint: disable=invalid-commit

    def rollback(self) -> None:
        self._raw.rollback()


class OdooAdapter:
    """Wraps Odoo's self.env into the DatabaseEnv protocol.

    Usage in cron model::

        from .env_adapter import OdooAdapter

        adapter = OdooAdapter(self.env)
        orchestrator = Orchestrator(adapter, transport, ...)
    """

    def __init__(self, odoo_env: Any) -> None:
        self.cr: ReadCursor = odoo_env.cr
        # Declare the public attribute as ``Connection`` (the Protocol) rather
        # than ``_OdooConnection``: the DatabaseEnv protocol's ``conn`` is
        # mutable, so structural matching needs invariance — declaring the
        # narrower concrete type here would fail Protocol assignment at the
        # call site (``Orchestrator(env=adapter, ...)``).
        self.conn: Connection = _OdooConnection(odoo_env.cr)
