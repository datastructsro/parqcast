from parqcast.core.version import V18
from parqcast.schemas.outbound import STOCK_QUANT_SCHEMA

from ..base import StockCollector


class StockQuantCollectorV18(StockCollector[V18]):
    """Stock quant collector for Odoo 18.

    v18 uses the legacy ``stock_quant_package`` table name (v19 renamed it
    to ``stock_package``). Probe discovers which table is present.
    """

    name = "stock_quant"
    schema = STOCK_QUANT_SCHEMA
    required_tables = {"stock_quant"}

    pk_column = "sq.id"
    primary_table = "stock_quant"

    optional_columns = {
        "stock_lot.expiration_date": ("lot.expiration_date", "NULL::timestamp"),
    }

    def get_sql(self):
        lang1 = self.caps.lang(1) or "en_US"
        pkg_table = "stock_package" if self.caps.has_table("stock_package") else "stock_quant_package"
        lot_exp = self.col_or_default("stock_lot", "expiration_date", "NULL::timestamp")

        return (
            f"""
            SELECT
                sq.id, sq.product_id,
                pt.name->>'{lang1}', pp.default_code,
                sq.location_id, sl.complete_name, sl.usage,
                sl.warehouse_id, sw.code,
                sq.quantity, sq.reserved_quantity,
                sq.lot_id, lot.name, {lot_exp},
                sq.package_id, pack.name,
                sq.owner_id, rp.name,
                sq.in_date,
                sq.company_id
            FROM stock_quant sq
            JOIN product_product pp ON sq.product_id = pp.id
            JOIN product_template pt ON pp.product_tmpl_id = pt.id
            JOIN stock_location sl ON sq.location_id = sl.id
            LEFT JOIN stock_warehouse sw ON sl.warehouse_id = sw.id
            LEFT JOIN stock_lot lot ON sq.lot_id = lot.id
            LEFT JOIN {pkg_table} pack ON sq.package_id = pack.id
            LEFT JOIN res_partner rp ON sq.owner_id = rp.id
            WHERE sq.quantity != 0 OR sq.reserved_quantity != 0
        """,
            None,
        )
