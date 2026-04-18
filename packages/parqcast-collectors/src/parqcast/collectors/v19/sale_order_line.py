from parqcast.core.version import V19
from parqcast.schemas.outbound import SALE_ORDER_LINE_SCHEMA

from ..base import SaleCollector


class SaleOrderLineCollectorV19(SaleCollector[V19]):
    """Sale order lines on Odoo 19.

    ``sale.order.line.product_uom_id`` is the canonical field (it has been
    named ``product_uom_id`` on this model for several releases — the
    rename in the ``product_uom → product_uom_id`` story applies to
    ``purchase.order.line``, not this model). ``uom.name`` is a translatable
    ``Char`` stored as JSONB Odoo-wide since 16/17.
    """

    name = "sale_order_line"
    schema = SALE_ORDER_LINE_SCHEMA
    depends_on = ["product", "partner", "stock_location"]
    required_tables = {"sale_order", "sale_order_line"}
    pk_column = "sol.id"
    primary_table = "sale_order_line"

    def get_sql(self):
        lang1 = self.caps.lang(1) or "en_US"
        return (
            f"""
            SELECT
                sol.id, so.id, so.name,
                sol.product_id, pt.name->>'{lang1}',
                sol.product_uom_qty, sol.qty_delivered,
                COALESCE(sol.qty_invoiced, 0),
                sol.product_uom_id, u.name->>'{lang1}',
                COALESCE(sol.price_unit, 0),
                COALESCE(sol.discount, 0),
                COALESCE(sol.price_subtotal, 0),
                COALESCE(sol.customer_lead, 0),
                so.partner_id, rp.name, rp.is_company,
                so.commitment_date, so.date_order,
                so.state, sol.state,
                so.warehouse_id, sw.code,
                so.picking_policy
            FROM sale_order_line sol
            JOIN sale_order so ON sol.order_id = so.id
            JOIN product_product pp ON sol.product_id = pp.id
            JOIN product_template pt ON pp.product_tmpl_id = pt.id
            LEFT JOIN uom_uom u ON sol.product_uom_id = u.id
            LEFT JOIN res_partner rp ON so.partner_id = rp.id
            LEFT JOIN stock_warehouse sw ON so.warehouse_id = sw.id
            WHERE sol.product_id IS NOT NULL
        """,
            None,
        )
