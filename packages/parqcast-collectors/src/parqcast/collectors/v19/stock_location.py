from parqcast.core.version import V19
from parqcast.schemas.outbound import STOCK_LOCATION_SCHEMA

from ..base import StockCollector


class StockLocationCollectorV19(StockCollector[V19]):
    """Odoo 19: ``scrap_location`` boolean column is removed; scrap locations
    are now identified by ``usage = 'inventory'`` (see the
    ``_check_scrap_location`` constraint in core stock). We do not rely on
    the old boolean.
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
