from parqcast.schemas.outbound import MRP_PRODUCTION_SCHEMA

from .base import MrpCollector


class MrpProductionCollector(MrpCollector):
    name = "mrp_production"
    schema = MRP_PRODUCTION_SCHEMA
    depends_on = ["product"]
    required_tables = {"mrp_production"}

    def get_sql(self):
        lang1 = self.caps.lang(1) or "en_US"
        return (
            f"""
            SELECT
                mp.id, mp.name,
                mp.product_id, pt.name->>'{lang1}',
                mp.bom_id, mp.product_qty, mp.qty_producing,
                mp.product_uom_id, mp.state,
                mp.priority, mp.reservation_state,
                mp.date_start, mp.date_finished, mp.date_deadline,
                mp.location_src_id, mp.location_dest_id,
                mp.picking_type_id, mp.origin, mp.company_id
            FROM mrp_production mp
            JOIN product_product pp ON mp.product_id = pp.id
            JOIN product_template pt ON pp.product_tmpl_id = pt.id
        """,
            None,
        )
