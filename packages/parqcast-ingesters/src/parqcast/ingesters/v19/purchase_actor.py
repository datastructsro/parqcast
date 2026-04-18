import pyarrow as pa

from parqcast.core.version import V19

from ..base import BaseIngester, IngestResult


class PurchaseActorV19(BaseIngester[V19]):
    """Create purchase orders and lines from planning-engine decisions.

    On Odoo 19 the UoM field on ``purchase.order.line`` is ``product_uom_id``
    (it was ``product_uom`` in v18; see docs/odoo-18-vs-19-evidence.md §2).
    This ingester targets the v19 name.
    """

    decision_type = "PO"

    def apply(self, decisions: pa.Table, env) -> IngestResult:
        df = decisions.to_pydict()
        created = 0
        pos = {}

        for i in range(decisions.num_rows):
            supplier_id = df["_odoo_supplier_id"][i]
            product_id = df["_odoo_product_id"][i]
            uom_id = df["_odoo_uom_id"][i]
            quantity = df["quantity"][i]
            end_date = df["end_date"][i]

            if supplier_id not in pos:
                po = env["purchase.order"].create(
                    {
                        "partner_id": supplier_id,
                        "origin": "Parqcast",
                    }
                )
                pos[supplier_id] = po
            else:
                po = pos[supplier_id]

            product = env["product.product"].browse(product_id)
            supplier_info = env["product.supplierinfo"].search(
                [
                    ("partner_id", "=", supplier_id),
                    ("product_tmpl_id", "=", product.product_tmpl_id.id),
                    ("min_qty", "<=", quantity),
                ],
                limit=1,
                order="min_qty desc",
            )

            pol = env["purchase.order.line"].create(
                {
                    "order_id": po.id,
                    "product_id": product_id,
                    "product_qty": quantity,
                    "product_uom_id": uom_id,
                }
            )

            if supplier_info and supplier_info.currency_id and supplier_info.currency_id.id != po.currency_id.id:
                po.currency_id = supplier_info.currency_id.id

            vals = pol._prepare_purchase_order_line(
                product,
                quantity,
                env["uom.uom"].browse(uom_id),
                env.company,
                supplier_info,
                po,
            )
            vals["date_planned"] = end_date
            pol.write(vals)
            created += 1

        return IngestResult(created=created)

    def cleanup_previous(self, env, company_id: int) -> int:
        recs = env["purchase.order"].search(
            [
                ("state", "=", "draft"),
                ("origin", "=like", "Parqcast%"),
                ("company_id", "=", company_id),
            ]
        )
        count = len(recs)
        recs.write({"state": "cancel"})
        recs.unlink()
        return count
