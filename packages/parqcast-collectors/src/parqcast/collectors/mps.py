from parqcast.schemas.outbound import MPS_FORECAST_SCHEMA, MPS_SCHEDULE_SCHEMA

from .base import MpsCollector


class MpsScheduleCollector(MpsCollector):
    name = "mps_schedule"
    schema = MPS_SCHEDULE_SCHEMA
    primary_table = "mrp_production_schedule"
    required_tables = {"mrp_production_schedule"}

    def get_sql(self):
        return (
            """
            SELECT
                mps.id, mps.product_id, mps.warehouse_id,
                mps.bom_id,
                COALESCE(mps.forecast_target_qty, 0),
                COALESCE(mps.min_to_replenish_qty, 0),
                mps.replenish_trigger,
                mps.route_id, mps.supplier_id,
                COALESCE(mps.is_indirect, false),
                COALESCE(mps.mps_sequence, 10),
                mps.company_id
            FROM mrp_production_schedule mps
        """,
            None,
        )


class MpsForecastCollector(MpsCollector):
    name = "mps_forecast"
    schema = MPS_FORECAST_SCHEMA
    depends_on = ["mps_schedule"]
    primary_table = "mrp_product_forecast"
    required_tables = {"mrp_product_forecast"}

    def get_sql(self):
        return (
            """
            SELECT
                mpf.id, mpf.production_schedule_id,
                mpf.date,
                COALESCE(mpf.forecast_qty, 0),
                COALESCE(mpf.replenish_qty, 0),
                COALESCE(mpf.replenish_qty_updated, false),
                COALESCE(mpf.procurement_launched, false)
            FROM mrp_product_forecast mpf
        """,
            None,
        )
