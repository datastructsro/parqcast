"""
Collector type hierarchy.

BaseCollector
├── CoreCollector          — always runs (uom, partner)
├── StockCollector         — requires 'stock' module
├── SaleCollector          — requires 'sale' module
├── PurchaseCollector      — requires 'purchase' module
├── MrpCollector           — requires 'mrp' module
└── PosCollector           — requires 'point_of_sale' module

Each collector declares:
  - required_modules: set[str]     — Odoo modules that must be installed
  - required_tables: set[str]      — DB tables that must exist
  - required_columns: dict[str, set[str]]  — columns that must exist on tables
  - optional_columns: dict[str, tuple[str, str]]  — {table.col: (sql_expr, default)}

Collectors implement get_sql() to return their SQL query. The orchestrator
calls collect(key_from, key_to) with keyset bounds for large tables.

No streaming / server-side cursors — all execution goes through env.cr
which is safe inside Odoo's transaction model.
"""

from __future__ import annotations

from abc import ABC
from decimal import Decimal
from hashlib import sha256
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from parqcast.core import __version__
from parqcast.core.capabilities import OdooCapabilities


class BaseCollector[V](ABC):
    name: str
    schema: pa.Schema
    depends_on: list[str] = []

    # Override in subclasses to declare requirements
    required_modules: set[str] = set()
    required_tables: set[str] = set()
    required_columns: dict[str, set[str]] = {}  # table -> {col, col, ...}
    optional_columns: dict[str, tuple[str, str]] = {}  # "table.col" -> (sql_if_exists, sql_fallback)

    # Chunking configuration
    pk_column: str = "id"  # primary key for keyset pagination
    max_chunk_rows: int = 50_000  # max rows per sub-chunk
    primary_table: str = ""  # main FROM table name (for row estimation)

    def __init__(self, env, caps: OdooCapabilities[V]) -> None:
        self.env = env
        self.caps = caps

    def _stamped_schema(self) -> pa.Schema:
        """Return schema with parqcast and Odoo version metadata embedded."""
        meta = {
            b"parqcast_version": __version__.encode(),
            b"odoo_version": (self.caps.odoo_version or "unknown").encode(),
        }
        existing = self.schema.metadata or {}
        return self.schema.with_metadata({**existing, **meta})

    @classmethod
    def is_compatible(cls, caps: OdooCapabilities[V]) -> bool:
        for mod in cls.required_modules:
            if not caps.has_module(mod):
                return False
        for table in cls.required_tables:
            if not caps.has_table(table):
                return False
        for table, cols in cls.required_columns.items():
            for col in cols:
                if not caps.has_column(table, col):
                    return False
        return True

    # --- SQL generation (override in subclasses) ---

    def get_sql(self) -> tuple[str, tuple | None]:
        """Return (sql_string, params_or_None). Subclasses must implement this."""
        raise NotImplementedError(f"{self.__class__.__name__} must implement get_sql()")

    # --- Execution ---

    def collect(self, key_from: int = 0, key_to: int = 0) -> pa.Table:
        """Execute SQL with optional keyset bounds and return PyArrow Table.

        Uses env.cr (Odoo's cursor) — safe inside Odoo's transaction model.
        Memory is bounded by the orchestrator's chunk splitting.
        """
        sql, params = self.get_sql()
        sql = sql.rstrip().rstrip(";")

        # Apply keyset pagination bounds
        if key_from > 0 or key_to > 0:
            joiner = " AND" if self._sql_has_where(sql) else "\nWHERE"
            if key_from > 0:
                sql += f"{joiner} {self.pk_column} >= {key_from}"
                joiner = " AND"
            if key_to > 0:
                sql += f"{joiner} {self.pk_column} < {key_to}"
            sql += f"\nORDER BY {self.pk_column}"

        rows = self._execute(sql, params)
        return self._to_table(rows)

    def to_parquet(self, table: pa.Table, path: Path) -> dict:
        pq.write_table(table, path, compression="snappy")
        file_bytes = path.read_bytes()
        return {
            "file": f"{self.name}.parquet",
            "rows": table.num_rows,
            "bytes": len(file_bytes),
            "checksum": f"sha256:{sha256(file_bytes).hexdigest()}",
            "collector": self.name,
        }

    # --- Helpers ---

    @staticmethod
    def _sql_has_where(sql: str) -> bool:
        """Check if SQL has a WHERE clause after the last FROM."""
        upper = sql.upper()
        last_from = upper.rfind("FROM")
        if last_from < 0:
            return False
        return "WHERE" in upper[last_from:]

    def col_or_default(self, table: str, column: str, default: str = "NULL") -> str:
        """Return the column reference if it exists, else the default SQL expression."""
        key = f"{table}.{column}"
        if key in self.optional_columns:
            sql_if, sql_fallback = self.optional_columns[key]
            if self.caps.has_column(table, column):
                return sql_if
            return sql_fallback
        if self.caps.has_column(table, column):
            return f"{table}.{column}" if "." not in column else column
        return default

    def _execute(self, sql: str, params=None) -> list[tuple]:
        self.env.cr.execute(sql, params)
        return self.env.cr.fetchall()

    def _to_table(self, rows: list[tuple]) -> pa.Table:
        cols = {field.name: [] for field in self.schema}
        for row in rows:
            for i, field in enumerate(self.schema):
                val = row[i] if i < len(row) else None
                if isinstance(val, Decimal):
                    val = float(val)
                cols[field.name].append(val)
        return pa.table(cols, schema=self._stamped_schema())


# --- Type hierarchy tiers ---


class CoreCollector[V](BaseCollector[V]):
    """Always runs. No module requirements."""

    required_modules = set()


class StockCollector[V](BaseCollector[V]):
    """Requires the stock module."""

    required_modules = {"stock"}


class SaleCollector[V](BaseCollector[V]):
    """Requires the sale module."""

    required_modules = {"sale"}


class PurchaseCollector[V](BaseCollector[V]):
    """Requires the purchase module."""

    required_modules = {"purchase"}


class MrpCollector[V](BaseCollector[V]):
    """Requires the mrp (Manufacturing) module."""

    required_modules = {"mrp"}
    required_tables = {"mrp_production", "mrp_bom", "mrp_workcenter"}


class PosCollector[V](BaseCollector[V]):
    """Requires the point_of_sale module."""

    required_modules = {"point_of_sale"}


class MpsCollector[V](BaseCollector[V]):
    """Requires the mrp_mps (Master Production Schedule) module."""

    required_modules = {"mrp_mps"}


class QualityCollector[V](BaseCollector[V]):
    """Requires the quality module."""

    required_modules = {"quality"}
