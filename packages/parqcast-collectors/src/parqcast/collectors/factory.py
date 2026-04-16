"""
CollectorFactory: probes the database, builds the capability profile,
and instantiates only the collectors that are compatible.
"""

from __future__ import annotations

import logging

from parqcast.core.capabilities import OdooCapabilities, probe

from .base import BaseCollector
from .suites import ALL_SUITES, collect_probe_tables

logger = logging.getLogger(__name__)


class CollectorFactory:
    def __init__(self, env):
        self.env = env

    def probe(self) -> OdooCapabilities:
        return probe(self.env.cr, probe_tables=collect_probe_tables(ALL_SUITES))

    def create_collectors(self, caps: OdooCapabilities | None = None) -> list[BaseCollector]:
        if caps is None:
            caps = self.probe()

        compatible = []
        skipped_suites = []

        for suite in ALL_SUITES:
            if not suite.is_available(caps):
                skipped_suites.append(suite.name)
                continue
            compatible.extend(cls(self.env, caps) for cls in suite.collector_classes if cls.is_compatible(caps))

        if skipped_suites:
            logger.info("Skipped suites: %s", ", ".join(skipped_suites))
        logger.info(
            "Instantiated %d collectors for %s mode: %s",
            len(compatible),
            caps.mode,
            ", ".join(c.name for c in compatible),
        )

        return compatible

    def resolve_order(self, collectors: list[BaseCollector]) -> list[BaseCollector]:
        """Topological sort respecting depends_on."""
        by_name = {c.name: c for c in collectors}
        active_names = set(by_name.keys())
        visited: set[str] = set()
        order: list[BaseCollector] = []

        def visit(name: str):
            if name in visited:
                return
            visited.add(name)
            collector = by_name.get(name)
            if collector:
                for dep in collector.depends_on:
                    if dep in active_names:
                        visit(dep)
                order.append(collector)

        for c in collectors:
            visit(c.name)

        return order
