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
from .partner import PartnerCollector
from .product_category import ProductCategoryCollector
from .quality import QualityCheckCollector, QualityPointCollector
from .v19 import (
    BomByproductCollectorV19,
    BomCollectorV19,
    BomLinesCollectorV19,
    BomOperationsCollectorV19,
    MrpProductionCollectorV19,
    MrpWorkorderCollectorV19,
    OrderpointCollectorV19,
    PosOrderCollectorV19,
    PosOrderLineCollectorV19,
    PosSessionCollectorV19,
    PricelistCollectorV19,
    PricelistItemCollectorV19,
    ProductCollectorV19,
    ProductRemovalCollectorV19,
    ProductSupplierinfoCollectorV19,
    PurchaseOrderCollectorV19,
    PurchaseOrderLineCollectorV19,
    PurchaseRequisitionCollectorV19,
    SaleOrderCollectorV19,
    SaleOrderLineCollectorV19,
    StockLocationCollectorV19,
    StockLotCollectorV19,
    StockMoveCollectorV19,
    StockMoveLineCollectorV19,
    StockPackageCollectorV19,
    StockPackageTypeCollectorV19,
    StockPickingCollectorV19,
    StockPickingTypeCollectorV19,
    StockPutawayRuleCollectorV19,
    StockQuantCollectorV19,
    StockRouteCollectorV19,
    StockStorageCategoryCollectorV19,
    StockWarehouseCollectorV19,
    UomCollectorV19,
    WorkcenterCapacityCollectorV19,
    WorkcenterCollectorV19,
)


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
            StockLocationCollectorV19,
            StockWarehouseCollectorV19,
            StockStorageCategoryCollectorV19,
            StockPackageTypeCollectorV19,
            StockPackageCollectorV19,
            StockPickingTypeCollectorV19,
            StockQuantCollectorV19,
            StockMoveCollectorV19,
            StockMoveLineCollectorV19,
            StockPickingCollectorV19,
            StockRouteCollectorV19,
            StockLotCollectorV19,
            StockPutawayRuleCollectorV19,
            ProductRemovalCollectorV19,
            OrderpointCollectorV19,
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
            SaleOrderCollectorV19,
            SaleOrderLineCollectorV19,
            PricelistCollectorV19,
            PricelistItemCollectorV19,
        ),
    ),
    CollectorSuite(
        "purchase",
        frozenset({"purchase"}),
        (
            PurchaseOrderCollectorV19,
            PurchaseOrderLineCollectorV19,
            ProductSupplierinfoCollectorV19,
            PurchaseRequisitionCollectorV19,
        ),
    ),
    CollectorSuite(
        "pos",
        frozenset({"point_of_sale"}),
        (
            PosSessionCollectorV19,
            PosOrderCollectorV19,
            PosOrderLineCollectorV19,
        ),
    ),
    CollectorSuite(
        "mrp",
        frozenset({"mrp"}),
        (
            WorkcenterCollectorV19,
            WorkcenterCapacityCollectorV19,
            BomCollectorV19,
            BomLinesCollectorV19,
            BomOperationsCollectorV19,
            BomByproductCollectorV19,
            MrpProductionCollectorV19,
            MrpWorkorderCollectorV19,
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
