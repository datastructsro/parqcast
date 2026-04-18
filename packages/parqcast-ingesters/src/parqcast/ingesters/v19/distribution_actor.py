import pyarrow as pa

from parqcast.core.version import V19

from ..base import BaseIngester, IngestResult


class DistributionActorV19(BaseIngester[V19]):
    decision_type = "DO"

    def apply(self, decisions: pa.Table, env) -> IngestResult:
        df = decisions.to_pydict()
        created = 0
        pickings = {}

        for i in range(decisions.num_rows):
            origin = df["origin_location"][i]
            dest = df["destination_location"][i]
            key = (origin, dest)

            origin_wh = env["stock.warehouse"].search([("code", "=", origin)], limit=1)
            dest_wh = env["stock.warehouse"].search([("code", "=", dest)], limit=1)
            if not origin_wh or not dest_wh:
                continue

            origin_loc = env["stock.location"].search(
                [
                    ("warehouse_id", "=", origin_wh.id),
                    ("usage", "=", "internal"),
                    ("name", "like", "Stock"),
                ],
                limit=1,
            )
            dest_loc = env["stock.location"].search(
                [
                    ("warehouse_id", "=", dest_wh.id),
                    ("usage", "=", "internal"),
                    ("name", "like", "Stock"),
                ],
                limit=1,
            )
            if not origin_loc or not dest_loc:
                continue

            if key not in pickings:
                picking_type = env["stock.picking.type"].search(
                    [
                        ("code", "=", "internal"),
                        ("default_location_src_id", "=", origin_loc.id),
                    ],
                    limit=1,
                )
                if not picking_type:
                    picking_type = env["stock.picking.type"].search(
                        [
                            ("code", "=", "internal"),
                        ],
                        limit=1,
                    )

                pickings[key] = env["stock.picking"].create(
                    {
                        "picking_type_id": picking_type.id,
                        "location_id": origin_loc.id,
                        "location_dest_id": dest_loc.id,
                        "origin": "Parqcast",
                        "scheduled_date": df["start_date"][i],
                    }
                )

            sp = pickings[key]
            env["stock.move"].create(
                {
                    "product_id": df["_odoo_product_id"][i],
                    "product_uom_qty": df["quantity"][i],
                    "product_uom": df["_odoo_uom_id"][i],
                    "location_id": sp.location_id.id,
                    "location_dest_id": sp.location_dest_id.id,
                    "picking_id": sp.id,
                    "name": f"Parqcast DO {i}",
                    "date": df["start_date"][i],
                    "origin": "Parqcast",
                }
            )
            created += 1

        return IngestResult(created=created)

    def cleanup_previous(self, env, company_id: int) -> int:
        recs = env["stock.picking"].search(
            [
                ("origin", "=like", "Parqcast%"),
                ("state", "=", "draft"),
            ]
        )
        count = len(recs)
        recs.unlink()
        return count
