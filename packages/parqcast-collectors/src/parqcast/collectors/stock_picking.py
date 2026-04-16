from parqcast.schemas.outbound import STOCK_PICKING_SCHEMA

from .base import StockCollector


class StockPickingCollector(StockCollector):
    name = "stock_picking"
    schema = STOCK_PICKING_SCHEMA
    depends_on = ["stock_location", "partner"]
    required_tables = {"stock_picking", "stock_picking_type"}

    pk_column = "sp.id"
    primary_table = "stock_picking"

    def get_sql(self):
        return (
            """
            SELECT
                sp.id, sp.name, sp.state,
                spt.code,
                sp.location_id, sp.location_dest_id,
                sp.scheduled_date, sp.date_deadline,
                sp.date_done,
                sp.origin, sp.partner_id,
                sp.backorder_id,
                sp.sale_id,
                sp.priority, sp.move_type,
                sp.company_id
            FROM stock_picking sp
            JOIN stock_picking_type spt ON sp.picking_type_id = spt.id
        """,
            None,
        )
