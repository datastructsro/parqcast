from parqcast.schemas.outbound import PARTNER_SCHEMA

from .base import CoreCollector


class PartnerCollector[V](CoreCollector[V]):
    name = "partner"
    schema = PARTNER_SCHEMA
    pk_column = "rp.id"
    primary_table = "res_partner"

    def get_sql(self):
        return (
            """
            SELECT
                rp.id, rp.name, rp.ref,
                rp.is_company,
                rp.parent_id, parent.name,
                rp.country_id,
                COALESCE(rp.customer_rank, 0),
                COALESCE(rp.supplier_rank, 0),
                rp.active, rp.company_id
            FROM res_partner rp
            LEFT JOIN res_partner parent ON rp.parent_id = parent.id
        """,
            None,
        )
