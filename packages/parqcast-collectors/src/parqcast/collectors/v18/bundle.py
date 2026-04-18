"""The single source of truth for the Odoo-18 collector bundle.

Defines :data:`V18_SUITES` — the module-gated suites of v18 collectors —
and registers the bundle (collectors, suites, probe) into
:data:`parqcast.core.registry.REGISTRY`. Importing this module is the
idempotent way to populate the v18 entry. Suites grow in lockstep with
their v19 counterparts; ordering mirrors v19 for diff-readability.
"""

from __future__ import annotations

from parqcast.core.capabilities import probe_v18
from parqcast.core.registry import append_to_bundle
from parqcast.core.suite import CollectorSuite

from ..calendar import CalendarCollector
from ..calendar_leaves import CalendarLeavesCollector
from ..company import CompanyCollector
from ..country import CountryCollector
from ..currency import CurrencyCollector
from ..partner import PartnerCollector
from ..product_category import ProductCategoryCollector
from .orderpoint import OrderpointCollectorV18
from .pricelist import PricelistCollectorV18, PricelistItemCollectorV18
from .product import ProductCollectorV18
from .product_removal import ProductRemovalCollectorV18
from .sale_order import SaleOrderCollectorV18
from .sale_order_line import SaleOrderLineCollectorV18
from .stock_location import StockLocationCollectorV18
from .stock_lot import StockLotCollectorV18
from .stock_move import StockMoveCollectorV18
from .stock_move_line import StockMoveLineCollectorV18
from .stock_package import StockPackageCollectorV18, StockPackageTypeCollectorV18
from .stock_picking import StockPickingCollectorV18
from .stock_picking_type import StockPickingTypeCollectorV18
from .stock_putaway_rule import StockPutawayRuleCollectorV18
from .stock_quant import StockQuantCollectorV18
from .stock_route import StockRouteCollectorV18
from .stock_storage_category import StockStorageCategoryCollectorV18
from .stock_warehouse import StockWarehouseCollectorV18
from .uom import UomCollectorV18

V18_SUITES: tuple[CollectorSuite, ...] = (
    CollectorSuite(
        "core",
        frozenset(),
        (
            UomCollectorV18,
            PartnerCollector,
            ProductCollectorV18,
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
            StockLocationCollectorV18,
            StockWarehouseCollectorV18,
            StockStorageCategoryCollectorV18,
            StockPackageTypeCollectorV18,
            StockPackageCollectorV18,
            StockPickingTypeCollectorV18,
            StockQuantCollectorV18,
            StockMoveCollectorV18,
            StockMoveLineCollectorV18,
            StockPickingCollectorV18,
            StockRouteCollectorV18,
            StockLotCollectorV18,
            StockPutawayRuleCollectorV18,
            ProductRemovalCollectorV18,
            OrderpointCollectorV18,
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
            SaleOrderCollectorV18,
            SaleOrderLineCollectorV18,
            PricelistCollectorV18,
            PricelistItemCollectorV18,
        ),
    ),
)


V18_COLLECTORS: tuple[type, ...] = tuple(
    cls for suite in V18_SUITES for cls in suite.collector_classes
)


append_to_bundle(
    "18",
    collectors=V18_COLLECTORS,
    suites=V18_SUITES,
    probe_capabilities=probe_v18,
)
