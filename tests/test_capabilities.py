from parqcast.collectors import ALL_COLLECTOR_CLASSES, ALL_SUITES, collect_probe_tables
from parqcast.collectors.base import (
    CoreCollector,
    MpsCollector,
    MrpCollector,
    PosCollector,
    PurchaseCollector,
    QualityCollector,
    SaleCollector,
)
from parqcast.core.capabilities import _DEFAULT_PROBE_TABLES, OdooCapabilities


def _make_caps(**kwargs) -> OdooCapabilities:
    defaults = {
        "installed_modules": frozenset(),
        "existing_tables": frozenset(),
        "columns_by_table": {},
    }
    defaults.update(kwargs)
    return OdooCapabilities(**defaults)


def test_mode_minimal():
    caps = _make_caps()
    assert caps.mode == "minimal"


def test_mode_inventory():
    caps = _make_caps(has_stock=True, has_sale_data=True)
    assert caps.mode == "inventory"


def test_mode_manufacturing_idle():
    caps = _make_caps(has_mrp=True, has_stock=True)
    assert caps.mode == "manufacturing_idle"


def test_mode_manufacturing_active():
    caps = _make_caps(has_mrp=True, has_manufacturing_data=True)
    assert caps.mode == "manufacturing"


def test_core_collectors_always_compatible():
    caps = _make_caps()  # minimal - no modules
    for cls in ALL_COLLECTOR_CLASSES:
        if issubclass(cls, CoreCollector) and not cls.required_tables:
            assert cls.is_compatible(caps), f"{cls.__name__} should be compatible with minimal caps"


def test_mrp_collectors_need_mrp():
    caps = _make_caps(
        installed_modules=frozenset({"stock", "sale", "purchase"}),
        existing_tables=frozenset({"stock_quant", "stock_move", "sale_order"}),
    )
    for cls in ALL_COLLECTOR_CLASSES:
        if issubclass(cls, MrpCollector):
            assert not cls.is_compatible(caps), f"{cls.__name__} should NOT be compatible without mrp"


def test_sale_collectors_need_sale():
    caps = _make_caps(installed_modules=frozenset({"stock"}))
    for cls in ALL_COLLECTOR_CLASSES:
        if issubclass(cls, SaleCollector):
            assert not cls.is_compatible(caps), f"{cls.__name__} should NOT be compatible without sale"


def test_purchase_collectors_need_purchase():
    caps = _make_caps(installed_modules=frozenset({"stock"}))
    for cls in ALL_COLLECTOR_CLASSES:
        if issubclass(cls, PurchaseCollector):
            assert not cls.is_compatible(caps), f"{cls.__name__} should NOT be compatible without purchase"


def test_full_manufacturing_caps():
    caps = _make_caps(
        installed_modules=frozenset(
            {
                "stock",
                "sale",
                "purchase",
                "mrp",
                "point_of_sale",
                "purchase_requisition",
                "mrp_mps",
                "quality",
            }
        ),
        existing_tables=frozenset(
            {
                "res_country",
                "stock_quant",
                "stock_move",
                "stock_move_line",
                "stock_location",
                "stock_warehouse",
                "stock_warehouse_orderpoint",
                "stock_picking",
                "stock_picking_type",
                "stock_route",
                "stock_rule",
                "stock_lot",
                "stock_storage_category",
                "stock_putaway_rule",
                "product_removal",
                "product_category",
                "product_pricelist",
                "sale_order",
                "sale_order_line",
                "purchase_order",
                "purchase_order_line",
                "purchase_requisition",
                "product_supplierinfo",
                "mrp_production",
                "mrp_bom",
                "mrp_workcenter",
                "mrp_workorder",
                "mrp_bom_line",
                "mrp_routing_workcenter",
                "resource_calendar",
                "resource_calendar_attendance",
                "resource_calendar_leaves",
                "pos_order",
                "pos_order_line",
                "pos_session",
                "stock_package",
                "stock_package_type",
                "product_pricelist_item",
                "mrp_bom_byproduct",
                "mrp_workcenter_capacity",
                # Enterprise
                "mrp_production_schedule",
                "mrp_product_forecast",
                "quality_point",
                "quality_check",
            }
        ),
        has_mrp=True,
        has_mrp_mps=True,
        has_quality=True,
        has_manufacturing_data=True,
    )
    # All collectors should be compatible
    for cls in ALL_COLLECTOR_CLASSES:
        assert cls.is_compatible(caps), f"{cls.__name__} should be compatible with full caps"


