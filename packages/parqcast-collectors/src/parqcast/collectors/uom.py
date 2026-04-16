from parqcast.schemas.outbound import UOM_SCHEMA

from .base import CoreCollector


class UomCollector(CoreCollector):
    """Odoo 19: uom_category removed. Hierarchy via relative_uom_id + parent_path."""

    name = "uom"
    schema = UOM_SCHEMA

    def get_sql(self):
        lang1 = self.caps.lang(1) or "en_US"
        return (
            f"""
            SELECT
                u.id,
                u.name->>'{lang1}',
                u.relative_uom_id,
                u.parent_path,
                u.factor,
                u.relative_factor,
                u.active
            FROM uom_uom u
        """,
            None,
        )
