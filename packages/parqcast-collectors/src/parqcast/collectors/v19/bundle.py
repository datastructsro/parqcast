"""The single source of truth for the Odoo-19 collector bundle.

Defines :data:`V19_SUITES` — the module-gated suites of v19 collectors —
and registers the full bundle (collectors, suites, probe) into
:data:`parqcast.core.registry.REGISTRY`. Importing this module is the
idempotent way to populate the v19 entry.
"""

from __future__ import annotations

from parqcast.core.capabilities import probe_v19
from parqcast.core.registry import append_to_bundle
from parqcast.core.suite import CollectorSuite

from ..calendar import CalendarCollector
from ..calendar_leaves import CalendarLeavesCollector
from ..company import CompanyCollector
from ..country import CountryCollector
from ..currency import CurrencyCollector
from ..partner import PartnerCollector
from ..product_category import ProductCategoryCollector
from .mps import MpsForecastCollectorV19, MpsScheduleCollectorV19
from .mrp_bom import (
    BomByproductCollectorV19,
    BomCollectorV19,
    BomLinesCollectorV19,
    BomOperationsCollectorV19,
)
from .mrp_production import MrpProductionCollectorV19
from .mrp_workorder import MrpWorkorderCollectorV19
from .orderpoint import OrderpointCollectorV19
from .pos_order import PosOrderCollectorV19, PosOrderLineCollectorV19
from .pos_session import PosSessionCollectorV19
from .pricelist import PricelistCollectorV19, PricelistItemCollectorV19
from .product import ProductCollectorV19
from .product_removal import ProductRemovalCollectorV19
from .product_supplierinfo import ProductSupplierinfoCollectorV19
from .purchase_order import PurchaseOrderCollectorV19
from .purchase_order_line import PurchaseOrderLineCollectorV19
from .purchase_requisition import PurchaseRequisitionCollectorV19
from .quality import QualityCheckCollectorV19, QualityPointCollectorV19
from .sale_order import SaleOrderCollectorV19
from .sale_order_line import SaleOrderLineCollectorV19
from .stock_location import StockLocationCollectorV19
from .stock_lot import StockLotCollectorV19
from .stock_move import StockMoveCollectorV19
from .stock_move_line import StockMoveLineCollectorV19
from .stock_package import StockPackageCollectorV19, StockPackageTypeCollectorV19
from .stock_picking import StockPickingCollectorV19
from .stock_picking_type import StockPickingTypeCollectorV19
from .stock_putaway_rule import StockPutawayRuleCollectorV19
from .stock_quant import StockQuantCollectorV19
from .stock_route import StockRouteCollectorV19
from .stock_storage_category import StockStorageCategoryCollectorV19
from .stock_warehouse import StockWarehouseCollectorV19
from .uom import UomCollectorV19
from .workcenter import WorkcenterCapacityCollectorV19, WorkcenterCollectorV19

V19_SUITES: tuple[CollectorSuite, ...] = (
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
            MpsScheduleCollectorV19,
            MpsForecastCollectorV19,
        ),
    ),
    CollectorSuite(
        "quality",
        frozenset({"quality"}),
        (
            QualityPointCollectorV19,
            QualityCheckCollectorV19,
        ),
    ),
)


V19_COLLECTORS: tuple[type, ...] = tuple(
    cls for suite in V19_SUITES for cls in suite.collector_classes
)


append_to_bundle(
    "19",
    collectors=V19_COLLECTORS,
    suites=V19_SUITES,
    probe_capabilities=probe_v19,
)