def test_inventory_mode_caps():
    """Simulates an inventory-mode setup: stock+sale+purchase+pos+purchase_requisition, no mrp."""
    caps = _make_caps(
        installed_modules=frozenset(
            {"stock", "sale", "purchase", "product_expiry", "point_of_sale", "purchase_requisition"}
        ),
        existing_tables=frozenset(
            {
                "res_country",
                "stock_quant",
                "stock_move",
                "stock_move_line",
                "stock_location",
                "stock_warehouse",
                "stock_warehouse_orderpoint",
                "stock_picking",
                "stock_picking_type",
                "stock_route",
                "stock_rule",
                "stock_lot",
                "stock_storage_category",
                "stock_putaway_rule",
                "product_removal",
                "product_category",
                "product_pricelist",
                "sale_order",
                "sale_order_line",
                "purchase_order",
                "purchase_order_line",
                "purchase_requisition",
                "product_supplierinfo",
                "resource_calendar",
                "resource_calendar_attendance",
                "resource_calendar_leaves",
                "pos_order",
                "pos_order_line",
                "pos_session",
                "stock_package",
                "stock_package_type",
                "product_pricelist_item",
            }
        ),
        has_stock=True,
        has_sale=True,
        has_purchase=True,
        has_product_expiry=True,
        has_sale_data=True,
        has_purchase_data=True,
    )
    assert caps.mode == "inventory"

    compatible = [cls for cls in ALL_COLLECTOR_CLASSES if cls.is_compatible(caps)]
    compatible_names = {c.name for c in compatible}

    # Core collectors
    assert "product" in compatible_names
    assert "uom" in compatible_names
    assert "partner" in compatible_names
    assert "calendar" in compatible_names
    assert "company" in compatible_names
    assert "currency" in compatible_names

    # Stock collectors
    assert "stock_location" in compatible_names
    assert "stock_warehouse" in compatible_names
    assert "stock_quant" in compatible_names
    assert "stock_move" in compatible_names
    assert "stock_picking" in compatible_names
    assert "stock_picking_type" in compatible_names
    assert "stock_route" in compatible_names
    assert "stock_lot" in compatible_names
    assert "stock_storage_category" in compatible_names
    assert "stock_putaway_rule" in compatible_names
    assert "product_removal" in compatible_names
    assert "orderpoint" in compatible_names

    # Sale collectors
    assert "sale_order" in compatible_names
    assert "sale_order_line" in compatible_names

    # Purchase collectors
    assert "purchase_order_line" in compatible_names
    assert "product_supplierinfo" in compatible_names
    assert "purchase_requisition" in compatible_names

    # POS collectors
    assert "pos_order" in compatible_names
    assert "pos_session" in compatible_names
    assert "pos_order_line" in compatible_names

    # New collectors
    assert "calendar_leaves" in compatible_names
    assert "stock_package_type" in compatible_names
    assert "stock_package" in compatible_names
    assert "pricelist_item" in compatible_names

    # These should NOT be present (no MRP)
    assert "workcenter" not in compatible_names
    assert "bom" not in compatible_names
    assert "bom_lines" not in compatible_names
    assert "bom_operations" not in compatible_names
    assert "mrp_production" not in compatible_names
    assert "mrp_workorder" not in compatible_names
    assert "bom_byproduct" not in compatible_names
    assert "workcenter_capacity" not in compatible_names


def test_pos_collectors_need_pos():
    caps = _make_caps(installed_modules=frozenset({"stock", "sale", "purchase"}))
    for cls in ALL_COLLECTOR_CLASSES:
        if issubclass(cls, PosCollector):
            assert not cls.is_compatible(caps), f"{cls.__name__} should NOT be compatible without point_of_sale"


