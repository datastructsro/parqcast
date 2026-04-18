from parqcast.core.version import V18
from parqcast.schemas.outbound import PRODUCT_REMOVAL_SCHEMA

from ..base import StockCollector


class ProductRemovalCollectorV18(StockCollector[V18]):
    """Both ``product_removal.name`` and ``product_removal.method`` are JSONB
    translatable fields in v18 (same as v19)."""

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
