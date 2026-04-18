from parqcast.core.version import V18
from parqcast.schemas.outbound import WORKCENTER_CAPACITY_SCHEMA, WORKCENTER_SCHEMA

from ..base import MrpCollector


class WorkcenterCollectorV18(MrpCollector[V18]):
    """Workcenter collector for Odoo 18.

    Core columns (id/name/resource_id, time_efficiency, resource_calendar_id,
    company_id) are stable; v19 added ``tool``, ``constrained``, ``owner``,
    and ``post_operation_time`` — all gated via ``optional_columns`` with
    fallbacks that match the outbound schema's NULL/default semantics, so
    v18 runs cleanly without those columns.
    """

    name = "workcenter"
    schema = WORKCENTER_SCHEMA
    depends_on = ["stock_location"]
    required_tables = {"mrp_workcenter"}

    optional_columns = {
        "mrp_workcenter.default_capacity": ("COALESCE(wc.default_capacity, 1)", "1"),
        "mrp_workcenter.tool": ("COALESCE(wc.tool, false)", "false"),
        "mrp_workcenter.constrained": ("COALESCE(wc.constrained, true)", "true"),
        "mrp_workcenter.owner": ("wc.owner", "NULL::int"),
        "mrp_workcenter.post_operation_time": ("COALESCE(wc.post_operation_time, 0)", "0"),
        "mrp_workcenter.employee_costs_hour": ("COALESCE(wc.employee_costs_hour, 0)", "0"),
    }

    def get_sql(self):
        cap_col = self.col_or_default("mrp_workcenter", "default_capacity", "1")
        tool_col = self.col_or_default("mrp_workcenter", "tool", "false")
        const_col = self.col_or_default("mrp_workcenter", "constrained", "true")
        owner_col = self.col_or_default("mrp_workcenter", "owner", "NULL::int")
        post_col = self.col_or_default("mrp_workcenter", "post_operation_time", "0")
        emp_cost_col = self.col_or_default("mrp_workcenter", "employee_costs_hour", "0")

        owner_join = ""
        owner_name = "NULL::text"
        if self.caps.has_column("mrp_workcenter", "owner"):
            owner_join = "LEFT JOIN mrp_workcenter owner_wc ON wc.owner = owner_wc.id"
            owner_name = "owner_wc.name"

        return (
            f"""
            SELECT
                wc.id, wc.name, wc.resource_id,
                {cap_col}, wc.time_efficiency,
                {tool_col}, {const_col},
                {owner_col}, {owner_name},
                wc.resource_calendar_id, rc.name,
                {post_col},
                {emp_cost_col},
                wc.company_id
            FROM mrp_workcenter wc
            {owner_join}
            LEFT JOIN resource_calendar rc ON wc.resource_calendar_id = rc.id
        """,
            None,
        )


class WorkcenterCapacityCollectorV18(MrpCollector[V18]):
    """``mrp_workcenter_capacity`` columns are identical in v18 and v19."""

    name = "workcenter_capacity"
    schema = WORKCENTER_CAPACITY_SCHEMA
    depends_on = ["workcenter", "product"]
    required_tables = {"mrp_workcenter_capacity"}

    def get_sql(self):
        return (
            """
            SELECT
                mwc.id, mwc.workcenter_id,
                mwc.product_id,
                COALESCE(mwc.capacity, 1),
                COALESCE(mwc.time_start, 0),
                COALESCE(mwc.time_stop, 0)
            FROM mrp_workcenter_capacity mwc
        """,
            None,
        )
