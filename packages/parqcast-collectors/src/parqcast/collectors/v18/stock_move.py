from parqcast.core.version import V18
from parqcast.schemas.outbound import STOCK_MOVE_SCHEMA

from ..base import StockCollector


class StockMoveCollectorV18(StockCollector[V18]):
    """Stock-move collector for Odoo 18.

    v18's ``stock_move`` has the same surface as v19 for the columns we
    export: ``product_uom`` (integer FK — note name is ``product_uom``,
    same as v18/v19 for stock_move; the purchase-line rename to
    ``product_uom_id`` in v19 is separate), ``product_uom_qty``,
    ``quantity``, ``state``, ``priority``, ``picking_id``, ``location_id``,
    ``location_dest_id``, ``warehouse_id``, ``origin``, ``date``,
    ``date_deadline``, ``delay_alert_date``, ``procure_method``.

    Optional columns (``production_id``, ``sale_line_id``,
    ``purchase_line_id``, ``is_subcontract``) continue to be gated via
    :meth:`col_or_default`. v18 demo has no ``is_subcontract`` column on
    stock_move unless the subcontracting module is installed — the
    fallback writes ``false``, matching the outbound schema's expected
    default.
    """

    name = "stock_move"
    schema = STOCK_MOVE_SCHEMA
    required_tables = {"stock_move"}

    optional_columns = {
        "stock_move.production_id": ("sm.production_id", "NULL::int"),
        "stock_move.sale_line_id": ("sm.sale_line_id", "NULL::int"),
        "stock_move.purchase_line_id": ("sm.purchase_line_id", "NULL::int"),
        "stock_move.is_subcontract": ("COALESCE(sm.is_subcontract, false)", "false"),
    }

    pk_column = "sm.id"
    primary_table = "stock_move"

    def get_sql(self):
        lang1 = self.caps.lang(1) or "en_US"
        prod_col = self.col_or_default("stock_move", "production_id", "NULL::int")
        sol_col = self.col_or_default("stock_move", "sale_line_id", "NULL::int")
        pol_col = self.col_or_default("stock_move", "purchase_line_id", "NULL::int")
        subcon_col = self.col_or_default("stock_move", "is_subcontract", "false")

        return (
            f"""
            SELECT
                sm.id, sm.product_id,
                pt.name->>'{lang1}',
                sm.product_uom_qty, sm.quantity,
                sm.product_uom, sm.state,
                sm.priority,
                sm.picking_id, sp.name,
                sm.location_id, sm.location_dest_id,
                sm.warehouse_id,
                {prod_col},
                {sol_col},
                {pol_col},
                sm.origin,
                sm.date, sm.date_deadline,
                sm.delay_alert_date,
                sm.procure_method,
                COALESCE(
                    (SELECT string_agg(move_dest_id::text, ',')
                     FROM stock_move_move_rel WHERE move_orig_id = sm.id), ''),
                COALESCE(
                    (SELECT string_agg(move_orig_id::text, ',')
                     FROM stock_move_move_rel WHERE move_dest_id = sm.id), ''),
                {subcon_col}
            FROM stock_move sm
            JOIN product_product pp ON sm.product_id = pp.id
            JOIN product_template pt ON pp.product_tmpl_id = pt.id
            LEFT JOIN stock_picking sp ON sm.picking_id = sp.id
        """,
            None,
        )
