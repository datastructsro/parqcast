from parqcast.schemas.outbound import COUNTRY_SCHEMA

from .base import CoreCollector


class CountryCollector[V](CoreCollector[V]):
    name = "country"
    schema = COUNTRY_SCHEMA
    required_tables = {"res_country"}

    def get_sql(self):
        lang1 = self.caps.lang(1) or "en_US"
        return (
            f"""
            SELECT
                rc.id,
                rc.name->>'{lang1}',
                rc.code
            FROM res_country rc
        """,
            None,
        )
