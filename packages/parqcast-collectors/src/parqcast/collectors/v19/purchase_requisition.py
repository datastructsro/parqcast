from parqcast.core.version import V19
from parqcast.schemas.outbound import PURCHASE_REQUISITION_SCHEMA

from ..base import PurchaseCollector


class PurchaseRequisitionCollectorV19(PurchaseCollector[V19]):
    """Requires both ``purchase`` and ``purchase_requisition`` modules."""

    name = "purchase_requisition"
    schema = PURCHASE_REQUISITION_SCHEMA
    depends_on = ["partner"]
    required_modules = {"purchase", "purchase_requisition"}
    required_tables = {"purchase_requisition"}

    def get_sql(self):
        return (
            """
            SELECT
                pr.id, pr.name, pr.state,
                pr.requisition_type,
                pr.vendor_id, rp.name,
                pr.currency_id,
                pr.date_start, pr.date_end,
                pr.warehouse_id,
                pr.active, pr.company_id
            FROM purchase_requisition pr
            LEFT JOIN res_partner rp ON pr.vendor_id = rp.id
        """,
            None,
        )
