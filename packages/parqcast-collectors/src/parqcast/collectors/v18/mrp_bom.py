from parqcast.core.version import V18
from parqcast.schemas.outbound import (
    BOM_BYPRODUCT_SCHEMA,
    BOM_LINES_SCHEMA,
    BOM_OPERATIONS_SCHEMA,
    BOM_SCHEMA,
)

from ..base import MrpCollector


class BomCollectorV18(MrpCollector[V18]):
    """BOM collector for Odoo 18.

    v18 lacks ``mrp_bom.product_qty_multiple`` (introduced in v19); gated
    optional with fallback ``0``. ``days_to_prepare_mo`` exists in both.
    """

    name = "bom"
    schema = BOM_SCHEMA
    depends_on = ["product"]
    required_tables = {"mrp_bom"}

    optional_columns = {
        "mrp_bom.product_qty_multiple": (
            "COALESCE(mb.product_qty_multiple, 0)",
            "0",
        ),
        "mrp_bom.days_to_prepare_mo": (
            "COALESCE(mb.days_to_prepare_mo, 0)",
            "0",
        ),
    }

    def get_sql(self):
        lang1 = self.caps.lang(1) or "en_US"
        mult_col = self.col_or_default("mrp_bom", "product_qty_multiple", "0")
        prep_col = self.col_or_default("mrp_bom", "days_to_prepare_mo", "0")

        return (
            f"""
            SELECT
                mb.id, mb.product_tmpl_id, mb.product_id,
                pt.name->>'{lang1}',
                mb.type, mb.product_qty,
                mb.product_uom_id, u.name->>'{lang1}',
                {mult_col},
                COALESCE(mb.produce_delay, 0),
                {prep_col},
                mb.sequence, mb.code, mb.company_id
            FROM mrp_bom mb
            JOIN product_template pt ON mb.product_tmpl_id = pt.id
            LEFT JOIN uom_uom u ON mb.product_uom_id = u.id
        """,
            None,
        )


class BomLinesCollectorV18(MrpCollector[V18]):
    """``mrp_bom_line`` columns (bom_id, product_id, product_qty, product_uom_id,
    operation_id) are identical in v18 and v19."""

    name = "bom_lines"
    schema = BOM_LINES_SCHEMA
    depends_on = ["bom"]
    required_tables = {"mrp_bom_line"}

    def get_sql(self):
        lang1 = self.caps.lang(1) or "en_US"
        return (
            f"""
            SELECT
                bl.id, bl.bom_id, bl.product_id,
                pt.name->>'{lang1}',
                bl.product_qty, bl.product_uom_id, u.name->>'{lang1}',
                bl.operation_id, rw.name,
                COALESCE(
                    (SELECT string_agg(bptavr.product_template_attribute_value_id::text, ',')
                     FROM mrp_bom_line_product_template_attribute_value_rel bptavr
                     WHERE bptavr.mrp_bom_line_id = bl.id), '')
            FROM mrp_bom_line bl
            JOIN product_product pp ON bl.product_id = pp.id
            JOIN product_template pt ON pp.product_tmpl_id = pt.id
            LEFT JOIN uom_uom u ON bl.product_uom_id = u.id
            LEFT JOIN mrp_routing_workcenter rw ON bl.operation_id = rw.id
        """,
            None,
        )


class BomOperationsCollectorV18(MrpCollector[V18]):
    """BOM routing operations for Odoo 18.

    Evidence doc §4 erratum: ``time_cycle`` / ``time_cycle_manual`` semantics
    are identical across v18 and v19 — only the display label changed. On
    v18 the stored column may be ``time_cycle_manual`` while v19 exposes a
    computed ``time_cycle``; ``col_or_default`` picks whichever is
    available. Some optional metadata columns
    (``workcenter_quantity``, ``skill``, ``post_operation_time``,
    ``search_mode``) are v19-only on ``mrp_routing_workcenter`` and fall
    back to NULL/default on v18.
    """

    name = "bom_operations"
    schema = BOM_OPERATIONS_SCHEMA
    depends_on = ["bom", "workcenter"]
    required_tables = {"mrp_routing_workcenter"}

    optional_columns = {
        "mrp_routing_workcenter.workcenter_quantity": (
            "COALESCE(rw.workcenter_quantity, 1)",
            "1",
        ),
        "mrp_routing_workcenter.skill": ("rw.skill", "NULL::int"),
        "mrp_routing_workcenter.post_operation_time": (
            "COALESCE(rw.post_operation_time, 0)",
            "0",
        ),
        "mrp_routing_workcenter.search_mode": ("rw.search_mode", "NULL::text"),
        "mrp_routing_workcenter.time_cycle": ("rw.time_cycle", "NULL::float"),
    }

    def get_sql(self):
        wc_qty = self.col_or_default("mrp_routing_workcenter", "workcenter_quantity", "1")
        skill_col = self.col_or_default("mrp_routing_workcenter", "skill", "NULL::int")
        post_op = self.col_or_default("mrp_routing_workcenter", "post_operation_time", "0")
        search_mode = self.col_or_default("mrp_routing_workcenter", "search_mode", "NULL::text")

        if self.caps.has_column("mrp_routing_workcenter", "time_cycle"):
            time_cycle = "rw.time_cycle"
        elif self.caps.has_column("mrp_routing_workcenter", "time_cycle_manual"):
            time_cycle = "rw.time_cycle_manual"
        else:
            time_cycle = "NULL::float"

        skill_join = ""
        skill_name = "NULL::text"
        if self.caps.has_table("mrp_skill") and self.caps.has_column("mrp_routing_workcenter", "skill"):
            skill_join = f"LEFT JOIN mrp_skill ms ON {skill_col} = ms.id"
            skill_name = "ms.name"

        return (
            f"""
            SELECT
                rw.id, rw.bom_id, rw.name, rw.sequence,
                rw.workcenter_id, wc.name,
                {time_cycle},
                {wc_qty},
                {search_mode},
                {skill_col},
                {skill_name},
                {post_op}
            FROM mrp_routing_workcenter rw
            JOIN mrp_workcenter wc ON rw.workcenter_id = wc.id
            {skill_join}
        """,
            None,
        )


class BomByproductCollectorV18(MrpCollector[V18]):
    """``mrp_bom_byproduct`` columns are identical in v18 and v19."""

    name = "bom_byproduct"
    schema = BOM_BYPRODUCT_SCHEMA
    depends_on = ["bom", "product"]
    required_tables = {"mrp_bom_byproduct"}

    def get_sql(self):
        return (
            """
            SELECT
                bp.id, bp.bom_id,
                bp.product_id,
                COALESCE(bp.product_qty, 0),
                bp.product_uom_id,
                COALESCE(bp.cost_share, 0),
                bp.company_id
            FROM mrp_bom_byproduct bp
        """,
            None,
        )
