"""Runtime gate that refuses to operate on unsupported Odoo majors.

Call :func:`assert_supported` once per parqcast entrypoint (cron tick,
addon registry hook) before any collector or ingester touches Odoo.
The function consults :data:`parqcast.core.registry.REGISTRY` and raises
:class:`UnsupportedOdooVersionError` when the DB reports a major version
that is not registered.
"""

from __future__ import annotations

from typing import Protocol, cast

from parqcast.core.registry import REGISTRY
from parqcast.core.version import SupportedVersionStr, UnsupportedOdooVersionError


class _Cursor(Protocol):
    def execute(self, sql: str) -> object: ...
    def fetchone(self) -> tuple[object, ...] | None: ...


def _read_odoo_major(cr: _Cursor) -> str:
    """Return the Odoo major (e.g. ``"19"``) reported by the connected DB.

    Reads ``ir_module_module.latest_version`` of the ``base`` module — the
    same source of truth used by :func:`parqcast.core.capabilities.probe`.
    Returns an empty string if the row is missing.
    """
    cr.execute(
        "SELECT latest_version FROM ir_module_module "
        "WHERE name = 'base' AND state = 'installed' LIMIT 1"
    )
    row = cr.fetchone()
    if not row or not row[0]:
        return ""
    return str(row[0]).split(".", 1)[0]


def assert_supported(cr: _Cursor) -> SupportedVersionStr:
    """Verify the DB is an Odoo major parqcast supports; return the tag.

    Raises :class:`UnsupportedOdooVersionError` if the detected major is not
    in :data:`REGISTRY`. The error message names the detected major and the
    supported set so the operator can diagnose immediately.
    """
    major = _read_odoo_major(cr)
    if major and major in REGISTRY:
        return cast(SupportedVersionStr, major)
    supported = sorted(REGISTRY.keys()) or ["<none>"]
    detected = major or "<unknown>"
    raise UnsupportedOdooVersionError(
        f"parqcast supports Odoo {supported}; detected Odoo {detected}. "
        f"Install a matching parqcast release for this Odoo major."
    )
