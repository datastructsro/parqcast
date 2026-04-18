from parqcast.core.version import V18
from parqcast.schemas.outbound import POS_ORDER_LINE_SCHEMA, POS_ORDER_SCHEMA

from ..base import PosCollector


class PosOrderCollectorV18(PosCollector[V18]):
    """Pos-order collector for Odoo 18.

    v18 lacks ``pos_order.is_refund`` (v19 addition); gated optional with
    fallback ``false``. All other columns (date_order, partner_id,
    session_id, config_id, amounts, company_id) match v19.
    """

    name = "pos_order"
    schema = POS_ORDER_SCHEMA
    depends_on = ["partner"]
    required_tables = {"pos_order", "pos_session"}

    optional_columns = {
        "pos_order.is_refund": ("COALESCE(po.is_refund, false)", "false"),
    }

    def get_sql(self):
        is_refund = self.col_or_default("pos_order", "is_refund", "false")
        return (
            f"""
            SELECT
                po.id, po.name, po.state,
                po.date_order, po.partner_id,
                po.session_id, po.config_id,
                po.amount_total, po.amount_tax, po.amount_paid,
                {is_refund},
                po.company_id
            FROM pos_order po
        """,
            None,
        )


class PosOrderLineCollectorV18(PosCollector[V18]):
    """Pos-order-line columns (order_id, product_id, full_product_name, qty,
    price_unit, price_subtotal, price_subtotal_incl, discount, company_id)
    are identical in v18 and v19."""

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
