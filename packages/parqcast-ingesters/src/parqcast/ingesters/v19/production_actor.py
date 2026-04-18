import pyarrow as pa

from parqcast.core.version import V19

from ..base import BaseIngester, IngestResult


class ProductionActorV19(BaseIngester[V19]):
    decision_type = "MO"

    def apply(self, decisions: pa.Table, env) -> IngestResult:
        df = decisions.to_pydict()
        created = 0

        for i in range(decisions.num_rows):
            mo = env["mrp.production"].create(
                {
                    "product_id": df["_odoo_product_id"][i],
                    "product_qty": df["quantity"][i],
                    "product_uom_id": df["_odoo_uom_id"][i],
                    "bom_id": df["_odoo_bom_id"][i],
                    "date_start": df["start_date"][i],
                    "date_finished": df["end_date"][i],
                    "qty_producing": 0.0,
                    "origin": "Parqcast",
                }
            )
            mo._create_update_move_finished()
            created += 1

        return IngestResult(created=created)

    def cleanup_previous(self, env, company_id: int) -> int:
        recs = env["mrp.production"].search(
            [
                "|",
                ("state", "=", "draft"),
                ("state", "=", "cancel"),
                ("origin", "=like", "Parqcast%"),
                ("company_id", "=", company_id),
            ]
        )
        count = len(recs)
        recs.write({"state": "cancel"})
        recs.unlink()
        return count
