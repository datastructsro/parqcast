from parqcast.core.version import V19
from parqcast.schemas.outbound import STOCK_WAREHOUSE_SCHEMA

from ..base import StockCollector


class StockWarehouseCollectorV19(StockCollector[V19]):
    name = "stock_warehouse"
    schema = STOCK_WAREHOUSE_SCHEMA
    depends_on = ["stock_location"]
    required_tables = {"stock_warehouse"}

    def get_sql(self):
        return (
            """
            SELECT
                sw.id, sw.name, sw.code,
                sw.lot_stock_id,
                sw.wh_input_stock_loc_id,
                sw.wh_output_stock_loc_id,
                sw.reception_steps, sw.delivery_steps,
                sw.active, sw.company_id
            FROM stock_warehouse sw
        """,
            None,
        )
