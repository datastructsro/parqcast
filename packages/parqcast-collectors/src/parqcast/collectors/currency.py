from parqcast.schemas.outbound import CURRENCY_SCHEMA

from .base import CoreCollector


class CurrencyCollector[V](CoreCollector[V]):
    name = "currency"
    schema = CURRENCY_SCHEMA

    def get_sql(self):
        return (
            """
            SELECT
                rc.id, rc.name, rc.symbol,
                rc.decimal_places, rc.rounding,
                rc.active,
                rcr.id, rcr.rate, rcr.name, rcr.company_id
            FROM res_currency rc
            LEFT JOIN res_currency_rate rcr ON rc.id = rcr.currency_id
        """,
            None,
        )
