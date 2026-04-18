from parqcast.core.version import V19
from parqcast.schemas.outbound import ORDERPOINT_SCHEMA

from ..base import StockCollector


class OrderpointCollectorV19(StockCollector[V19]):
    """``qty_on_hand`` / ``qty_forecast`` / ``qty_to_order`` / ``lead_days`` are
    computed (not stored) on ``stock.warehouse.orderpoint`` in v19 — same as
    v18, so the optional-column probe handles both transparently.
    """

    name = "orderpoint"
    schema = ORDERPOINT_SCHEMA
    depends_on = ["product", "stock_location"]
    required_tables = {"stock_warehouse_orderpoint"}

    optional_columns = {
        "stock_warehouse_orderpoint.replenishment_uom_id": ("op.replenishment_uom_id", "NULL::int"),
        "stock_warehouse_orderpoint.qty_to_order_computed": ("op.qty_to_order_computed", "NULL::numeric"),
        "stock_warehouse_orderpoint.qty_to_order_manual": ("op.qty_to_order_manual", "NULL::numeric"),
        "stock_warehouse_orderpoint.supplier_id": ("op.supplier_id", "NULL::int"),
    }

    def get_sql(self):
        lang1 = self.caps.lang(1) or "en_US"
        repl_uom = self.col_or_default("stock_warehouse_orderpoint", "replenishment_uom_id", "NULL::int")
        qty_computed = self.col_or_default("stock_warehouse_orderpoint", "qty_to_order_computed", "NULL::numeric")
        qty_manual = self.col_or_default("stock_warehouse_orderpoint", "qty_to_order_manual", "NULL::numeric")
        supplier = self.col_or_default("stock_warehouse_orderpoint", "supplier_id", "NULL::int")

        return (
            f"""
            SELECT
                op.id, op.product_id, pt.name->>'{lang1}',
                op.warehouse_id, sw.code,
                op.location_id, sl.complete_name,
                op.product_min_qty, op.product_max_qty,
                op.trigger, op.active,
                op.snoozed_until::timestamp,
                op.route_id, sr.name->>'{lang1}',
                op.deadline_date::timestamp,
                {repl_uom},
                {qty_computed},
                {qty_manual},
                {supplier},
                op.company_id
            FROM stock_warehouse_orderpoint op
            JOIN product_product pp ON op.product_id = pp.id
            JOIN product_template pt ON pp.product_tmpl_id = pt.id
            LEFT JOIN stock_warehouse sw ON op.warehouse_id = sw.id
            LEFT JOIN stock_location sl ON op.location_id = sl.id
            LEFT JOIN stock_route sr ON op.route_id = sr.id
        """,
            None,
        )
