from parqcast.schemas.outbound import PRODUCT_REMOVAL_SCHEMA

from .base import StockCollector


class ProductRemovalCollector(StockCollector):
    """Both product_removal.name and product_removal.method are JSONB."""

    name = "product_removal"
    schema = PRODUCT_REMOVAL_SCHEMA
    required_tables = {"product_removal"}

    def get_sql(self):
        lang1 = self.caps.lang(1) or "en_US"
        return (
            f"""
            SELECT
                pr.id, pr.name->>'{lang1}',
                pr.method->>'{lang1}'
            FROM product_removal pr
        """,
            None,
        )
