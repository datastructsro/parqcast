import pyarrow as pa

from parqcast.core.protocols import OdooEnvironment
from parqcast.core.version import V19

from ..base import BaseIngester, IngestResult


class RescheduleActorV19(BaseIngester[V19]):
    decision_type = "RESCHEDULE"

    def apply(self, decisions: pa.Table, env: OdooEnvironment) -> IngestResult:
        df = decisions.to_pydict()
        updated = 0
        errors = 0

        for i in range(decisions.num_rows):
            ref = df["parent_reference"][i]
            mo = env["mrp.production"].search([("name", "=", ref)], limit=1)
            if not mo:
                errors += 1
                continue

            start = df["start_date"][i]
            end = df["end_date"][i]

            update = {}
            if start:
                update["date_start"] = start
            if end:
                update["date_finished"] = end

            if not any(wo.state == "progress" for wo in mo.workorder_ids):
                mo.write(update)
            elif "date_finished" in update:
                mo.write({"date_finished": update["date_finished"]})

            updated += 1

        return IngestResult(updated=updated, errors=errors)

    def cleanup_previous(self, env: OdooEnvironment, company_id: int) -> int:
        return 0
