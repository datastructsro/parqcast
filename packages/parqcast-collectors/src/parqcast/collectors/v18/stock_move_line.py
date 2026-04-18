from parqcast.core.version import V18
from parqcast.schemas.outbound import STOCK_MOVE_LINE_SCHEMA

from ..base import StockCollector


class StockMoveLineCollectorV18(StockCollector[V18]):
    """Stock-move-line collector for Odoo 18.

    ``expiration_date`` on ``stock_move_line`` is contributed by the
    ``product_expiry`` module on both v18 and v19; we gate it through
    ``optional_columns`` so a vanilla install (no product_expiry) still
    produces a complete row.
    """

    name = "stock_move_line"
    schema = STOCK_MOVE_LINE_SCHEMA
    required_tables = {"stock_move_line"}
    pk_column = "sml.id"
    primary_table = "stock_move_line"

    optional_columns = {
        "stock_move_line.expiration_date": (
            "sml.expiration_date",
            "NULL::timestamp",
        ),
    }

    def get_sql(self):
        exp = self.col_or_default("stock_move_line", "expiration_date", "NULL::timestamp")
        return (
            f"""
            SELECT
                sml.id, sml.move_id, sml.picking_id,
                sml.product_id, sml.product_uom_id,
                sml.quantity,
                sml.lot_id, sml.lot_name,
                sml.package_id, sml.result_package_id,
                sml.owner_id,
                sml.location_id, sml.location_dest_id,
                sml.state, sml.date,
                {exp},
                sml.company_id
            FROM stock_move_line sml
        """,
            None,
        )
