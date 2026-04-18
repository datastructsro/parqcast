"""Odoo 18-specific collector implementations.

Importing this subpackage populates the v18 bundle in
:data:`parqcast.core.registry.REGISTRY` via the side-effect import of
:mod:`parqcast.collectors.v18.bundle`.
"""

from __future__ import annotations

from . import bundle as bundle  # noqa: F401 — side-effect: registers v18 bundle
from .product import ProductCollectorV18
from .uom import UomCollectorV18

__all__ = [
    "ProductCollectorV18",
    "UomCollectorV18",
]
