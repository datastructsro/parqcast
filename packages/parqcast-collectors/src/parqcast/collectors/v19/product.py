import re

from parqcast.core.version import V19
from parqcast.schemas.outbound import PRODUCT_SCHEMA

from ..base import CoreCollector

_LANG_RE = re.compile(r"^[a-z]{2}_[A-Z]{2}$")


class ProductCollectorV19(CoreCollector[V19]):
    """Product collector for Odoo 19.

    Notes on storage shape (not all v19-specific):

    - ``pp.standard_price`` is declared ``company_dependent=True`` and stored
      as JSONB keyed by company — an Odoo-wide format since company-dependent
      fields were migrated to JSONB (pre-18, not v19-specific). We extract the
      value for the first active language and cast to float8.
    - ``pt.name``, ``sr.name``, ``pt.description_sale`` are translatable
      ``Char``/``Text`` fields and likewise stored as JSONB (also pre-18).
    - ``price_extra`` still exists on ``product.product`` in v19; we do not
      export it here because it's a computed variant-pricing field — extract
      from ``list_price`` when needed downstream.
    - Multi-language: name is exported in up to 3 active languages.
    """

    name = "product"
    schema = PRODUCT_SCHEMA
    depends_on = ["uom"]
    pk_column = "pp.id"
    primary_table = "product_product"

    optional_columns = {
        "product_template.expiration_time": (
            "COALESCE(pt.expiration_time, 0)",
            "0",
        ),
        "product_template.is_storable": (
            "COALESCE(pt.is_storable, false)",
            "false",
        ),
        "product_template.sale_delay": (
            "COALESCE(pt.sale_delay, 0)",
            "0",
        ),
        "product_template.purchase_method": (
            "pt.purchase_method",
            "NULL::text",
        ),
        "product_template.use_expiration_date": (
            "COALESCE(pt.use_expiration_date, false)",
            "false",
        ),
    }

    def _lang_col(self, expr: str, lang: str | None) -> str:
        """Build a JSONB language extraction expression, or NULL if no language."""
        if lang and _LANG_RE.match(lang):
            return f"{expr}->>'{lang}'"
        return "NULL::text"

    def get_sql(self):
        expiry_col = self.col_or_default("product_template", "expiration_time", "0")
        is_storable_col = self.col_or_default("product_template", "is_storable", "false")
        sale_delay_col = self.col_or_default("product_template", "sale_delay", "0")
        purchase_method_col = self.col_or_default("product_template", "purchase_method", "NULL::text")
        use_expiry_col = self.col_or_default("product_template", "use_expiration_date", "false")

        lang1 = self.caps.lang(1) or "en_US"
        lang2 = self.caps.lang(2)
        lang3 = self.caps.lang(3)

        name_col1 = self._lang_col("pt.name", lang1)
        name_col2 = self._lang_col("pt.name", lang2)
        name_col3 = self._lang_col("pt.name", lang3)
        price_col = self._lang_col("pp.standard_price", lang1)
        desc_sale_col = self._lang_col("pt.description_sale", lang1)

        return (
            f"""
            SELECT
                pp.id,
                pp.product_tmpl_id,
                {name_col1},
                {name_col2},
                {name_col3},
                pp.default_code,
                pp.barcode,
                COALESCE(pp.default_code, '') || ' ' || COALESCE({name_col1}, ''),
                pt.uom_id,
                {self._lang_col("u.name", lang1)},
                u.factor::float8,
                COALESCE(pt.list_price, 0),
                COALESCE(({price_col})::float8, 0),
                COALESCE(pp.weight::float8, 0),
                COALESCE(pp.volume::float8, 0),
                pt.categ_id,
                pc.complete_name,
                pt.purchase_ok,
                pt.sale_ok,
                {is_storable_col},
                pp.active,
                pt.type,
                {desc_sale_col},
                pt.invoice_policy,
                {purchase_method_col},
                {use_expiry_col},
                pt.service_tracking,
                {sale_delay_col},
                COALESCE(
                    (SELECT string_agg(sr.id::text, ',')
                     FROM stock_route_product srp
                     JOIN stock_route sr ON srp.route_id = sr.id
                     WHERE srp.product_id = pp.id), ''),
                COALESCE(
                    (SELECT string_agg({self._lang_col("sr.name", lang1)}, ',')
                     FROM stock_route_product srp
                     JOIN stock_route sr ON srp.route_id = sr.id
                     WHERE srp.product_id = pp.id), ''),
                {expiry_col},
                pt.tracking,
                pt.company_id
            FROM product_product pp
            JOIN product_template pt ON pp.product_tmpl_id = pt.id
            JOIN uom_uom u ON pt.uom_id = u.id
            LEFT JOIN product_category pc ON pt.categ_id = pc.id
        """,
            None,
        )
