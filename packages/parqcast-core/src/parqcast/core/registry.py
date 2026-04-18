"""Per-version bundle registry.

Each supported Odoo major registers a :class:`VersionBundle` here. Populated
by subpackage imports (e.g. ``parqcast.collectors.v19`` will register on
import once it exists). The :func:`parqcast.core.version_gate.assert_supported`
function reads :data:`REGISTRY` keys to decide which Odoo versions parqcast
accepts at runtime.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from parqcast.core.version import SupportedVersionStr


@dataclass(frozen=True)
class VersionBundle[V]:
    """All version-specific components for one Odoo major.

    The ``V`` type parameter is phantom — it never appears at runtime, only
    as a generic marker that downstream code can use to constrain types
    (e.g. ``list[Collector[V19]]``). ``collectors`` and ``ingesters`` are
    currently untyped tuples; they gain tighter types in later commits once
    ``BaseCollector`` and ``BaseIngester`` are generic in ``V``.
    """

    version_str: SupportedVersionStr
    collectors: tuple[type, ...] = ()
    ingesters: tuple[type, ...] = ()


REGISTRY: dict[SupportedVersionStr, VersionBundle[Any]] = {}


def _bootstrap() -> None:
    """Install an empty bundle for Odoo 19 so the runtime gate accepts it.

    Real collector and ingester classes are appended as per-suite migrations
    land. The bootstrap entry becomes the real v19 bundle in the collector
    cutover commit.
    """
    REGISTRY.setdefault("19", VersionBundle(version_str="19"))


_bootstrap()
