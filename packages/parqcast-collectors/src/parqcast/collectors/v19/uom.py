from parqcast.core.version import V19
from parqcast.schemas.outbound import UOM_SCHEMA

from ..base import CoreCollector


class UomCollectorV19(CoreCollector[V19]):
    """UOM collector for Odoo 19.

    Odoo 19 removed the ``uom.category`` model and replaced it with a
    self-referential hierarchy on ``uom.uom`` via ``relative_uom_id`` +
    ``parent_path``. The SELECT below reads the new shape directly.

    ``uom.name`` is a translatable ``Char``; at the Postgres layer this
    is a JSONB column (Odoo's translation-storage format since 16/17 —
    not a v19-specific change), hence the ``->>'<lang>'`` extraction.
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
                u.relative_uom_id,
                u.parent_path,
                u.factor,
                u.relative_factor,
                u.active
            FROM uom_uom u
        """,
            None,
        )
