"""Odoo 18-specific collector implementations.

Importing this subpackage populates the v18 bundle in
:data:`parqcast.core.registry.REGISTRY` via the side-effect import of
:mod:`parqcast.collectors.v18.bundle`.
"""

from __future__ import annotations

from . import bundle as bundle  # noqa: F401 — side-effect: registers v18 bundle
from .orderpoint import OrderpointCollectorV18
from .pricelist import PricelistCollectorV18, PricelistItemCollectorV18
from .product import ProductCollectorV18
from .product_removal import ProductRemovalCollectorV18
from .product_supplierinfo import ProductSupplierinfoCollectorV18
from .purchase_order import PurchaseOrderCollectorV18
from .purchase_order_line import PurchaseOrderLineCollectorV18
from .purchase_requisition import PurchaseRequisitionCollectorV18
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

__all__ = [
    "OrderpointCollectorV18",
    "PricelistCollectorV18",
    "PricelistItemCollectorV18",
    "ProductCollectorV18",
    "ProductRemovalCollectorV18",
    "ProductSupplierinfoCollectorV18",
    "PurchaseOrderCollectorV18",
    "PurchaseOrderLineCollectorV18",
    "PurchaseRequisitionCollectorV18",
    "SaleOrderCollectorV18",
    "SaleOrderLineCollectorV18",
    "StockLocationCollectorV18",
    "StockLotCollectorV18",
    "StockMoveCollectorV18",
    "StockMoveLineCollectorV18",
    "StockPackageCollectorV18",
    "StockPackageTypeCollectorV18",
    "StockPickingCollectorV18",
    "StockPickingTypeCollectorV18",
    "StockPutawayRuleCollectorV18",
    "StockQuantCollectorV18",
    "StockRouteCollectorV18",
    "StockStorageCategoryCollectorV18",
    "StockWarehouseCollectorV18",
    "UomCollectorV18",
]
