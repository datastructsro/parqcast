# Copyright 2025 DataStruct s.r.o.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

"""Adapt Odoo's env object to satisfy the DatabaseEnv protocol.

The key subtlety: Odoo's cursor .commit() manages savepoints, so we
delegate commit/rollback through the cursor rather than hitting the
raw psycopg2 connection directly.
"""


class _OdooConnection:
    """Wraps Odoo's cursor and its underlying psycopg2 connection.

    Presents the Connection protocol while preserving Odoo savepoint semantics.
    """

    def __init__(self, odoo_cr):
        self._cr = odoo_cr
        self._raw = self._resolve_raw(odoo_cr)

    @staticmethod
    def _resolve_raw(cr):
        """Extract the underlying psycopg2 connection."""
        if hasattr(cr, "_cnx"):
            return cr._cnx
        if hasattr(cr, "connection"):
            return cr.connection
        if hasattr(cr, "_obj") and hasattr(cr._obj, "connection"):
            return cr._obj.connection
        raise RuntimeError("Cannot resolve psycopg2 connection from Odoo cursor")

    @property
    def autocommit(self):
        return self._raw.autocommit

    @autocommit.setter
    def autocommit(self, value):
        self._raw.autocommit = value

    def cursor(self, name=None):
        """Return a psycopg2 cursor (named for server-side streaming)."""
        if name:
            return self._raw.cursor(name=name)
        return self._raw.cursor()

    def commit(self):  # pylint: disable=invalid-commit
        """Commit via Odoo cursor to preserve savepoint semantics."""
        if hasattr(self._cr, "commit"):
            self._cr.commit()  # pylint: disable=invalid-commit
        elif not self._raw.autocommit:
            self._raw.commit()  # pylint: disable=invalid-commit

    def rollback(self):
        self._raw.rollback()


class OdooAdapter:
    """Wraps Odoo's self.env into the DatabaseEnv protocol.

    Usage in cron model::

        from .env_adapter import OdooAdapter

        adapter = OdooAdapter(self.env)
        orchestrator = Orchestrator(adapter, transport, ...)
    """

    def __init__(self, odoo_env):
        self.cr = odoo_env.cr
        self.conn = _OdooConnection(odoo_env.cr)
