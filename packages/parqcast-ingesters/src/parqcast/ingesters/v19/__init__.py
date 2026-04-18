"""Odoo 19-specific ingester implementations.

Importing this subpackage appends the v19 ingester classes into the
``REGISTRY['19'].ingesters`` tuple via :func:`append_to_bundle`.
"""

from __future__ import annotations

from parqcast.core.registry import append_to_bundle

from .distribution_actor import DistributionActorV19
from .orderpoint_actor import OrderpointActorV19
from .production_actor import ProductionActorV19
from .purchase_actor import PurchaseActorV19
from .reschedule_actor import RescheduleActorV19

append_to_bundle(
    "19",
    ingesters=(
        PurchaseActorV19,
        ProductionActorV19,
        DistributionActorV19,
        RescheduleActorV19,
        OrderpointActorV19,
    ),
)

__all__ = [
    "DistributionActorV19",
    "OrderpointActorV19",
    "ProductionActorV19",
    "PurchaseActorV19",
    "RescheduleActorV19",
]
