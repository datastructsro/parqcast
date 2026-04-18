"""Odoo 19-specific collector implementations.

Importing this subpackage populates the v19 bundle in
:data:`parqcast.core.registry.REGISTRY` via the side-effect import of
:mod:`parqcast.collectors.v19.bundle`.
"""

from __future__ import annotations

from . import bundle as bundle  # noqa: F401 — side-effect: registers v19 bundle
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

__all__ = [
    "BomByproductCollectorV19",
    "BomCollectorV19",
    "BomLinesCollectorV19",
    "BomOperationsCollectorV19",
    "MpsForecastCollectorV19",
    "MpsScheduleCollectorV19",
    "MrpProductionCollectorV19",
    "MrpWorkorderCollectorV19",
    "OrderpointCollectorV19",
    "PosOrderCollectorV19",
    "PosOrderLineCollectorV19",
    "PosSessionCollectorV19",
    "PricelistCollectorV19",
    "PricelistItemCollectorV19",
    "ProductCollectorV19",
    "ProductRemovalCollectorV19",
    "ProductSupplierinfoCollectorV19",
    "PurchaseOrderCollectorV19",
    "PurchaseOrderLineCollectorV19",
    "PurchaseRequisitionCollectorV19",
    "QualityCheckCollectorV19",
    "QualityPointCollectorV19",
    "SaleOrderCollectorV19",
    "SaleOrderLineCollectorV19",
    "StockLocationCollectorV19",
    "StockLotCollectorV19",
    "StockMoveCollectorV19",
    "StockMoveLineCollectorV19",
    "StockPackageCollectorV19",
    "StockPackageTypeCollectorV19",
    "StockPickingCollectorV19",
    "StockPickingTypeCollectorV19",
    "StockPutawayRuleCollectorV19",
    "StockQuantCollectorV19",
    "StockRouteCollectorV19",
    "StockStorageCategoryCollectorV19",
    "StockWarehouseCollectorV19",
    "UomCollectorV19",
    "WorkcenterCapacityCollectorV19",
    "WorkcenterCollectorV19",
]
