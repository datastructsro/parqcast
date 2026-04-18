from parqcast.core.version import V18
from parqcast.schemas.outbound import UOM_SCHEMA

from ..base import CoreCollector


class UomCollectorV18(CoreCollector[V18]):
    """UOM collector for Odoo 18.

    v18 still has the ``uom.category`` model and uses ``uom_uom.category_id``
    (a Many2one) to group convertible UOMs. v19's ``relative_uom_id`` /
    ``parent_path`` / ``relative_factor`` tree-walk fields do not exist here —
    the SELECT fills those three outbound columns with NULL so the Parquet
    schema stays identical to v19's (Snowflake contract). Downstream code
    that needs the hierarchy can reconstruct it via ``category_id`` when the
    source is known to be v18.

    ``uom.name`` is a translatable Char stored as JSONB (Odoo's translation
    format since 16/17, not v18-specific).
    """

    name = "uom"
    schema = UOM_SCHEMA

    def get_sql(self):
        lang1 = self.caps.lang(1) or "en_US"
        return (
            f"""
            SELECT
                u.id,
                u.name->>'{lang1}',
                NULL::integer,
                NULL::text,
                u.factor,
                NULL::numeric,
                u.active
            FROM uom_uom u
        """,
            None,
        )
