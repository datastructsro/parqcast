"""The single source of truth for the Odoo-18 collector bundle.

Defines :data:`V18_SUITES` — the module-gated suites of v18 collectors —
and registers the bundle (collectors, suites, probe) into
:data:`parqcast.core.registry.REGISTRY`. Importing this module is the
idempotent way to populate the v18 entry. The bundle grows one suite at
a time as v18-specific collectors land; the core suite is the pilot.
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
from .product import ProductCollectorV18
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
