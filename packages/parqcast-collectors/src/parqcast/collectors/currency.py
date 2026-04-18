from parqcast.schemas.outbound import CURRENCY_SCHEMA

from .base import CoreCollector


class CurrencyCollector[V](CoreCollector[V]):
    """Currency + currency-rate collector, shared across Odoo majors.

    ``res_currency_rate.name`` is declared as ``fields.Date`` in both v18
    and v19, but the outbound schema's ``rate_date`` column is
    ``OdooDate = pa.timestamp(..., tz='UTC')``. psycopg2 returns Python
    ``datetime.date`` for DATE columns, which pyarrow refuses to coerce to
    a timestamp. We cast to ``timestamp`` in SQL so the driver yields a
    ``datetime.datetime`` that pyarrow accepts.
    """

    name = "currency"
    schema = CURRENCY_SCHEMA

    def get_sql(self):
        return (
            """
            SELECT
                rc.id, rc.name, rc.symbol,
                rc.decimal_places, rc.rounding,
                rc.active,
                rcr.id, rcr.rate, rcr.name::timestamp, rcr.company_id
            FROM res_currency rc
            LEFT JOIN res_currency_rate rcr ON rc.id = rcr.currency_id
        """,
            None,
        )
