from parqcast.core.version import V18
from parqcast.schemas.outbound import PURCHASE_REQUISITION_SCHEMA

from ..base import PurchaseCollector


class PurchaseRequisitionCollectorV18(PurchaseCollector[V18]):
    """Requires both ``purchase`` and ``purchase_requisition`` modules.

    Column surface is stable across v18 and v19 — requisition_type,
    vendor_id, currency_id, date_start, date_end, warehouse_id, active,
    company_id all exist on both. The v18 demo DB does not install
    purchase_requisition, so ``is_compatible`` short-circuits and this
    collector does not run there.
    """

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
