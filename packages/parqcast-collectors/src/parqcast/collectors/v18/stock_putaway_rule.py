from parqcast.core.version import V18
from parqcast.schemas.outbound import STOCK_PUTAWAY_RULE_SCHEMA

from ..base import StockCollector


class StockPutawayRuleCollectorV18(StockCollector[V18]):
    """Putaway-rule columns (product/category/location_in/location_out, storage
    category, sequence, sublocation, active) are identical in v18 and v19."""

    name = "stock_putaway_rule"
    schema = STOCK_PUTAWAY_RULE_SCHEMA
    depends_on = ["stock_location", "product"]
    required_tables = {"stock_putaway_rule"}

    def get_sql(self):
        return (
            """
            SELECT
                spr.id, spr.product_id, spr.category_id,
                spr.location_in_id, spr.location_out_id,
                spr.storage_category_id, spr.sequence,
                spr.sublocation, spr.active
            FROM stock_putaway_rule spr
        """,
            None,
        )
