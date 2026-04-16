from parqcast.schemas.outbound import PURCHASE_ORDER_SCHEMA

from .base import PurchaseCollector


class PurchaseOrderCollector(PurchaseCollector):
    name = "purchase_order"
    schema = PURCHASE_ORDER_SCHEMA
    depends_on = ["partner"]
    required_tables = {"purchase_order"}
    pk_column = "po.id"
    primary_table = "purchase_order"

    def get_sql(self):
        return (
            """
            SELECT
                po.id, po.name, po.state,
                po.partner_id,
                po.date_order, po.date_approve, po.date_planned,
                po.receipt_status, po.invoice_status,
                COALESCE(po.amount_untaxed, 0),
                COALESCE(po.amount_total, 0),
                po.currency_id,
                po.picking_type_id, spt.warehouse_id,
                po.origin, po.priority,
                po.company_id
            FROM purchase_order po
            LEFT JOIN stock_picking_type spt ON po.picking_type_id = spt.id
        """,
            None,
        )
