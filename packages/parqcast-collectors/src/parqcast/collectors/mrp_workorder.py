from parqcast.schemas.outbound import MRP_WORKORDER_SCHEMA

from .base import MrpCollector


class MrpWorkorderCollector(MrpCollector):
    name = "mrp_workorder"
    schema = MRP_WORKORDER_SCHEMA
    depends_on = ["mrp_production", "workcenter"]
    required_tables = {"mrp_workorder", "mrp_workcenter"}

    optional_columns = {
        "mrp_workorder.is_user_working": ("COALESCE(wo.is_user_working, false)", "false"),
        "mrp_workorder.employee_costs_hour": ("COALESCE(wo.employee_costs_hour, 0)", "0"),
    }

    def get_sql(self):
        # display_name is computed (not stored); use wo.name instead
        is_working = self.col_or_default("mrp_workorder", "is_user_working", "false")
        emp_cost = self.col_or_default("mrp_workorder", "employee_costs_hour", "0")
        return (
            f"""
            SELECT
                wo.id, wo.production_id, wo.name,
                wo.workcenter_id, wc.name,
                wo.operation_id, wo.state,
                wo.date_start, wo.date_finished,
                wo.duration_expected, wo.duration_unit,
                {is_working},
                {emp_cost}
            FROM mrp_workorder wo
            JOIN mrp_workcenter wc ON wo.workcenter_id = wc.id
        """,
            None,
        )
