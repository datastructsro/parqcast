from parqcast.core.version import V19
from parqcast.schemas.outbound import POS_ORDER_LINE_SCHEMA, POS_ORDER_SCHEMA

from ..base import PosCollector


class PosOrderCollectorV19(PosCollector[V19]):
    name = "pos_order"
    schema = POS_ORDER_SCHEMA
    depends_on = ["partner"]
    required_tables = {"pos_order", "pos_session"}

    def get_sql(self):
        return (
            """
            SELECT
                po.id, po.name, po.state,
                po.date_order, po.partner_id,
                po.session_id, po.config_id,
                po.amount_total, po.amount_tax, po.amount_paid,
                po.is_refund,
                po.company_id
            FROM pos_order po
        """,
            None,
        )


class PosOrderLineCollectorV19(PosCollector[V19]):
    name = "pos_order_line"
    schema = POS_ORDER_LINE_SCHEMA
    depends_on = ["pos_order", "product"]
    required_tables = {"pos_order_line"}

    def get_sql(self):
        return (
            """
            SELECT
                pol.id, pol.order_id,
                pol.product_id,
                pol.full_product_name,
                pol.qty,
                COALESCE(pol.price_unit, 0),
                COALESCE(pol.price_subtotal, 0),
                COALESCE(pol.price_subtotal_incl, 0),
                COALESCE(pol.discount, 0),
                pol.company_id
            FROM pos_order_line pol
        """,
            None,
        )
