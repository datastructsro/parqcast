"""Odoo 19-specific collector implementations.

Importing this subpackage registers the v19 collector classes into
:data:`parqcast.core.registry.REGISTRY` under the ``"19"`` key. As new
collectors move from the flat layout into this subpackage, they are added
to the registration list below.
"""

from __future__ import annotations

from parqcast.core.registry import append_to_bundle

from .product import ProductCollectorV19
from .uom import UomCollectorV19

append_to_bundle(
    "19",
    collectors=(
        UomCollectorV19,
        ProductCollectorV19,
    ),
)

__all__ = [
    "ProductCollectorV19",
    "UomCollectorV19",
]
