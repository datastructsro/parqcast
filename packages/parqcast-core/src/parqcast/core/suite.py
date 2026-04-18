"""Per-version collector suites.

A :class:`CollectorSuite` groups collectors that share an Odoo module guard
(``stock``, ``sale``, …). The orchestrator iterates suites, skipping those
whose module is not installed, and activates the individual collectors
inside the survivors that pass their own ``is_compatible(caps)`` check.

This module is version-neutral. Each supported Odoo major assembles its
own ``tuple[CollectorSuite, ...]`` — e.g. ``V19_SUITES`` in
``parqcast.collectors.v19.bundle`` — and registers it into
:data:`parqcast.core.registry.REGISTRY`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class CollectorSuite:
    """A typed group of related collectors sharing module prerequisites."""

    name: str
    required_modules: frozenset[str]
    collector_classes: tuple[type, ...]
    # Tables that need column introspection but are referenced in JOINs or
    # inline caps checks rather than via required_tables / optional_columns.
    probe_extra_tables: frozenset[str] = field(default_factory=frozenset)

    def is_available(self, caps: Any) -> bool:
        return all(caps.has_module(m) for m in self.required_modules)


def collect_probe_tables(suites: tuple[CollectorSuite, ...]) -> frozenset[str]:
    """Derive the full column-probe table set from collector declarations.

    Inverts the old coupling where ``capabilities.probe()`` owned a hardcoded
    table list: collectors declare what they need and the probe adapts
    automatically.
    """
    tables: set[str] = set()
    for suite in suites:
        tables.update(suite.probe_extra_tables)
        for cls in suite.collector_classes:
            primary_table = getattr(cls, "primary_table", "")
            if primary_table:
                tables.add(primary_table)
            tables.update(getattr(cls, "required_tables", set()))
            tables.update(getattr(cls, "required_columns", {}).keys())
            for key in getattr(cls, "optional_columns", {}):
                tables.add(key.split(".", 1)[0])
    return frozenset(tables)
