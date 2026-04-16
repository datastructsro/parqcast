from parqcast.schemas.outbound import STOCK_PACKAGE_SCHEMA, STOCK_PACKAGE_TYPE_SCHEMA

from .base import StockCollector


class StockPackageTypeCollector(StockCollector):
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


class StockPackageCollector(StockCollector):
    """Odoo 19: stock_quant_package -> stock_package."""

    name = "stock_package"
    schema = STOCK_PACKAGE_SCHEMA
    depends_on = ["stock_package_type"]

    @classmethod
    def is_compatible(cls, caps):
        if not caps.has_module("stock"):
            return False
        return caps.has_table("stock_package") or caps.has_table("stock_quant_package")

    def _pkg_table(self):
        if self.caps.has_table("stock_package"):
            return "stock_package"
        return "stock_quant_package"

    def get_sql(self):
        pkg = self._pkg_table()

        pack_date = "sp.pack_date" if self.caps.has_column(pkg, "pack_date") else "NULL::date"
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
