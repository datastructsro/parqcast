"""Odoo 18-specific ingester implementations.

Importing this subpackage appends the v18 ingester classes into the
``REGISTRY['18'].ingesters`` tuple via :func:`append_to_bundle`.
"""

from __future__ import annotations

from parqcast.core.registry import append_to_bundle

from .distribution_actor import DistributionActorV18
from .orderpoint_actor import OrderpointActorV18
from .production_actor import ProductionActorV18
from .purchase_actor import PurchaseActorV18
from .reschedule_actor import RescheduleActorV18

append_to_bundle(
    "18",
    ingesters=(
        PurchaseActorV18,
        ProductionActorV18,
        DistributionActorV18,
        RescheduleActorV18,
        OrderpointActorV18,
    ),
)

__all__ = [
    "DistributionActorV18",
    "OrderpointActorV18",
    "ProductionActorV18",
    "PurchaseActorV18",
    "RescheduleActorV18",
]
