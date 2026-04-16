from parqcast.schemas.outbound import STOCK_LOT_SCHEMA

from .base import StockCollector


class StockLotCollector(StockCollector):
    """Expiry date columns come from product_expiry module — made optional."""

    name = "stock_lot"
    schema = STOCK_LOT_SCHEMA
    depends_on = ["product"]
    required_tables = {"stock_lot"}

    optional_columns = {
        "stock_lot.expiration_date": ("sl.expiration_date", "NULL::timestamp"),
        "stock_lot.use_date": ("sl.use_date", "NULL::timestamp"),
        "stock_lot.removal_date": ("sl.removal_date", "NULL::timestamp"),
        "stock_lot.alert_date": ("sl.alert_date", "NULL::timestamp"),
    }

    def get_sql(self):
        exp = self.col_or_default("stock_lot", "expiration_date", "NULL::timestamp")
        use = self.col_or_default("stock_lot", "use_date", "NULL::timestamp")
        rem = self.col_or_default("stock_lot", "removal_date", "NULL::timestamp")
        alr = self.col_or_default("stock_lot", "alert_date", "NULL::timestamp")

        return (
            f"""
            SELECT
                sl.id, sl.name, sl.ref,
                sl.product_id, sl.company_id,
                {exp}, {use}, {rem}, {alr}
            FROM stock_lot sl
        """,
            None,
        )
