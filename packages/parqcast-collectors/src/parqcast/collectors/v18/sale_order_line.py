from parqcast.core.version import V18
from parqcast.schemas.outbound import SALE_ORDER_LINE_SCHEMA

from ..base import SaleCollector


class SaleOrderLineCollectorV18(SaleCollector[V18]):
    """Sale-order-line collector for Odoo 18.

    **Undocumented drift vs v19:** ``sale_order_line.product_uom`` in v18
    was renamed to ``product_uom_id`` in v19 — the same rename the
    evidence doc §2 documents for ``purchase_order_line``, but also
    applied to sale lines. The v19 source's ``_check`` constraint spells
    this out (``product_uom_id IS NOT NULL`` vs v18's
    ``product_uom IS NOT NULL``). This collector uses the v18 spelling.

    ``uom.name`` is translatable JSONB on both majors (pre-18 format).
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
                sol.product_uom, u.name->>'{lang1}',
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
            LEFT JOIN uom_uom u ON sol.product_uom = u.id
            LEFT JOIN res_partner rp ON so.partner_id = rp.id
            LEFT JOIN stock_warehouse sw ON so.warehouse_id = sw.id
            WHERE sol.product_id IS NOT NULL
        """,
            None,
        )
