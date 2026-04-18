from parqcast.core.version import V18
from parqcast.schemas.outbound import STOCK_LOCATION_SCHEMA

from ..base import StockCollector


class StockLocationCollectorV18(StockCollector[V18]):
    """Stock location collector for Odoo 18.

    v18 still has the legacy ``scrap_location`` and ``replenish_location``
    booleans on ``stock_location``; parqcast does not export them (the
    outbound schema doesn't include them) so their presence is a no-op
    here. ``return_location`` is folklore — absent in both v18 and v19 per
    grep; not referenced.

    The shared SQL surface (id, name, complete_name, usage, parent refs,
    removal strategy, optional storage category) is identical to v19.
    """

    name = "stock_location"
    schema = STOCK_LOCATION_SCHEMA
    required_tables = {"stock_location"}

    optional_columns = {
        "stock_location.storage_category_id": ("sl.storage_category_id", "NULL::int"),
    }

    def get_sql(self):
        cat_id = self.col_or_default("stock_location", "storage_category_id", "NULL::int")

        cat_join = ""
        cat_name = "NULL::text"
        if self.caps.has_column("stock_location", "storage_category_id"):
            cat_join = "LEFT JOIN stock_storage_category sc ON sl.storage_category_id = sc.id"
            cat_name = "sc.name"

        return (
            f"""
            SELECT
                sl.id, sl.name, sl.complete_name, sl.usage,
                sl.location_id, sl.warehouse_id, sw.code,
                pr.method,
                {cat_id}, {cat_name},
                sl.active, sl.company_id
            FROM stock_location sl
            LEFT JOIN stock_warehouse sw ON sl.warehouse_id = sw.id
            LEFT JOIN product_removal pr ON sl.removal_strategy_id = pr.id
            {cat_join}
        """,
            None,
        )
