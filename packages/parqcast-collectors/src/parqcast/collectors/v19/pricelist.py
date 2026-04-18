from parqcast.core.version import V19
from parqcast.schemas.outbound import PRICELIST_ITEM_SCHEMA, PRICELIST_SCHEMA

from ..base import SaleCollector


class PricelistCollectorV19(SaleCollector[V19]):
    name = "pricelist"
    schema = PRICELIST_SCHEMA
    required_tables = {"product_pricelist"}

    def get_sql(self):
        lang1 = self.caps.lang(1) or "en_US"
        return (
            f"""
            SELECT
                pp.id,
                pp.name->>'{lang1}',
                pp.currency_id,
                pp.company_id,
                pp.active
            FROM product_pricelist pp
        """,
            None,
        )


class PricelistItemCollectorV19(SaleCollector[V19]):
    name = "pricelist_item"
    schema = PRICELIST_ITEM_SCHEMA
    depends_on = ["pricelist", "product"]
    required_tables = {"product_pricelist_item"}

    def get_sql(self):
        return (
            """
            SELECT
                ppi.id, ppi.pricelist_id,
                ppi.applied_on, ppi.compute_price, ppi.base,
                COALESCE(ppi.fixed_price, 0),
                COALESCE(ppi.percent_price, 0),
                COALESCE(ppi.price_discount, 0),
                COALESCE(ppi.price_surcharge, 0),
                COALESCE(ppi.price_round, 0),
                COALESCE(ppi.price_min_margin, 0),
                COALESCE(ppi.price_max_margin, 0),
                COALESCE(ppi.min_quantity, 0),
                ppi.date_start, ppi.date_end,
                ppi.product_tmpl_id, ppi.product_id,
                ppi.categ_id, ppi.base_pricelist_id,
                ppi.company_id
            FROM product_pricelist_item ppi
        """,
            None,
        )
