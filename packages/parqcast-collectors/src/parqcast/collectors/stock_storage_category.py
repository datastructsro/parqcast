from parqcast.schemas.outbound import STOCK_STORAGE_CATEGORY_SCHEMA

from .base import StockCollector


class StockStorageCategoryCollector(StockCollector):
    """stock_storage_category.name is varchar (not JSONB)."""

    name = "stock_storage_category"
    schema = STOCK_STORAGE_CATEGORY_SCHEMA
    required_tables = {"stock_storage_category"}

    def get_sql(self):
        return (
            """
            SELECT
                sc.id, sc.name, sc.max_weight,
                sc.allow_new_product, sc.company_id
            FROM stock_storage_category sc
        """,
            None,
        )
