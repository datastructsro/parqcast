from parqcast.core.version import V18
from parqcast.schemas.outbound import SALE_ORDER_SCHEMA

from ..base import SaleCollector


class SaleOrderCollectorV18(SaleCollector[V18]):
    """Sale-order column surface is stable across v18 and v19 — same
    picking_policy / amount_untaxed / delivery_status / invoice_status
    columns exist in both majors."""

    name = "sale_order"
    schema = SALE_ORDER_SCHEMA
    depends_on = ["partner", "stock_location"]
    required_tables = {"sale_order"}

    pk_column = "so.id"
    primary_table = "sale_order"

    def get_sql(self):
        return (
            """
            SELECT
                so.id, so.name, so.state,
                so.partner_id,
                so.date_order, so.commitment_date,
                so.warehouse_id, sw.code,
                so.picking_policy,
                COALESCE(so.amount_untaxed, 0),
                COALESCE(so.amount_total, 0),
                so.currency_id,
                so.invoice_status,
                so.delivery_status,
                so.company_id
            FROM sale_order so
            LEFT JOIN stock_warehouse sw ON so.warehouse_id = sw.id
        """,
            None,
        )
