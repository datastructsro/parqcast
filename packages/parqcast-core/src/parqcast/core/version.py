"""Phantom version-tag types for compile-time Odoo-version isolation.

These sentinel classes are never instantiated at runtime. They exist purely
as generic parameters on types like ``OdooCapabilities[V]`` and
``Collector[V]`` so the type checker refuses to mix a ``V19``-parameterised
value with a ``V20`` one. See ``docs/versioning-plan.md``.
"""

from __future__ import annotations

from typing import Literal


class V18:
    """Phantom type-tag for Odoo 18."""


class V19:
    """Phantom type-tag for Odoo 19."""


SupportedVersionStr = Literal["18", "19"]


class UnsupportedOdooVersionError(RuntimeError):
    """Raised when parqcast is installed against an Odoo major it does not support."""
