from parqcast.core.version import V19
from parqcast.schemas.outbound import STOCK_ROUTE_SCHEMA

from ..base import StockCollector


class StockRouteCollectorV19(StockCollector[V19]):
    """Denormalised route + rules. Both ``stock_route.name`` and
    ``stock_rule.name`` are translatable ``Char`` stored as JSONB (Odoo-wide
    since 16/17, not v19-specific).
    """

    name = "stock_route"
    schema = STOCK_ROUTE_SCHEMA
    depends_on = ["stock_location"]
    required_tables = {"stock_route", "stock_rule"}

    def get_sql(self):
        lang1 = self.caps.lang(1) or "en_US"
        return (
            f"""
            SELECT
                sr.route_id, rt.name->>'{lang1}', rt.active,
                sr.id, sr.name->>'{lang1}',
                sr.action, sr.procure_method,
                sr.picking_type_id, spt.code,
                sr.location_src_id, sr.location_dest_id,
                sr.delay, sr.sequence,
                sr.warehouse_id, sr.company_id,
                COALESCE(
                    (SELECT string_agg(srw.warehouse_id::text, ',')
                     FROM stock_route_warehouse srw
                     WHERE srw.route_id = sr.route_id), '')
            FROM stock_rule sr
            JOIN stock_route rt ON sr.route_id = rt.id
            LEFT JOIN stock_picking_type spt ON sr.picking_type_id = spt.id
        """,
            None,
        )
