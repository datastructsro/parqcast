from parqcast.core.capabilities import OdooCapabilities
from parqcast.core.version import V18
from parqcast.schemas.outbound import STOCK_PACKAGE_SCHEMA, STOCK_PACKAGE_TYPE_SCHEMA

from ..base import StockCollector


class StockPackageTypeCollectorV18(StockCollector[V18]):
    """``stock_package_type`` columns are identical in v18 and v19 — SQL is
    a straight copy."""

    name = "stock_package_type"
    schema = STOCK_PACKAGE_TYPE_SCHEMA
    required_tables = {"stock_package_type"}

    def get_sql(self):
        return (
            """
            SELECT
                spt.id, spt.name, spt.barcode,
                COALESCE(spt.height, 0),
                COALESCE(spt.width, 0),
                COALESCE(spt.packaging_length, 0),
                COALESCE(spt.max_weight, 0),
                COALESCE(spt.base_weight, 0),
                spt.company_id
            FROM stock_package_type spt
        """,
            None,
        )


class StockPackageCollectorV18(StockCollector[V18]):
    """Stock package collector for Odoo 18.

    v18 uses the legacy ``stock_quant_package`` table name (v19 renamed it
    to ``stock_package``). The capability probe discovers whichever exists
    and we select from it.

    ``pack_date`` is ``fields.Date`` in Odoo and stored as PostgreSQL
    ``date``; the outbound schema wants ``OdooDate = pa.timestamp(...)``.
    Cast in SQL so psycopg2 yields ``datetime.datetime`` (pyarrow refuses
    to coerce ``datetime.date`` to timestamp).
    """

    name = "stock_package"
    schema = STOCK_PACKAGE_SCHEMA
    depends_on = ["stock_package_type"]

    @classmethod
    def is_compatible(cls, caps: OdooCapabilities[V18]) -> bool:
        if not caps.has_module("stock"):
            return False
        return caps.has_table("stock_package") or caps.has_table("stock_quant_package")

    def _pkg_table(self) -> str:
        if self.caps.has_table("stock_package"):
            return "stock_package"
        return "stock_quant_package"

    def get_sql(self):
        pkg = self._pkg_table()

        pack_date = "sp.pack_date::timestamp" if self.caps.has_column(pkg, "pack_date") else "NULL::timestamp"
        location_id = "sp.location_id" if self.caps.has_column(pkg, "location_id") else "NULL::int"
        shipping_weight = "COALESCE(sp.shipping_weight, 0)" if self.caps.has_column(pkg, "shipping_weight") else "0"

        if self.caps.has_column(pkg, "package_type_id") and self.caps.has_table("stock_package_type"):
            type_id = "sp.package_type_id"
            type_join = "LEFT JOIN stock_package_type spt ON sp.package_type_id = spt.id"
        else:
            type_id = "NULL::int"
            type_join = ""

        return (
            f"""
            SELECT
                sp.id, sp.name,
                {pack_date},
                {location_id},
                {type_id},
                {shipping_weight},
                sp.company_id
            FROM {pkg} sp
            {type_join}
        """,
            None,
        )
