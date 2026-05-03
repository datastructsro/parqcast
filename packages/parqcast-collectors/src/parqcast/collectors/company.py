from parqcast.schemas.outbound import COMPANY_SCHEMA

from .base import CoreCollector


class CompanyCollector[V](CoreCollector[V]):
    name = "company"
    schema = COMPANY_SCHEMA

    def get_sql(self):
        return (
            """
            SELECT
                rc.id, rc.name, rc.currency_id,
                rc.parent_id,
                COALESCE(rc.security_lead, 0),
                rc.active,
                rp.country_id
            FROM res_company rc
            LEFT JOIN res_partner rp ON rp.id = rc.partner_id
        """,
            None,
        )
