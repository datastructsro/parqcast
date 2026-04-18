"""Narrow-cast helpers around :class:`ReadCursor` fetches.

The :class:`ReadCursor` Protocol returns rows as ``tuple[object, ...]`` — the
honest shape, because psycopg2 surfaces SQL values as ``object``. Callers
that know their SELECT clause can work with the values directly; the
helpers below give them ``Any``-typed tuples so destructuring and assigning
to typed fields doesn't require a cast at every call site.

Use :func:`fetch_one` when a row is mandatory (it raises if the cursor
returned nothing). Use :func:`fetch_one_or_none` when the SELECT may yield
zero rows. Use :func:`fetch_all` to materialise all rows in one call.

Keep these helpers thin — they're just narrowing casts around the Protocol
methods. Any non-trivial behaviour should live in the caller.
"""

from __future__ import annotations

from typing import Any, cast

from parqcast.core.protocols import ReadCursor


def fetch_one(cr: ReadCursor) -> tuple[Any, ...]:
    """Return one row from the cursor; raise if none was fetched."""
    row = cr.fetchone()
    if row is None:
        raise RuntimeError("Expected at least one row from the cursor")
    return cast("tuple[Any, ...]", row)


def fetch_one_or_none(cr: ReadCursor) -> tuple[Any, ...] | None:
    """Return one row from the cursor, or None if empty."""
    return cast("tuple[Any, ...] | None", cr.fetchone())


def fetch_all(cr: ReadCursor) -> list[tuple[Any, ...]]:
    """Return all rows from the cursor, each as an ``Any``-valued tuple."""
    return cast("list[tuple[Any, ...]]", cr.fetchall())
