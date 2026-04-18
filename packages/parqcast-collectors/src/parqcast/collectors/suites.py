"""
CollectorSuite: typed grouping of related collectors.

Each suite declares the Odoo module prerequisites and the collector
classes it provides.  The factory iterates suites -- if a suite's
required modules are all installed it evaluates the individual
collectors inside it; otherwise the whole group is skipped.

The key architectural benefit: probe_tables for capability
introspection are *derived* from collector declarations rather
than hardcoded, so adding a new collector auto-extends the probe.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from parqcast.core.capabilities import OdooCapabilities

from .base import BaseCollector
from .calendar import CalendarCollector
from .calendar_leaves import CalendarLeavesCollector
from .company import CompanyCollector
from .country import CountryCollector
from .currency import CurrencyCollector
from .mps import MpsForecastCollector, MpsScheduleCollector
from .mrp_bom import BomByproductCollector, BomCollector, BomLinesCollector, BomOperationsCollector
from .mrp_production import MrpProductionCollector
from .mrp_workorder import MrpWorkorderCollector
from .orderpoint import OrderpointCollector
from .partner import PartnerCollector
from .pos_order import PosOrderCollector, PosOrderLineCollector
from .pos_session import PosSessionCollector
from .pricelist import PricelistCollector, PricelistItemCollector
from .product_category import ProductCategoryCollector
from .product_removal import ProductRemovalCollector
from .product_supplierinfo import ProductSupplierinfoCollector
from .purchase_order import PurchaseOrderCollector
from .purchase_order_line import PurchaseOrderLineCollector
from .purchase_requisition import PurchaseRequisitionCollector
from .quality import QualityCheckCollector, QualityPointCollector
from .sale_order import SaleOrderCollector
from .sale_order_line import SaleOrderLineCollector
from .stock_location import StockLocationCollector
from .stock_lot import StockLotCollector
from .stock_move import StockMoveCollector
from .stock_move_line import StockMoveLineCollector
from .stock_package import StockPackageCollector, StockPackageTypeCollector
from .stock_picking import StockPickingCollector
from .stock_picking_type import StockPickingTypeCollector
from .stock_putaway_rule import StockPutawayRuleCollector
from .stock_quant import StockQuantCollector
from .stock_route import StockRouteCollector
from .stock_storage_category import StockStorageCategoryCollector
from .stock_warehouse import StockWarehouseCollector
from .v19 import ProductCollectorV19, UomCollectorV19
from .workcenter import WorkcenterCapacityCollector, WorkcenterCollector


@dataclass(frozen=True)
class CollectorSuite:
    """A typed group of related collectors sharing module prerequisites.

    Abstract Factory pattern: each suite is a concrete factory that
    declares which collector products it provides and the module guard
    for runtime activation.
    """

    name: str
    required_modules: frozenset[str]
    collector_classes: tuple[type[BaseCollector], ...]
    # Tables that need column introspection but are referenced in JOINs
    # or inline caps checks rather than via required_tables / optional_columns.
    probe_extra_tables: frozenset[str] = field(default_factory=frozenset)

    def is_available(self, caps: OdooCapabilities) -> bool:
        return all(caps.has_module(m) for m in self.required_modules)


def collect_probe_tables(suites: tuple[CollectorSuite, ...]) -> frozenset[str]:
    """Derive the full column-probe table set from collector declarations.

    This inverts the old coupling: capabilities.probe() no longer owns
    a hardcoded table list.  Collectors declare what they need and the
    probe adapts automatically.
    """
    tables: set[str] = set()
    for suite in suites:
        tables.update(suite.probe_extra_tables)
        for cls in suite.collector_classes:
            if cls.primary_table:
                tables.add(cls.primary_table)
            tables.update(cls.required_tables)
            tables.update(cls.required_columns.keys())
            for key in cls.optional_columns:
                tables.add(key.split(".", 1)[0])
    return frozenset(tables)


ALL_SUITES: tuple[CollectorSuite, ...] = (
    CollectorSuite(
        "core",
        frozenset(),
        (
            UomCollectorV19,
            PartnerCollector,
            ProductCollectorV19,
            ProductCategoryCollector,
            CalendarCollector,
            CalendarLeavesCollector,
            CompanyCollector,
            CountryCollector,
            CurrencyCollector,
        ),
        probe_extra_tables=frozenset({"res_company", "res_currency", "res_currency_rate"}),
    ),
    CollectorSuite(
        "stock",
        frozenset({"stock"}),
        (
            StockLocationCollector,
            StockWarehouseCollector,
            StockStorageCategoryCollector,
            StockPackageTypeCollector,
            StockPackageCollector,
            StockPickingTypeCollector,
            StockQuantCollector,
            StockMoveCollector,
            StockMoveLineCollector,
            StockPickingCollector,
            StockRouteCollector,
            StockLotCollector,
            StockPutawayRuleCollector,
            ProductRemovalCollector,
            OrderpointCollector,
        ),
        probe_extra_tables=frozenset(
            {
                "stock_package",
                "stock_quant_package",
                "stock_route_warehouse",
                "stock_storage_category_capacity",
                "stock_replenishment_info",
                "stock_replenishment_option",
            }
        ),
    ),
    CollectorSuite(
        "sale",
        frozenset({"sale"}),
        (
            SaleOrderCollector,
            SaleOrderLineCollector,
            PricelistCollector,
            PricelistItemCollector,
        ),
    ),
    CollectorSuite(
        "purchase",
        frozenset({"purchase"}),
        (
            PurchaseOrderCollector,
            PurchaseOrderLineCollector,
            ProductSupplierinfoCollector,
            PurchaseRequisitionCollector,
        ),
    ),
    CollectorSuite(
        "pos",
        frozenset({"point_of_sale"}),
        (
            PosSessionCollector,
            PosOrderCollector,
            PosOrderLineCollector,
        ),
    ),
    CollectorSuite(
        "mrp",
        frozenset({"mrp"}),
        (
            WorkcenterCollector,
            WorkcenterCapacityCollector,
            BomCollector,
            BomLinesCollector,
            BomOperationsCollector,
            BomByproductCollector,
            MrpProductionCollector,
            MrpWorkorderCollector,
        ),
    ),
    # -- Enterprise --
    CollectorSuite(
        "mps",
        frozenset({"mrp_mps"}),
        (
            MpsScheduleCollector,
            MpsForecastCollector,
        ),
    ),
    CollectorSuite(
        "quality",
        frozenset({"quality"}),
        (
            QualityPointCollector,
            QualityCheckCollector,
        ),
    ),
)

# Backward-compatible flat list derived from suites.
ALL_COLLECTOR_CLASSES: list[type[BaseCollector]] = [cls for suite in ALL_SUITES for cls in suite.collector_classes]
