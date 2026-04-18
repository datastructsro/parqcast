from parqcast.core.version import V19
from parqcast.schemas.outbound import STOCK_PICKING_TYPE_SCHEMA

from ..base import StockCollector


class StockPickingTypeCollectorV19(StockCollector[V19]):
    """``stock_picking_type.name`` is a translatable ``Char`` stored as JSONB
    (Odoo-wide since 16/17, not a v19-specific change).
    """

    name = "stock_picking_type"
    schema = STOCK_PICKING_TYPE_SCHEMA
    depends_on = ["stock_location"]
    required_tables = {"stock_picking_type"}

    def get_sql(self):
        lang1 = self.caps.lang(1) or "en_US"
        return (
            f"""
            SELECT
                spt.id, spt.name->>'{lang1}', spt.code,
                spt.sequence_code,
                spt.default_location_src_id,
                spt.default_location_dest_id,
                spt.warehouse_id, spt.active,
                spt.company_id
            FROM stock_picking_type spt
        """,
            None,
        )