def test_purchase_requisition_needs_both_modules():
    from parqcast.collectors.purchase_requisition import PurchaseRequisitionCollector

    # Has purchase but not purchase_requisition
    caps_purchase_only = _make_caps(
        installed_modules=frozenset({"purchase"}),
        existing_tables=frozenset({"purchase_requisition"}),
    )
    assert not PurchaseRequisitionCollector.is_compatible(caps_purchase_only)

    # Has both modules + table
    caps_both = _make_caps(
        installed_modules=frozenset({"purchase", "purchase_requisition"}),
        existing_tables=frozenset({"purchase_requisition"}),
    )
    assert PurchaseRequisitionCollector.is_compatible(caps_both)


def test_active_languages():
    caps = _make_caps()
    assert caps.active_languages == ("en_US",)
    assert caps.lang(1) == "en_US"
    assert caps.lang(2) is None
    assert caps.lang(3) is None

    caps_multi = _make_caps(active_languages=("en_US", "fr_FR", "ro_RO"))
    assert caps_multi.lang(1) == "en_US"
    assert caps_multi.lang(2) == "fr_FR"
    assert caps_multi.lang(3) == "ro_RO"
    assert caps_multi.lang(4) is None


# ── Suite tests ──


def test_mps_suite_needs_mrp_mps():
    """MPS collectors should not activate without the mrp_mps module."""
    caps = _make_caps(
        installed_modules=frozenset({"stock", "mrp"}),
        existing_tables=frozenset({"mrp_production_schedule", "mrp_product_forecast"}),
    )
    for cls in ALL_COLLECTOR_CLASSES:
        if issubclass(cls, MpsCollector):
            assert not cls.is_compatible(caps), f"{cls.__name__} should NOT be compatible without mrp_mps"


def test_mps_collectors_with_mrp_mps():
    caps = _make_caps(
        installed_modules=frozenset({"mrp_mps"}),
        existing_tables=frozenset({"mrp_production_schedule", "mrp_product_forecast"}),
    )
    for cls in ALL_COLLECTOR_CLASSES:
        if issubclass(cls, MpsCollector):
            assert cls.is_compatible(caps), f"{cls.__name__} should be compatible with mrp_mps"


def test_quality_suite_needs_quality():
    """Quality collectors should not activate without the quality module."""
    caps = _make_caps(
        installed_modules=frozenset({"stock", "mrp"}),
        existing_tables=frozenset({"quality_point", "quality_check"}),
    )
    for cls in ALL_COLLECTOR_CLASSES:
        if issubclass(cls, QualityCollector):
            assert not cls.is_compatible(caps), f"{cls.__name__} should NOT be compatible without quality"


def test_quality_collectors_with_quality():
    caps = _make_caps(
        installed_modules=frozenset({"quality"}),
        existing_tables=frozenset({"quality_point", "quality_check"}),
    )
    for cls in ALL_COLLECTOR_CLASSES:
        if issubclass(cls, QualityCollector):
            assert cls.is_compatible(caps), f"{cls.__name__} should be compatible with quality"


def test_probe_tables_derived_covers_defaults():
    """The derived probe set must cover every table from the old default list."""
    derived = collect_probe_tables(ALL_SUITES)
    for table in _DEFAULT_PROBE_TABLES:
        assert table in derived, f"Default probe table '{table}' not covered by any suite"


def test_suite_covers_all_collectors():
    """Every collector in the flat list must appear in exactly one suite."""
    from_suites = [cls for suite in ALL_SUITES for cls in suite.collector_classes]
    assert from_suites == ALL_COLLECTOR_CLASSES, "ALL_COLLECTOR_CLASSES must match suite contents"


def test_suite_availability():
    """Suites activate/deactivate based on installed modules."""
    caps_minimal = _make_caps()
    caps_stock = _make_caps(installed_modules=frozenset({"stock"}))
    caps_enterprise = _make_caps(installed_modules=frozenset({"stock", "mrp", "mrp_mps", "quality"}))

    suite_by_name = {s.name: s for s in ALL_SUITES}

    # Core always available
    assert suite_by_name["core"].is_available(caps_minimal)

    # Stock suite needs stock
    assert not suite_by_name["stock"].is_available(caps_minimal)
    assert suite_by_name["stock"].is_available(caps_stock)

    # Enterprise suites need their modules
    assert not suite_by_name["mps"].is_available(caps_stock)
    assert suite_by_name["mps"].is_available(caps_enterprise)
    assert not suite_by_name["quality"].is_available(caps_stock)
    assert suite_by_name["quality"].is_available(caps_enterprise)
