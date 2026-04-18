"""
Probe an Odoo database and build a capability profile.

The capability profile drives the factory pattern: collectors are only
instantiated if the database has the modules, tables, and columns they need.

The ``OdooCapabilities[V]`` class is generic in a phantom version tag ``V``
(see :mod:`parqcast.core.version`). The tag is pure type-checker information
— at runtime, every instance is an ordinary frozen dataclass. Use
:func:`probe_v19` to obtain a ``OdooCapabilities[V19]`` in version-aware
code paths; :func:`probe` is a legacy shim retained until the registry
cutover lands.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from parqcast.core.protocols import JsonDict
from parqcast.core.version import V19


@dataclass(frozen=True)
class OdooCapabilities[V]:
    # Module presence
    installed_modules: frozenset[str] = field(default_factory=frozenset)
    existing_tables: frozenset[str] = field(default_factory=frozenset)
    columns_by_table: dict[str, frozenset[str]] = field(default_factory=dict)

    # Derived module flags
    has_stock: bool = False
    has_sale: bool = False
    has_purchase: bool = False
    has_mrp: bool = False
    has_mrp_subcontracting: bool = False
    has_product_expiry: bool = False
    has_purchase_requisition: bool = False
    has_pos: bool = False
    has_quality: bool = False
    has_mrp_mps: bool = False

    # Data state flags (actual rows exist)
    has_inventory_data: bool = False
    has_open_moves: bool = False
    has_manufacturing_data: bool = False
    has_orderpoint_data: bool = False
    has_sale_data: bool = False
    has_purchase_data: bool = False
    has_supplier_info: bool = False

    # Database identity
    odoo_version: str = ""
    database_name: str = ""
    company_count: int = 0
    warehouse_count: int = 0

    # Language configuration
    active_languages: tuple[str, ...] = ("en_US",)

    def has_table(self, table: str) -> bool:
        return table in self.existing_tables

    def has_column(self, table: str, column: str) -> bool:
        return column in self.columns_by_table.get(table, frozenset())

    def has_module(self, module: str) -> bool:
        return module in self.installed_modules

    def lang(self, n: int) -> str | None:
        """Return nth active language code (1-indexed), or None."""
        idx = n - 1
        if 0 <= idx < len(self.active_languages):
            return self.active_languages[idx]
        return None

    @property
    def mode(self) -> str:
        if self.has_mrp and self.has_manufacturing_data:
            return "manufacturing"
        if self.has_mrp:
            return "manufacturing_idle"
        if self.has_stock and (self.has_sale_data or self.has_purchase_data):
            return "inventory"
        return "minimal"

    def summary(self) -> JsonDict:
        return {
            "mode": self.mode,
            "odoo_version": self.odoo_version,
            "database": self.database_name,
            "modules": {
                "stock": self.has_stock,
                "sale": self.has_sale,
                "purchase": self.has_purchase,
                "mrp": self.has_mrp,
                "mrp_subcontracting": self.has_mrp_subcontracting,
                "mrp_mps": self.has_mrp_mps,
                "product_expiry": self.has_product_expiry,
                "pos": self.has_pos,
                "quality": self.has_quality,
            },
            "data": {
                "inventory": self.has_inventory_data,
                "open_moves": self.has_open_moves,
                "manufacturing": self.has_manufacturing_data,
                "orderpoints": self.has_orderpoint_data,
                "sales": self.has_sale_data,
                "purchases": self.has_purchase_data,
                "supplier_info": self.has_supplier_info,
            },
            "warehouses": self.warehouse_count,
            "companies": self.company_count,
            "languages": {
                "active": list(self.active_languages),
                "lang1": self.lang(1),
                "lang2": self.lang(2),
                "lang3": self.lang(3),
            },
        }


_DEFAULT_PROBE_TABLES = frozenset(
    {
        "stock_quant",
        "stock_move",
        "stock_location",
        "stock_picking",
        "stock_picking_type",
        "stock_warehouse",
        "stock_route",
        "stock_rule",
        "stock_route_warehouse",
        "stock_lot",
        "stock_storage_category",
        "stock_storage_category_capacity",
        "stock_putaway_rule",
        "stock_package",
        "stock_quant_package",
        "stock_package_type",
        "stock_warehouse_orderpoint",
        "product_product",
        "product_template",
        "product_supplierinfo",
        "product_pricelist_item",
        "product_removal",
        "sale_order",
        "sale_order_line",
        "purchase_order",
        "purchase_order_line",
        "purchase_requisition",
        "mrp_production",
        "mrp_bom",
        "mrp_bom_byproduct",
        "mrp_workcenter",
        "mrp_workcenter_capacity",
        "mrp_workorder",
        "mrp_routing_workcenter",
        "resource_calendar",
        "resource_calendar_attendance",
        "resource_calendar_leaves",
        "res_currency",
        "res_currency_rate",
        "res_company",
        "pos_order",
        "pos_order_line",
        "pos_session",
        "stock_replenishment_info",
        "stock_replenishment_option",
    }
)


def probe_v19(cr, *, probe_tables: frozenset[str] | None = None) -> OdooCapabilities[V19]:
    """Probe a database cursor and return its Odoo-19 capability profile.

    Args:
        cr: Database cursor (Odoo-style or psycopg2).
        probe_tables: Tables to inspect for columns. When None, uses the
            built-in default list. The CollectorFactory derives this from
            collector declarations so new collectors auto-extend the probe.
    """

    # 1. Installed modules
    cr.execute("SELECT name FROM ir_module_module WHERE state = 'installed'")
    installed = frozenset(r[0] for r in cr.fetchall())

    # 2. Existing tables
    cr.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE'"
    )
    tables = frozenset(r[0] for r in cr.fetchall())

    # 3. Columns for tables we care about
    effective_probe_tables = probe_tables if probe_tables is not None else _DEFAULT_PROBE_TABLES
    columns_by_table = {}
    for t in effective_probe_tables:
        if t in tables:
            cr.execute("SELECT column_name FROM information_schema.columns WHERE table_name = %s", (t,))
            columns_by_table[t] = frozenset(r[0] for r in cr.fetchall())

    # 4. Data state (existence checks, not full counts)
    def _has_rows(table: str, where: str = "") -> bool:
        if table not in tables:
            return False
        sql = f"SELECT EXISTS (SELECT 1 FROM {table}"
        if where:
            sql += f" WHERE {where}"
        sql += ")"
        cr.execute(sql)
        return cr.fetchone()[0]

    has_inventory = _has_rows("stock_quant", "quantity != 0 OR reserved_quantity != 0")
    has_open_moves = _has_rows("stock_move", "state NOT IN ('done', 'cancel')")
    has_mfg = _has_rows("mrp_production") if "mrp_production" in tables else False
    has_orderpoints = _has_rows("stock_warehouse_orderpoint")
    has_sales = _has_rows("sale_order_line")
    has_purchases = _has_rows("purchase_order_line")
    has_supinfo = _has_rows("product_supplierinfo")

    # 5. Database identity
    cr.execute("SELECT current_database()")
    db_name = cr.fetchone()[0]

    odoo_version = ""
    if "ir_module_module" in tables:
        cr.execute("SELECT latest_version FROM ir_module_module WHERE name = 'base' AND state = 'installed' LIMIT 1")
        row = cr.fetchone()
        if row and row[0]:
            odoo_version = row[0]

    cr.execute("SELECT count(*) FROM res_company")
    company_count = cr.fetchone()[0]

    wh_count = 0
    if "stock_warehouse" in tables:
        cr.execute("SELECT count(*) FROM stock_warehouse")
        wh_count = cr.fetchone()[0]

    # 6. Active languages
    cr.execute("SELECT code FROM res_lang WHERE active = true ORDER BY code")
    langs = tuple(r[0] for r in cr.fetchall())
    if not langs:
        langs = ("en_US",)

    return OdooCapabilities(
        installed_modules=installed,
        existing_tables=tables,
        columns_by_table=columns_by_table,
        has_stock="stock" in installed,
        has_sale="sale" in installed,
        has_purchase="purchase" in installed,
        has_mrp="mrp" in installed,
        has_mrp_subcontracting="mrp_subcontracting" in installed,
        has_product_expiry="product_expiry" in installed,
        has_purchase_requisition="purchase_requisition" in installed,
        has_pos="point_of_sale" in installed,
        has_quality="quality" in installed,
        has_mrp_mps="mrp_mps" in installed,
        has_inventory_data=has_inventory,
        has_open_moves=has_open_moves,
        has_manufacturing_data=has_mfg,
        has_orderpoint_data=has_orderpoints,
        has_sale_data=has_sales,
        has_purchase_data=has_purchases,
        has_supplier_info=has_supinfo,
        odoo_version=odoo_version,
        database_name=db_name,
        company_count=company_count,
        warehouse_count=wh_count,
        active_languages=langs,
    )


