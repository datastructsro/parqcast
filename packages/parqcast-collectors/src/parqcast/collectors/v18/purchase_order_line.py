from parqcast.core.version import V18
from parqcast.schemas.outbound import PURCHASE_ORDER_LINE_SCHEMA

from ..base import PurchaseCollector


class PurchaseOrderLineCollectorV18(PurchaseCollector[V18]):
    """Purchase-order-line collector for Odoo 18.

    **Primary documented drift (evidence doc §2):**
    ``purchase_order_line.product_uom`` in v18 → ``product_uom_id`` in v19.
    This collector uses the v18 spelling. The v18 CHECK constraint on
    ``purchase_order_line`` references ``product_uom IS NOT NULL``, matching
    the column name.

    Other columns (product_qty, qty_received, price_unit, date_planned,
    sale_line_id, orderpoint_id, origin-via-po) are unchanged between
    majors. ``uom.name`` is translatable JSONB on both.
    """

    name = "purchase_order_line"
    schema = PURCHASE_ORDER_LINE_SCHEMA
    depends_on = ["product", "partner"]
    required_tables = {"purchase_order", "purchase_order_line"}
    pk_column = "pol.id"
    primary_table = "purchase_order_line"

    def get_sql(self):
        lang1 = self.caps.lang(1) or "en_US"
        return (
            f"""
            SELECT
                pol.id, po.id, po.name,
                po.state, po.receipt_status,
                pol.product_id, pt.name->>'{lang1}',
                pol.product_qty, pol.qty_received,
                pol.product_uom, u.name->>'{lang1}',
                pol.price_unit, po.currency_id,
                po.date_order, pol.date_planned,
                po.partner_id, rp.name,
                spt.warehouse_id,
                po.origin,
                pol.sale_line_id,
                pol.orderpoint_id,
                po.company_id
            FROM purchase_order_line pol
            JOIN purchase_order po ON pol.order_id = po.id
            JOIN product_product pp ON pol.product_id = pp.id
            JOIN product_template pt ON pp.product_tmpl_id = pt.id
            LEFT JOIN uom_uom u ON pol.product_uom = u.id
            LEFT JOIN res_partner rp ON po.partner_id = rp.id
            LEFT JOIN stock_picking_type spt ON po.picking_type_id = spt.id
            WHERE pol.product_id IS NOT NULL
        """,
            None,
        )
