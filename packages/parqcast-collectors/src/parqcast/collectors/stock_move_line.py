from parqcast.schemas.outbound import STOCK_MOVE_LINE_SCHEMA

from .base import StockCollector


class StockMoveLineCollector(StockCollector):
    name = "stock_move_line"
    schema = STOCK_MOVE_LINE_SCHEMA
    required_tables = {"stock_move_line"}
    pk_column = "sml.id"
    primary_table = "stock_move_line"

    def get_sql(self):
        return (
            """
            SELECT
                sml.id, sml.move_id, sml.picking_id,
                sml.product_id, sml.product_uom_id,
                sml.quantity,
                sml.lot_id, sml.lot_name,
                sml.package_id, sml.result_package_id,
                sml.owner_id,
                sml.location_id, sml.location_dest_id,
                sml.state, sml.date,
                sml.expiration_date,
                sml.company_id
            FROM stock_move_line sml
        """,
            None,
        )
