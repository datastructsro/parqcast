"""Per-version bundle registry.

Each supported Odoo major registers a :class:`VersionBundle` here. Populated
by subpackage imports (e.g. ``parqcast.collectors.v19.bundle`` registers on
import). The :func:`parqcast.core.version_gate.assert_supported` function
reads :data:`REGISTRY` keys to decide which Odoo versions parqcast accepts
at runtime.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass, replace
from typing import Any

from parqcast.core.suite import CollectorSuite
from parqcast.core.version import SupportedVersionStr


@dataclass(frozen=True)
class VersionBundle[V]:
    """All version-specific components for one Odoo major.

    The ``V`` type parameter is phantom — it never appears at runtime, only
    as a generic marker that downstream code can use to constrain types.

    Fields:

    - ``version_str``: the literal "19" / "20" / … matching this bundle.
    - ``collectors``: flat tuple of every collector class the bundle ships.
    - ``ingesters``: flat tuple of every ingester class.
    - ``suites``: module-gated groupings used by the orchestrator for
      early-exit when a prerequisite module is missing.
    - ``probe_capabilities``: the version-aware capabilities probe function.
      ``None`` while the bundle is still being assembled; must be set by the
      time the orchestrator reaches the bundle via :data:`REGISTRY`.
    """

    version_str: SupportedVersionStr
    collectors: tuple[type, ...] = ()
    ingesters: tuple[type, ...] = ()
    suites: tuple[CollectorSuite, ...] = ()
    probe_capabilities: Callable[..., Any] | None = None


REGISTRY: dict[SupportedVersionStr, VersionBundle[Any]] = {}


def _bootstrap() -> None:
    """Install an empty bundle for Odoo 19 so the runtime gate accepts it.

    Real collector and ingester classes are appended as per-suite migrations
    land. The bootstrap entry is replaced with the fully-assembled bundle
    once ``parqcast.collectors.v19.bundle`` is imported.
    """
    REGISTRY.setdefault("19", VersionBundle(version_str="19"))


_bootstrap()


def append_to_bundle(
    version: SupportedVersionStr,
    *,
    collectors: Iterable[type] = (),
    ingesters: Iterable[type] = (),
    suites: Iterable[CollectorSuite] = (),
    probe_capabilities: Callable[..., Any] | None = None,
) -> None:
    """Extend the version bundle at ``REGISTRY[version]``.

    Per-version subpackages call this at import time to register their
    collector and ingester classes. Each call replaces ``REGISTRY[version]``
    with a new frozen bundle — ``VersionBundle`` is immutable by design, so
    accumulation goes through :func:`dataclasses.replace`.
    """
    current = REGISTRY.get(version)
    if current is None:
        raise RuntimeError(
            f"append_to_bundle: no bundle registered for Odoo {version!r}; "
            f"bootstrap should have installed one."
        )
    REGISTRY[version] = replace(
        current,
        collectors=current.collectors + tuple(collectors),
        ingesters=current.ingesters + tuple(ingesters),
        suites=current.suites + tuple(suites),
        probe_capabilities=probe_capabilities if probe_capabilities is not None else current.probe_capabilities,
    )
