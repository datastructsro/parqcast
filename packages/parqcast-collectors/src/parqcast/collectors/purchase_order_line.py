from parqcast.schemas.outbound import PURCHASE_ORDER_LINE_SCHEMA

from .base import PurchaseCollector


class PurchaseOrderLineCollector(PurchaseCollector):
    """Odoo 19: product_uom -> product_uom_id, uom.name is JSONB."""

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
                pol.product_uom_id, u.name->>'{lang1}',
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
            LEFT JOIN uom_uom u ON pol.product_uom_id = u.id
            LEFT JOIN res_partner rp ON po.partner_id = rp.id
            LEFT JOIN stock_picking_type spt ON po.picking_type_id = spt.id
            WHERE pol.product_id IS NOT NULL
        """,
            None,
        )
