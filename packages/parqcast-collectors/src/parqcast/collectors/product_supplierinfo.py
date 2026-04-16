from parqcast.schemas.outbound import PRODUCT_SUPPLIERINFO_SCHEMA

from .base import PurchaseCollector


class ProductSupplierinfoCollector(PurchaseCollector):
    name = "product_supplierinfo"
    schema = PRODUCT_SUPPLIERINFO_SCHEMA
    depends_on = ["product"]
    required_tables = {"product_supplierinfo"}

    optional_columns = {
        "product_supplierinfo.batching_window": (
            "COALESCE(ps.batching_window, 0)",
            "0",
        ),
        "product_supplierinfo.is_subcontractor": (
            "COALESCE(ps.is_subcontractor, false)",
            "false",
        ),
    }

    pk_column = "ps.id"
    primary_table = "product_supplierinfo"

    def get_sql(self):
        batch_col = self.col_or_default("product_supplierinfo", "batching_window", "0")
        subcon_col = self.col_or_default("product_supplierinfo", "is_subcontractor", "false")

        return (
            f"""
            SELECT
                ps.id, ps.product_tmpl_id, ps.product_id,
                ps.partner_id, rp.name,
                ps.delay, ps.min_qty, ps.price,
                ps.currency_id, rc.name,
                ps.sequence,
                ps.date_start, ps.date_end,
                {batch_col},
                {subcon_col}
            FROM product_supplierinfo ps
            JOIN res_partner rp ON ps.partner_id = rp.id
            LEFT JOIN res_currency rc ON ps.currency_id = rc.id
        """,
            None,
        )
