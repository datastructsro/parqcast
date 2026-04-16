from parqcast.schemas.outbound import PRODUCT_CATEGORY_SCHEMA

from .base import CoreCollector


class ProductCategoryCollector(CoreCollector):
    name = "product_category"
    schema = PRODUCT_CATEGORY_SCHEMA
    required_tables = {"product_category"}

    def get_sql(self):
        lang1 = self.caps.lang(1) or "en_US"
        return (
            f"""
            SELECT
                pc.id,
                pc.name,
                pc.complete_name,
                pc.parent_id,
                pc.parent_path,
                pc.removal_strategy_id,
                pr.name,
                pc.property_valuation->>'{lang1}',
                pc.property_cost_method->>'{lang1}'
            FROM product_category pc
            LEFT JOIN product_removal pr ON pc.removal_strategy_id = pr.id
        """,
            None,
        )
