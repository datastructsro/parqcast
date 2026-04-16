from parqcast.schemas.outbound import QUALITY_CHECK_SCHEMA, QUALITY_POINT_SCHEMA

from .base import QualityCollector


class QualityPointCollector(QualityCollector):
    name = "quality_point"
    schema = QUALITY_POINT_SCHEMA
    primary_table = "quality_point"
    required_tables = {"quality_point"}

    # quality_control module adds measurement fields to quality_point
    optional_columns = {
        "quality_point.measure_on": ("qp.measure_on", "NULL::text"),
        "quality_point.measure_frequency_type": ("qp.measure_frequency_type", "NULL::text"),
        "quality_point.norm": ("COALESCE(qp.norm, 0)", "0"),
        "quality_point.tolerance_min": ("COALESCE(qp.tolerance_min, 0)", "0"),
        "quality_point.tolerance_max": ("COALESCE(qp.tolerance_max, 0)", "0"),
        "quality_point.norm_unit": ("qp.norm_unit", "NULL::text"),
    }

    def get_sql(self):
        measure_on = self.col_or_default("quality_point", "measure_on", "NULL::text")
        freq_type = self.col_or_default("quality_point", "measure_frequency_type", "NULL::text")
        norm = self.col_or_default("quality_point", "norm", "0")
        tol_min = self.col_or_default("quality_point", "tolerance_min", "0")
        tol_max = self.col_or_default("quality_point", "tolerance_max", "0")
        norm_unit = self.col_or_default("quality_point", "norm_unit", "NULL::text")

        return (
            f"""
            SELECT
                qp.id, qp.name, qp.title,
                COALESCE(qp.sequence, 0),
                qp.test_type_id,
                qptt.technical_name,
                qp.team_id, qp.company_id, qp.user_id,
                COALESCE(qp.active, true),
                {measure_on}, {freq_type},
                {norm}, {tol_min}, {tol_max}, {norm_unit},
                COALESCE(
                    (SELECT string_agg(product_product_id::text, ',')
                     FROM quality_point_product_product_rel
                     WHERE quality_point_id = qp.id), ''),
                COALESCE(
                    (SELECT string_agg(stock_picking_type_id::text, ',')
                     FROM quality_point_stock_picking_type_rel
                     WHERE quality_point_id = qp.id), '')
            FROM quality_point qp
            LEFT JOIN quality_point_test_type qptt ON qp.test_type_id = qptt.id
        """,
            None,
        )


class QualityCheckCollector(QualityCollector):
    name = "quality_check"
    schema = QUALITY_CHECK_SCHEMA
    depends_on = ["quality_point"]
    primary_table = "quality_check"
    required_tables = {"quality_check"}
    pk_column = "qc.id"

    # quality_control module adds measurement fields to quality_check
    optional_columns = {
        "quality_check.measure": ("COALESCE(qc.measure, 0)", "0"),
        "quality_check.measure_success": ("qc.measure_success", "NULL::text"),
        "quality_check.qty_tested": ("COALESCE(qc.qty_tested, 0)", "0"),
        "quality_check.qty_passed": ("COALESCE(qc.qty_passed, 0)", "0"),
        "quality_check.qty_failed": ("COALESCE(qc.qty_failed, 0)", "0"),
    }

    def get_sql(self):
        measure = self.col_or_default("quality_check", "measure", "0")
        measure_success = self.col_or_default("quality_check", "measure_success", "NULL::text")
        qty_tested = self.col_or_default("quality_check", "qty_tested", "0")
        qty_passed = self.col_or_default("quality_check", "qty_passed", "0")
        qty_failed = self.col_or_default("quality_check", "qty_failed", "0")

        return (
            f"""
            SELECT
                qc.id, qc.point_id, qc.quality_state,
                qc.product_id, qc.picking_id,
                qc.control_date, qc.user_id,
                qc.team_id, qc.company_id,
                {measure}, {measure_success},
                {qty_tested}, {qty_passed}, {qty_failed}
            FROM quality_check qc
        """,
            None,
        )
