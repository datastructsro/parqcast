from parqcast.core.version import V19
from parqcast.schemas.outbound import STOCK_STORAGE_CATEGORY_SCHEMA

from ..base import StockCollector


class StockStorageCategoryCollectorV19(StockCollector[V19]):
    """``stock_storage_category.name`` is a plain ``varchar`` (not translatable,
    not JSONB) in Odoo 19.
    """

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
