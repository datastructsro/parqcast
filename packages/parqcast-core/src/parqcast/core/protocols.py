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
from typing import Any, NotRequired, Protocol, TypeAlias, TypedDict, runtime_checkable

# ---------------------------------------------------------------------------
# Named type aliases shared across the workspace.
# ---------------------------------------------------------------------------

SqlParams: TypeAlias = Sequence[object] | Mapping[str, object] | None
"""Positional or named parameters accepted by psycopg2's execute()."""

SqlWithParams: TypeAlias = tuple[str, SqlParams]
"""Return shape of ``BaseCollector.get_sql()``: a SQL string paired with
bind-parameters (or None). Kept as a named alias so collector subclasses
match the abstract signature verbatim."""

JsonDict: TypeAlias = dict[str, object]
"""A JSON-serializable dict payload.

Used for manifests, capability summaries, chunk metadata, and anywhere
else parqcast hands around shape-unconstrained record dicts that will
eventually be serialised to JSON. Values are ``object`` rather than a
nested JSON union because the consumers accept anything ``json.dumps``
can handle (via ``default=str`` if needed)."""

OdooRow: TypeAlias = tuple[object, ...]
"""One row returned by a psycopg2/Odoo cursor's ``fetchone``/``fetchall``.

Columns are positional; the tuple's arity depends on the SELECT clause."""


class ChunkMetadata(TypedDict):
    """Shape of the per-chunk metadata record.

    Produced by :func:`BaseCollector.to_parquet` and
    :func:`ExportChunk.get_metadata`; consumed by the orchestrator during
    upload and by :func:`build_manifest` when it assembles the run's
    manifest.json. Keeping this as a named TypedDict means the upload
    path gets ``meta["file"]: str`` without an ad-hoc cast at the call
    site.

    ``duration_seconds`` is ``NotRequired`` because it is populated only
    when the record comes from ``ExportChunk.get_metadata``;
    ``BaseCollector.to_parquet`` does not include it.
    """

    file: str
    rows: int
    bytes: int
    checksum: str
    collector: str
    duration_seconds: NotRequired[float]


@runtime_checkable
class ReadCursor(Protocol):
    """Minimal cursor shape used by parqcast.

    The ``params`` argument mirrors psycopg2's DB-API behaviour: a positional
    sequence, a named mapping, or None. Positional-only so callers can't
    pass a keyword (psycopg2 also accepts positional only).
    """

    def execute(self, sql: str, params: SqlParams = None, /) -> object: ...

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


# ---------------------------------------------------------------------------
# Odoo ORM surface — structural Protocols for what ingesters actually call.
# ---------------------------------------------------------------------------
#
# These Protocols do NOT model the full Odoo ORM. They capture only the
# methods and attributes parqcast's ingesters touch. Attribute access goes
# through ``__getattr__`` returning ``Any`` because Odoo resolves fields
# dynamically at runtime — pyright can't infer e.g. ``po.currency_id.id``
# without loading Odoo's actual models, which aren't pip-installable.
#
# Pragmatically, this gives us:
#   - compile-time checking of .create / .search / .browse / .write / .unlink
#     arities (the methods we explicitly declare),
#   - permissive field access (via __getattr__) at the boundary where we
#     cannot do better.


class OdooRecord(Protocol):
    """An Odoo record or recordset.

    Models the subset of ``BaseModel`` we call. ``__getattr__`` makes
    arbitrary field access permissive (typed as ``Any``) because Odoo
    resolves fields dynamically and parqcast can't enumerate them.
    """

    id: int

    def write(self, vals: Mapping[str, object]) -> bool: ...
    def unlink(self) -> bool: ...
    def __bool__(self) -> bool: ...
    def __len__(self) -> int: ...
    def __getattr__(self, name: str) -> Any: ...
    def __setattr__(self, name: str, value: Any) -> None: ...


class OdooModel(Protocol):
    """An Odoo model accessor — what ``env["<model>"]`` returns."""

    def create(
        self, vals: Mapping[str, object] | list[Mapping[str, object]]
    ) -> OdooRecord: ...
    def search(
        self,
        domain: Sequence[object],
        *,
        limit: int = 0,
        order: str = "",
    ) -> OdooRecord: ...
    def browse(self, ids: int | Sequence[int]) -> OdooRecord: ...


class OdooEnvironment(Protocol):
    """The minimal Odoo ``env`` surface used by parqcast's ingesters.

    Satisfied by Odoo's own ``odoo.api.Environment`` at runtime. Tests that
    exercise ingester logic can supply a stub implementing the same shape.
    """

    company: OdooRecord

    def __getitem__(self, model_name: str) -> OdooModel: ...
