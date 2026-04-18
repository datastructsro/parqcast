from parqcast.core.version import V18
from parqcast.schemas.outbound import QUALITY_CHECK_SCHEMA, QUALITY_POINT_SCHEMA

from ..base import QualityCollector


class QualityPointCollectorV18(QualityCollector[V18]):
    """Enterprise ``quality_point`` collector for Odoo 18.

    The base ``quality_point`` columns (id/name/title/sequence/test_type_id,
    team_id/company_id/user_id, active) are present in v18 via the ``quality``
    module. Measurement fields (``measure_on``, ``norm``, ``tolerance_*``,
    ``norm_unit``) are added by the ``quality_control`` module and remain
    gated optional here — the fallback NULLs keep the outbound schema
    consistent regardless of install.
    """

    name = "quality_point"
    schema = QUALITY_POINT_SCHEMA
    primary_table = "quality_point"
    required_tables = {"quality_point"}

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

        # Per-product m2m (``quality_point_product_product_rel``) exists only
        # when the ``quality_control`` module is installed in v18 (v19 made it
        # part of the ``quality`` base); fall back to empty string on v18
        # community.
        if self.caps.has_table("quality_point_product_product_rel"):
            product_ids_expr = (
                "COALESCE("
                "(SELECT string_agg(product_product_id::text, ',') "
                "FROM quality_point_product_product_rel "
                "WHERE quality_point_id = qp.id), '')"
            )
        else:
            product_ids_expr = "''"

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
                {product_ids_expr},
                COALESCE(
                    (SELECT string_agg(stock_picking_type_id::text, ',')
                     FROM quality_point_stock_picking_type_rel
                     WHERE quality_point_id = qp.id), '')
            FROM quality_point qp
            LEFT JOIN quality_point_test_type qptt ON qp.test_type_id = qptt.id
        """,
            None,
        )


class QualityCheckCollectorV18(QualityCollector[V18]):
    """``quality_check`` column surface (point_id, quality_state, product_id,
    picking_id, control_date, user_id/team_id/company_id) is stable across
    v18 and v19. Measurement fields come from ``quality_control`` and stay
    gated."""

    name = "quality_check"
    schema = QUALITY_CHECK_SCHEMA
    depends_on = ["quality_point"]
    primary_table = "quality_check"
    required_tables = {"quality_check"}
    pk_column = "qc.id"

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
