import pyarrow as pa

from parqcast.core.protocols import OdooEnvironment
from parqcast.core.version import V19

from ..base import BaseIngester, IngestResult


class OrderpointActorV19(BaseIngester[V19]):
    decision_type = "ORDERPOINT"

    def apply(self, decisions: pa.Table, env: OdooEnvironment) -> IngestResult:
        df = decisions.to_pydict()
        created = 0
        updated = 0
        errors = 0
        messages = []

        for i in range(decisions.num_rows):
            product_id = df["_odoo_product_id"][i]
            location_id = df["_odoo_location_id"][i]
            min_qty = df["min_quantity"][i]
            max_qty = df["max_quantity"][i]
            supplier_id = df.get("_odoo_supplier_id", [None] * decisions.num_rows)[i]

            if not product_id or min_qty is None or max_qty is None:
                errors += 1
                messages.append(f"Row {i}: missing product_id, min_quantity, or max_quantity")
                continue

            # Look up existing orderpoint by product + location
            domain = [("product_id", "=", product_id)]
            if location_id:
                domain.append(("location_id", "=", location_id))

            existing = env["stock.warehouse.orderpoint"].search(domain, limit=1)

            if existing:
                vals = {
                    "product_min_qty": min_qty,
                    "product_max_qty": max_qty,
                }
                if supplier_id:
                    vals["supplier_id"] = supplier_id
                existing.write(vals)
                updated += 1
            else:
                vals = {
                    "product_id": product_id,
                    "product_min_qty": min_qty,
                    "product_max_qty": max_qty,
                    "name": f"Parqcast-{product_id}",
                }
                if location_id:
                    vals["location_id"] = location_id
                if supplier_id:
                    vals["supplier_id"] = supplier_id
                env["stock.warehouse.orderpoint"].create(vals)
                created += 1

        return IngestResult(created=created, updated=updated, errors=errors, messages=messages)

    def cleanup_previous(self, env: OdooEnvironment, company_id: int) -> int:
        recs = env["stock.warehouse.orderpoint"].search(
            [
                ("name", "=like", "Parqcast%"),
                ("company_id", "=", company_id),
            ]
        )
        count = len(recs)
        recs.unlink()
        return count
