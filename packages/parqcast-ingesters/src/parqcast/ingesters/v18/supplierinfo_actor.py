import pyarrow as pa

from parqcast.core.protocols import OdooEnvironment
from parqcast.core.version import V18

from ..base import BaseIngester, IngestResult


class SupplierinfoActorV18(BaseIngester[V18]):
    """Update vendor lead times (delay) based on ML empirical calculations."""

    decision_type = "LEAD_TIME"

    def apply(self, decisions: pa.Table, env: OdooEnvironment) -> IngestResult:
        df = decisions.to_pydict()
        updated = 0
        errors = 0

        for i in range(decisions.num_rows):
            supplier_id = df["_odoo_supplier_id"][i]
            product_id = df["_odoo_product_id"][i]
            delay = df["delay"][i]

            if not supplier_id or not product_id or delay is None:
                errors += 1
                continue

            product = env["product.product"].browse(product_id)
            if not product.exists():
                errors += 1
                continue

            # Find the exact supplier pricelist link
            supplier_info = env["product.supplierinfo"].search(
                [
                    ("partner_id", "=", supplier_id),
                    ("product_tmpl_id", "=", product.product_tmpl_id.id),
                ],
                limit=1,
            )

            if supplier_info:
                supplier_info.write({"delay": delay})
                updated += 1
            else:
                errors += 1  # We don't create new supplierinfo here, only update existing

        return IngestResult(updated=updated, errors=errors)

    def cleanup_previous(self, env: OdooEnvironment, company_id: int) -> int:
        # We don't cleanup past empirical lead times, they are a permanent state update
        return 0
